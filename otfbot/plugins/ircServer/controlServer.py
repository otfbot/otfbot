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
# (c) 2008 by Alexander Schier
#

from twisted.internet import reactor

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import time


class Plugin(chatMod.chatMod):
    def __init__(self, server):
        self.server=server
        self.first=True
        #self.control=controlInterface.controlInterface(self.server.root.getServiceNamed("control"))

    @callback
    def irc_NICK(self, prefix, params):
        if self.first:
            if not self.server.loggedon: #some error occured, i.e. nickname in use
                return
            self.server.join(self.server.getHostmask(), "#control")
            self.server.privmsg(self.server.getHostmask(), "#control", "Welcome to the OTFBot control channel. Type \"help\" for help ;).")
            self.server.names(self.server.name, "#control", ['OtfBot', self.server.name])

    @callback
    def irc_PRIVMSG(self, prefix, params):
        channel=params[0]
        if channel=="#control":
            msg=params[1]
            for server in self.server.factory.instances:
                self.logger.debug(self.server.getHostmask())
                server.privmsg(self.server.getHostmask(), "#control", msg)
            response=self.server.root.getServiceNamed("control").handle_command(msg)
            if not response:
                return
            elif not type(response)==list:
                response=[response]
            for resp in response:
                for line in resp.split("\n"):
                    self.server.privmsg(self.server.getHostmask(), "#control", line)
