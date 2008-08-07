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
#	   * configuring point of listening (TCP, SSL, Socket)
#	   * clientapp

from twisted.internet import protocol, error
from twisted.protocols import basic
import chatMod
from control import controlInterface

class BotProtocol(basic.LineOnlyReceiver):
	PLAIN=0
	TELNET=1
	READLINE=2
	NORMAL=3
	DEBUG=4
	terminal=PLAIN
	state=NORMAL
	def _output(self, data):
		if self.terminal == self.READLINE:
			self.sendLine("02 "+self.factory.bot.network)
			self.sendLine("01 +channels,"+",".join(self.factory.bot.channels)+":+networks,"+",".join(self.factory.bot.factory._getnetworkslist())+":config:help:reload:listmodules:stop:quit:disconnect,+networks:connect:listnetworks:currentnetwork:changenetwork,+networks:listchannels:changenick:join:part,+channels:kick")
		if not data or data == "" and self.terminal == self.READLINE:
			self.sendLine("00")
		else:
			self.sendLine(data)
		
	def lineReceived(self, data):
		tmp = data.strip().split(" ",1)
		if len(tmp) == 1:
			command=tmp[0]
			argument=""
		else:
			(command, argument) = tmp
		if command == "shell":
			if argument == "telnet":
				self.terminal=self.TELNET
			elif argument == "readline":
				self.terminal=self.READLINE
		elif command == "debug":
			self.state=self.DEBUG
		elif data != "":
			self._output(self.control.input(data))
		else:
			self._output("")

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
		self.proto=[]
		
	def buildProtocol(self,addr):
		proto=protocol.ServerFactory.buildProtocol(self,addr)
		self.proto.append(proto)
		return proto

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
	def start(self):
		self.f=BotProtocolFactory(self.bot)
		try:
			self.bot.getReactor().listenTCP(5022, self.f)
		except (error.CannotListenError):
			pass
		
	def debug(self,line):
		for p in self.f.proto:
			if p.state == p.DEBUG:
				p._output(line)
	def lineReceived(self, line):
		self.debug("< "+line)
	def sendLine(self,line):
		self.debug("> "+line)