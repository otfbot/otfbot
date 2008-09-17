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
# (c) 2008 by Alexander Schier
# (c) 2008 by Robert Weidlich
# 
from twisted.internet import protocol, reactor, error
import logging
from bot import Bot

class BotFactory(protocol.ReconnectingClientFactory):
	"""The Factory for the Bot"""

	def __init__(self, config, network):
		self.logger=logging.getLogger(network)
		self.protocol=Bot
		self.network=network
		self.config=config

	def clientConnectionLost(self, connector, reason):
		if not reason.check(error.ConnectionDone):
			self.logger.warn("Got disconnected from "+connector.host+": "+str(reason.getErrorMessage()))
			protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		
	def clientConnectionFailed(self, connector, reason):
		self.logger.warn("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
		#protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
	
	def buildProtocol(self,addr):
		#proto=protocol.ReconnectingClientFactory.buildProtocol(self,addr)
		proto=self.protocol(self.config, self.network)
		proto.factory=self
		return proto
