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
# (c) 2007 by Robert Weidlich
#

from otfbot.lib import chatMod

import random, re, string

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.control={}
    
    def query(self, user, channel, msg):
        nick=user.split("!")[0]
        if self.control.has_key(user) and msg == "endcontrol":
            del self.control[user]
        if msg == "control" and self.bot.auth(user) > 0:
            self.control[user]=self.bot.root.getServiceNamed("control")
            self.bot.sendmsg(nick,"Entered configuration modus. type 'endcontrol' to exit")
        elif self.control.has_key(user):
            output=self.control[user].handle_command(msg)
            if output == None:
                output = "None"
            self.bot.sendmsg(nick, output)
    
    def command(self, user, channel, command, options):
        if self.bot.auth(user) > 0:
            cmd=[]
            cmd.append(command)
            if options and options != "":
                cmd.append(options)
            r=self.bot.root.getServiceNamed("control").handle_command(" ".join(cmd))
            if r is None:
                cmd.insert(0,self.bot.parent.parent.name)
                cmd.insert(0,self.network)
                r=self.bot.root.getServiceNamed("control").handle_command(" ".join(cmd))
            if r is not None:
                self.bot.sendmsg(channel, r)
        elif command == "reload" and len(options) > 0:
            try:
                self.bot.plugins['ircClient.'+options].reload()
                self.bot.sendmsg(channel, "Reloaded "+options)
            except KeyError:
                self.bot.sendmsg(channel, "Could not reload "+options.strip()+": No such Plugin")
    
    def invitedTo(self, channel, inviter):
        self.logger.info("I was invited to "+channel+" by "+inviter)
        if self.bot.auth(inviter) > 0:
            self.logger.info("Accepting invitation.")
            self.bot.join(channel)
