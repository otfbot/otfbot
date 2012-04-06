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
# (c) 2012 by Alexander Schier
#

"""
    mark a checkbox from a list of checkboxes
"""
from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import random, re


class Plugin(chatMod.chatMod):
    """ checkbox plugin """

    def __init__(self, bot):
        self.bot = bot

    @callback
    def msg(self, user, channel, msg):
        if self.bot.nickname.lower() != user.getNick().lower() and "[ ]" in msg:
            parts = re.split("\[ \]", msg)
            check = random.randint(1, len(parts) -1)
            count=1
            msg=parts[0]
            for part in parts[1:]:
                if check == count:
                    msg += "[x]"
                else:
                    msg += "[ ]"
                msg += parts[count]
                count += 1
            self.bot.sendmsg(channel, msg)
