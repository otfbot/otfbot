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
# (c) 2009 by Alexander Schier
#

"""
    Calculate the current phase of the moon
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import time


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    @callback
    def command(self, user, channel, command, options):
        _=self.bot.get_gettext(channel)
        #http://avila.star-shine.ch/astro/berechnungen.html
        known_fullmoon_date = 915245340 #seconds since 1970
        monthlength = 29.530588
        ts = time.time()
        if command in ["moon", "fullmoon", "mond", "vollmond"]:
            if len(options):
                options = options.split("-")
                if len(options) == 3:
                    try:
                        year = int(options[0])
                        month = int(options[1])
                        day = int(options[2])
                        ts = time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))
                    except ValueError:
                        self.bot.sendmsg(channel, _(u"Time format: XXXX-XX-XX"))
                        return
                else:
                    self.bot.sendmsg(channel,  _(u"Time format: XXXX-XX-XX"))
                    return
        phase = (ts - known_fullmoon_date) / (60 * 60 * 24) / monthlength
        phase = phase - int(phase)

        if command == "fullmoon" or command == "vollmond":
            self.bot.sendmsg(channel, _(u"Next fullmoon in %d days") % (
                                            round((1 - phase) * monthlength)))
        elif command == "moon" or command == "mond":
            symbol = ""
            name = ""

            if phase < 0.05:
                symbol = "[ (  ) ]"
                name = _("fullmoon")
            elif phase < 0.20:
                symbol = "[ C   ]" #grosser Teil
                name = _("decreasing moon")
            elif phase < 0.30:
                symbol = "[ C   ]"
                name = _("half moon")
            elif phase < 0.45:
                symbol = "[ (   ]" #kleiner Teil
                name = _("decreasing moon")
            elif phase < 0.65:
                symbol = "[     ]"
                name = _("new moon")
            elif phase < 0.80:
                symbol = "[   ) ]" #kleiner Teil
                name = _("waxing moon")
            elif phase < 0.80:
                symbol = "[   D ]"
                name = _("half moon")
            else:
                symbol = "[   D ]" #grosser Teil
                name = _("waxing moon")
            self.bot.sendmsg(channel, u"%s %s" % (symbol, name))
