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
	def startService(self):
		self.config=self.parent.getServiceNamed("config")
		port=int(self.config.getConfig("port", "6667", "server"))
		interface=interface=self.config.getConfig("interface", "127.0.0.1", "server")
		factory=ircServerFactory(self.config)
		serv=internet.TCPServer(port=port, factory=factory, interface=interface)
		self.addService(serv)
		service.MultiService.startService(self)  


class Server(IRCUser, pluginSupport):
	pluginSupportName="ircServer"
	pluginSupportPath="plugins/ircServer"
	def __init__(self, config):
		self.name="nickname"
		self.user="user"
		self.firstnick=True
		self.plugins={}
		self.logger=logging.getLogger("server")
		self.classes=[]
		self.config=config
		#files=glob.glob("plugins/ircServer/*.py")
		#sys.path.insert(1, "plugins/ircServer")
		#for file in files:
		#	name=file.split("plugins/ircServer/")[1].split(".py")[0]
		#	self.importPlugin(name)
		print "blub"
		self.startPlugins()


	def logerror(self, logger, module, exception):
		""" format a exception nicely and pass it to the logger
			@param logger: the logger instance to use
			@param module: the module in which the exception occured
			@type module: string
			@param exception: the exception
			@type exception: exception
		"""
		#for c in self.bot.classes:
		#	if c.__name__ in self.bot.getConfig("modsEnabled", [], "main", self.bot.network):
		#		try:
		#			if hasattr(c, "serverMod"):
		#				self.mods[c.__name__]=c.serverMod(self)
		#				self.mods[c.__name__].name=c.__name__
		#		except Exception, e:
		#			self.logerror(self.logger, c.__name__, e)
		#self._apirunner("start")
		logger.error("Exception in Module "+module+": "+str(exception))
		tb_list = traceback.format_tb(sys.exc_info()[2])
		for entry in tb_list:
			for line in entry.strip().split("\n"):
				logger.error(line)
	def _apirunner(self,apifunction,args={}):
		"""
			Pass all calls to modules callbacks through this method, they 
			are checked whether they should be executed or not.
			
			Example C{self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})}
			
			@type	apifunction: string
			@param	apifunction: the name of the callback function
			@type	args:	dict
			@param	args:	the arguments for the callback
		"""
		for mod in self.plugins.values():
			#if (args.has_key("channel") and args["channel"] in self.channels and mod.name in self.getConfig("modsEnabled",[],"main",self.network,args["channel"])) or not args.has_key("channel") or args["channel"] not in self.channels:
			try:
				if hasattr(mod, apifunction):
					getattr(mod, apifunction)(**args)
			except Exception, e:
				self.logerror(self.logger, mod.name, e)
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
	def __init__(self, config):
		self.protocol=Server
		self.config=config
	def buildProtocol(self, addr):
		proto=self.protocol(self.config)
		proto.connected=True
		proto.factory=self
		return proto
	def stopFactory(self):
		pass
