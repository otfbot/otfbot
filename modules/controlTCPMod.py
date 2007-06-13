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

from twisted.internet import reactor, protocol
from twisted.protocols import basic
import chatMod
from control import configShell, controlInterface

class BotProtocol(basic.LineOnlyReceiver):
    def dataReceived(self, data):
        self.sendLine(self.control.input(data))
    def connectionMade(self):
        self.control=controlInterface(self.factory.bot)

class BotProtocolFactory(protocol.ServerFactory):
    def __init__(self, bot):
        self.bot=bot
        self.protocol=BotProtocol

class chatMod(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
    def start(self):
        f=BotProtocolFactory(self.bot)
        reactor.listenTCP(5022, f)

