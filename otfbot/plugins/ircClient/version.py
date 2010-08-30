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
# (c) 2009-2010 by Alexander Schier
#

from otfbot.lib import chatMod
from otfbot.lib.vername import *
from otfbot.lib.pluginSupport.decorators import callback

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot

    @callback
    def command(self, user, channel, command, options):
        if command == "version":
            self.bot.sendmsg(channel, self.bot.root.version.short())
        elif command == "ver2name":
            if not len(options)==7:
                self.bot.sendmsg(channel, "need 7-digit version")
            elif not set(options).issubset(set(hex)):
                self.bot.sendmsg(channel, "git versions are 7 digits [0-9a-f]")
            else:
                self.bot.sendmsg(channel, ver2name(options))
        elif command == "name2ver":
            options=options.lower()
            if not len(options)==9:
                self.bot.sendmsg(channel, "need 9-character version name")
            elif not validVername(options):
                self.bot.sendmsg(channel, "invalid version name")
            else:
                self.bot.sendmsg(channel, name2ver(options))
            
                

