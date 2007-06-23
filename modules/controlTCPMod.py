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
# (c) 2007 Robert Weidlich
#

# TODO: * some authorization
#       * configuring point of listening (TCP, SSL, Socket)
#       * clientapp

from twisted.internet import protocol, error
from twisted.protocols import basic
import chatMod
from control import configShell, controlInterface

class BotProtocol(basic.LineOnlyReceiver):
    def lineReceived(self, data):
        result = self.control.input(data)
        if result:
            self.sendLine(result)
        else:
            self.sendLine("00")
    def connectionMade(self):
        if self.transport.client[0] == "127.0.0.1":
            self.control=controlInterface(self.factory.bot)
        else:
            self.sendLine("Connection not allowed")
            self.transport.loseConnection()

class BotProtocolFactory(protocol.ServerFactory):
    def __init__(self, bot):
        self.bot=bot #.getFactory()._getnetwork(factory._getnetworkslist()[0])
        self.protocol=BotProtocol

class chatMod(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
    def start(self):
        f=BotProtocolFactory(self.bot)
        try:
            self.bot.getReactor().listenTCP(5022, f)
        except (error.CannotListenError):
            pass
