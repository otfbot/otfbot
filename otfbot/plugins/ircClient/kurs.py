# This file is part of OtfBot.
#
# OtfBot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OtfBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OtfBot; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# (c) 2006, 2007 by Robert Weidlich
#

"""
    Fetch current stock prices
"""

from otfbot.lib import chatMod
from otfbot.lib import functions
from otfbot.lib import urlutils
from otfbot.lib.pluginSupport.decorators import callback

import string
import re
import urllib
import time


class Plugin(chatMod.chatMod):
    ku = "http://de.old.finance.yahoo.com/d/quotes.csv?s=%s&f=" + \
         "nsl1d1t1cohgvc4x&e=.csv"
    wknu = "http://de.finsearch.yahoo.com/de/index.php?s=de_sort&nm=%s&tp=S"

    def __init__(self, bot):
        self.bot = bot
        self.time = time.time()
        self.commands = ["kurs", "wkn"]

    @callback
    def command(self, user, channel, command, options):
        nick = user.getNick()
        if command in self.commands and 0 < (time.time() - self.time) < 5:
            self.bot.sendmsg(channel, "Wait a minute ...")
            return
        self.time = time.time()
        if command == "kurs":
            d = urlutils.download(self.ku % urllib.quote_plus(options))
            d.addCallback(self.parseKurs, channel)
            d.addErrback(self.error, channel)
        if command == "wkn":
            d = urlutils.download(self.wknu % urllib.quote_plus(options))
            d.addCallback(self.parseWKN, channel)
            d.addErrback(self.error, channel)

    def error(self, failure, channel):
        emsg = "Error while fetching data: %s" % failure.getErrorMessage()
        self.bot.sendmsg(channel, emsg)

    def parseWKN(self, data, channel):
        res = []
        for line in data.split("\n"):
            if line[:3] == " <a":
                res.append(
                    re.sub(
                        '.*s\=([^"]*)">([^<]*)<.*', r'\1;\2', line).split(";"))
        if len(res) < 4:
            to = len(res)
        else:
            to = 4
        for i in range(to):
            self.bot.sendmsg(channel, res[i][0] + "\t" + res[i][1])

    def parseKurs(self, data, channel):
        datas = data.strip().split('\r\n')
        if len(datas) > 4:
            datas = datas[:3]
        for data in datas:
            data = data.strip().split(";")
            date = data[4].split("/")
            d = {'name': data[0],
                 'symbol': data[1],
                 'kurs': data[2],
                 'day': date[1] + "." + date[0] + "." + date[2],
                 'time': data[3],
                 'change_kurs': "", #data[5].split(" - ")[0],
                 'change_percent': data[5], #.split(" - ")[1],
                 'last_day': data[6],
                 'top_range': data[7],
                 'low_range': data[8],
                 'volumen': data[9],
                 'currency': data[10],
                 'boerse': data[11]}
            # \x03C C=Colorcode

            answer = "%s, %s %s (%s: %s) %s %s" % (d['day'], d['time'],
                                                   d['name'], d['boerse'],
                                                   d['symbol'], d['kurs'],
                                                   d['currency'])
            if d['change_kurs'] != "N/A":
                if d['change_kurs'][:1] == "+":
                    color = "\x033"
                elif d['change_kurs'][:1] == "-":
                    color = "\x034"
                else:
                    color = ""
                answer += "%s, %s%s %s\x03, %s%s\x03, Vol.:%s St." % (answer,
                                    color, d['change_kurs'], d['currency'],
                                    color, d['change_percent'], d['volumen'])
            if d['low_range'] != "N/A":
                answer += ", Intraday %s bis %s %s." % (d['low_range'],
                                                        d['top_range'],
                                                        d['currency'])
            if d['kurs'] == "N/A":
                answer = "Der geforderte Kurs wurde nicht gefunden."
            self.bot.sendmsg(channel, answer)
