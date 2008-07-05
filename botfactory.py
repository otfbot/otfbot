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

class BotFactory(protocol.ReconnectingClientFactory):
	"""The Factory for the Bot"""
	instances = {}

	def __init__(self, bot, logger, theconfig, classes):
		self.corelogger=logger
		self.protocol=bot
		self.theconfig=theconfig
		self.classes=classes

	def _addnetwork(self,addr,nw):
		self.instances[addr] = nw

	def _removenetwork(self,addr):
		if self.instances.has_key(addr):
			del self.instances[addr]
	
	def _getnetwork(self,addr):
		return self.instances[addr]

	def _getnetworkslist(self):
		return self.instances.keys()

	def _checkforshutdown(self):
		if len(self.instances)==0:
			self.corelogger.info("Not Connected to any network. Shutting down.")
			#TODO: add sth to stop modules
			reactor.stop()
	
	def clientConnectionLost(self, connector, reason):
		clean = error.ConnectionDone()
		if reason.getErrorMessage() == str(clean):
			self._removenetwork(connector.host)
			self._checkforshutdown()
			self.corelogger.info("Cleanly disconnected from "+connector.host)
		else:
			self.corelogger.error("Disconnected from "+connector.host+": "+str(reason.getErrorMessage())+".")
			protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		#	connector.connect()
		
	def clientConnectionFailed(self, connector, reason):
		self.corelogger.error("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
		self._removenetwork(connector.host)
		protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		#self._checkforshutdown()
	
	def buildProtocol(self,addr):
		#proto=protocol.ReconnectingClientFactory.buildProtocol(self,addr)
		proto=self.protocol(self.theconfig, self.classes)
		proto.svnrevision=self.svnrevision
		proto.factory=self
		self._addnetwork(addr.host, proto)
		return proto
