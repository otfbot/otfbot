#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
# (c) 2008 by Robert Weidlich
# (c) 2008 by Alexander Schier
# 

from twisted.application import internet, service
from twisted.internet import protocol, reactor, error
from lib.bot import Bot
import logging

class ircClientService(service.MultiService):
	name="ircClient"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		service.MultiService.__init__(self)
	def startService(self):
		self.config=self.root.getNamedServices()['config']
		for network in self.config.getNetworks():
			self.connect(network)
		service.MultiService.startService(self)

	def connect(self, network):
		f = BotFactory(self.root, self, network)
		servername=self.config.get("server", "localhost", "main", network)
		port = int(self.config.get('port','6667','main', network))
		if (self.config.getBool('ssl','False','main', network)):
			s = ssl.ClientContextFactory()
			serv=internet.SSLClient(servername, port, f,s)
			serv.__repr__=lambda: "<IRC Connection with SSL to %s:%s>"%(servername, port)
		else:
			serv=internet.TCPClient(servername, port, f)
			serv.__repr__=lambda: "<IRC Connection to %s:%s>"%(servername, port)
		f.service=serv
		serv.setName(network)
		serv.parent=self
		self.addService(serv)


class BotFactory(protocol.ReconnectingClientFactory):
	"""The Factory for the Bot"""

	def __init__(self, root, parent, network):
		self.root=root
		self.parent=parent
		self.logger=logging.getLogger(network)

		self.protocol=Bot
		self.network=network
		self.config=root.getNamedServices()['config']
	def __repr__(self):
		return "<BotFactory for network %s>"%self.network

	def clientConnectionLost(self, connector, reason):
		self.protocol=None
		self.service.protocol=None
		if not reason.check(error.ConnectionDone):
			self.logger.warn("Got disconnected from "+connector.host+": "+str(reason.getErrorMessage()))
			protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		
	def clientConnectionFailed(self, connector, reason):
		self.logger.warn("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
		#protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
	
	def buildProtocol(self,addr):
		proto=self.protocol(self.root, self)
		self.protocol=proto
		return proto
