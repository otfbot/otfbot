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
# (c) 2005, 2006 by Alexander Schier
#

"""
    Calculate a random number
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import random


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    @callback
    def command(self, user, channel, command, options):
        _=self.bot.get_gettext(channel)
        if command == "wuerfel" or command == "dice":
            if options == "":
                answ = _("rolls a die. The result is %i") % random.randint(1, 6)
                self.bot.sendme(channel, answ)
            else:
                num = 2
                string = _("rolls dice. The results are: ")
                try:
                    num = int(options)
                except ValueError:
                    num = 2
                if num > 10:
                    num = 10
                for i in range(1, num + 1):
                    zahl = random.randint(1, 6)
                    if i < num:
                        string += str(zahl) + ", "
                    else:
                        string += str(zahl)
                self.bot.sendme(channel, string)
