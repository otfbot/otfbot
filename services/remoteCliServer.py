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

from twisted.internet import protocol, error, reactor
from twisted.protocols import basic
import chatMod
from control import controlInterface

class botService(service.MultiService):
	""" 
		This Service should open a port where either a 
		Telnet- or a SSH-Service is listing.
		
		It have to check the authorization of the User,
		who wants to use it. It should provide a verbose
		list of the available Plugins and should manage 
		the textin- and -output. It may also provide a
		Readline-Interface for easier usage.
	"""
	name="remoteCliServer"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		service.MultiService.__init__(self)

	def startService(self):
		self.config=self.parent.getServiceNamed("config")
		f = remoteCLIFactory(self.config)
		serv=internet.TCPServer(
			int(self.bot.config.get("port", 5022, "controlTCPMod")),
			f, 
			interface=self.bot.config.get("interface", "127.0.0.1", "controlTCPMod")
		)
		serv.setName("server")
		self.addService(serv)
		service.MultiService.startService(self)		

class remoteCLI(basic.LineOnlyReceiver):
	def __init__(self):
		"""read the list of plugins"""
		basic.LineOnlyReceiver.__init__(self)
	   
	def lineReceived(self, data):
		""" 
			Select the plugin
			pass the data to the selected plugin
			provide a "leave plugin"
		"""
		pass

	def connectionMade(self):
		""" check the auth of the user and present a list of plugins """
		if self.transport.client[0] == "127.0.0.1":
			self.control=controlInterface(self.factory.bot)
		else:
			self.sendLine("Connection not allowed")
			self.transport.loseConnection()

class remoteCLIFactory(protocol.ServerFactory):
	def __init__(self):
		self.protocol=remoteCLI
		self.proto=[]
		
	def buildProtocol(self,addr):
		proto=protocol.ServerFactory.buildProtocol(self,addr)
		self.proto.append(proto)
		return proto