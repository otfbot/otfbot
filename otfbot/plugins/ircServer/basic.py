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
# (c) 2005 - 2010 by Alexander Schier
# (c) 2006 - 2010 by Robert Weidlich
#

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback, callback_with_priority
from twisted.words.protocols import irc

class Plugin(chatMod.chatMod):
    def __init__(self, server):
        self.server=server

    @callback
    def irc_PING(self, prefix, params):
        self.server.sendMessage("PONG", ":"+params[0])

    @callback
    def irc_USER(self, prefix, params):
        self.server.user=params[0]
        self.server.hostname=params[2]
        self.server.realname=params[3]

    @callback_with_priority(100)
    def irc_NICK(self, prefix, params):
        for server in self.server.parent.instances:
            if server.name==params[0] and server != self.server:
                self.server.sendMessage(irc.ERR_NICKNAMEINUSE, "nickname already in use", prefix="localhost")
                return
        self.server.name=params[0]
        if not self.server.loggedon:
            self.server.sendMessage(irc.RPL_WELCOME, ":connected to OTFBot IRC", prefix="localhost")
            self.server.sendMessage(irc.RPL_YOURHOST, ":Your host is %(serviceName)s, running version %(serviceVersion)s" % {"serviceName": self.server.transport.server.getHost(),"serviceVersion": "VERSION"},prefix="localhost")
            self.server.sendMessage(irc.RPL_MOTD, ":Welcome to the Bot-Control-Server", prefix="localhost")
            self.server.loggedon=True

    @callback
    def irc_QUIT(self, prefix, params):
        self.server.connected=False
