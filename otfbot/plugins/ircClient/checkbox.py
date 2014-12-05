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
# (c) 2012, 2014 by Alexander Schier
# (c) 2014 by neTear
#
# neTear thought (2014) true checkboxes as option will increase the entropy oO
# so now it is [ ] "multi"-checkboxes and a one radiobox () to be filled.
# Any number ahead in checkbox-list will be treaten as a maximum qty of
# checkboxes to be checked randomly, but there's no "minimum" value
# at the moment, so possibly 'bitwise' it could be "0" as nothing checked

"""
    marks randomly checkboxes [ ] (or not) - and or - one radiobuttons ( )
    from a list of checkboxes &| radiobuttons
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import random


class Plugin(chatMod.chatMod):
    """ checkbox/radiobutton plugin """

    def __init__(self, bot):
        self.bot = bot

    @callback
    def msg(self, user, channel, msg):
        if self.bot.nickname.lower() != user.getNick().lower() and \
                                  ("[ ]" in msg or "( )" in msg):

            # radiobutton ( )
            if "( )" in msg:
                parts = msg.split("( )")
                which_radiobutton = random.randint(1, len(parts) - 1)
                msg = "( )".join(parts[:which_radiobutton]) + \
                      "(x)" + \
                      "( )".join(parts[which_radiobutton:])

            # checkbox [ ]
            if "[ ]" in msg:
                parts = msg.split("[ ]")
                num_checkmarks = len(parts)
                try:
                    num_checkmarks = int(msg.split(" ")[0])+1
                except:
                    pass
                checkmarks = [0]*(len(parts) - num_checkmarks) \
                    + [random.randint(0, 1) for i in range(num_checkmarks)]
                msg = parts[0]
                for i, part in enumerate(parts[1:]):
                    msg += "[x]" if checkmarks[i] else "[ ]"
                    msg += part
            self.bot.sendmsg(channel, msg)
