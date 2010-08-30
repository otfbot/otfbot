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
# (c) 2008 by Thomas Wiegart
# (c) 2009 by Alexander Schier
#

"""
    Sends quotes and proverbs to the channel
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import urllib2
import re


class Plugin(chatMod.chatMod):
    """ quotesfromweb plugin """
    quoteurl = "http://www.all4quotes.com/quote/rss/quotes/"

    def __init__(self,bot):
        self.bot = bot
        self.feedparser = self.bot.depends_on_module("feedparser")
    
    @callback
    def command(self, user, channel, command, options):
        """
            Handels the commands !zitat, !sprichwort and !proverb and posts appropriate phrases in the channel
        """
        if command.lower() == "zitat":
            zitat=self.feedparser.parse(self.quoteurl)
            zitat=zitat['entries'][0]
            desc = zitat['description'].replace('<p class="q_pate"><a href="http://www.all4quotes.com/paten-information/b3967a0e938dc2a6340e258630febd5a/" target="_blank" title="Treffsichere Textlinkwerbung">Werden Sie Zitatepate&trade;</a></p>',"").encode("utf8")
            desc = desc.replace(re.findall('<p.*class=".+">.+</p>',desc)[0],"")
            self.bot.msg(channel,"\"" + desc + "\" (" + zitat['title'].encode("utf8") + ")")
            return
        elif command == "sprichwort":
            url=urllib2.urlopen("http://www.sprichwortrekombinator.de")
        elif command == "proverb":
            url=urllib2.urlopen("http://proverb.gener.at/or/")
        else:
            return
        data=url.read()
        url.close()
        sprichwort=re.search("<div class=\"spwort\">([^<]*)<\/div>", data, re.S).group(1)
        self.bot.sendmsg(channel, sprichwort)
