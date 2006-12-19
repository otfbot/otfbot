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

import random, re
import chatMod

class chatMod(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.modes={}
        self.modes["op"]={"char": "o", "set": 1}
        self.modes["deop"]={"char": "o", "set": 0}
        self.modes["voice"]={"char": "v", "set": 1}
        self.modes["devoice"]={"char": "v", "set": 0}
	self.modes["protect"]={"char": "a", "set": 1}
	self.modes["unprotect"]={"char": "a", "set": 0}

    def msg(self, user, channel, msg):
        user=user.split("!")[0]
        if self.bot.auth(user) > 2:
            for mode in self.modes.keys():
                if msg[0:len(mode)+1]=="!"+mode:
                    msg=msg[len(mode)+1:]
                    if msg != "":
                        if msg[0]==" ":
                            msg=msg[1:]
                        self.bot.mode(channel, self.modes[mode]["set"], self.modes[mode]["char"], None, msg)
                    else:
                        self.bot.mode(channel, self.modes[mode]["set"], self.modes[mode]["char"], None, user)
