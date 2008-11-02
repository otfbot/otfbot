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
import chatMod
from twisted.internet import reactor, protocol
from twisted.internet.tcp import Server
from twisted.words.protocols.irc import IRC
from twisted.words.protocols import irc
from twisted.words.service import IRCUser
from twisted.application import service, internet
import logging, traceback, sys, time
from lib import bot
from lib.pluginSupport import pluginSupport
import glob

class ircServerService(service.MultiService):
	name="ircServer"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		service.MultiService.__init__(self)
	def startService(self):
		self.config=self.root.getNamedServices()['config']
		port=int(self.config.get("port", "6667", "server"))
		interface=interface=self.config.get("interface", "127.0.0.1", "server")
		factory=ircServerFactory(self.root, self)
		serv=internet.TCPServer(port=port, factory=factory, interface=interface)
		self.addService(serv)
		service.MultiService.startService(self)  


class Server(IRCUser, pluginSupport):
	pluginSupportName="ircServer"
	pluginSupportPath="plugins/ircServer"
	def __init__(self, root, parent):
		pluginSupport.__init__(self, root, parent)

		self.name="nickname"
		self.user="user"
		self.firstnick=True
		self.plugins={}
		self.logger=logging.getLogger("server")
		self.classes=[]
		self.config=root.getNamedServices()['config']

		self.startPlugins()


	def handleCommand(self, command, prefix, params):
		"""Determine the function to call for the given command and call
        it with the given arguments.
        """
		###twisted handling###
        #method = getattr(self, "irc_%s" % command, None)
        #try:
        #    if method is not None:
        #        method(prefix, params)
        #    else:
        #        self.irc_unknown(prefix, command, params)
        #except:
        #    log.deferr()
		###we use _apirunner instead###
		self._apirunner("irc_%s"%command, {'prefix': prefix, 'params': params})
	def connectionMade(self):
		self._apirunner("connectionMade")
	def connectionLost(self, reason):
		self.connected=False
	def getHostmask(self):
		return "%s!%s@%s"%(self.name, self.user, self.hostname)
	def sendmsg(self, user, channel, msg):
		if self.connected:
			self.privmsg(user, channel, msg)
	def stop(self):
		self._apirunner("stop")
		for mod in self.plugins.keys():
			del(self.plugins[mod])
		self.plugins={}

class ircServerFactory(protocol.ServerFactory):
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		self.config=root.getNamedServices()['config']

		self.protocol=Server
	def buildProtocol(self, addr):
		proto=self.protocol(self.root, self)
		proto.connected=True
		proto.factory=self
		self.protocol=proto
		return proto
	def stopFactory(self):
		pass
