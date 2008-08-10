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
from twisted.words.protocols.irc import IRC
from twisted.words.service import IRCUser
import logging, traceback, sys

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
	def start(self):
		if not self.bot.getBoolConfig("active", "False", "serverMod"):
			return
		reactor.listenTCP(6667, ircServerFactory(self.bot))

class server(IRCUser):
	def __init__(self, bot):
		self.bot=bot
		self.name="nickname"
		self.user="user"
		self.firstnick=True
		self.mods={}
		self.logger=logging.getLogger("serverMod")
		for c in self.bot.classes:
			if hasattr(c, "serverMod"):
				self.mods[c.__name__]=c.serverMod(self)
				self.mods[c.__name__].name=c.__name__
			self._apirunner("start")
	def logerror(self, logger, module, exception):
		""" format a exception nicely and pass it to the logger
			@param logger: the logger instance to use
			@param module: the module in which the exception occured
			@type module: string
			@param exception: the exception
			@type exception: exception
		"""
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
		for mod in self.mods.values():
			#if (args.has_key("channel") and args["channel"] in self.channels and mod.name in self.getConfig("modsEnabled",[],"main",self.network,args["channel"])) or not args.has_key("channel") or args["channel"] not in self.channels:
			try:
				if hasattr(mod, apifunction):
					getattr(mod,apifunction)(**args)
			except Exception, e:
				self.logerror(self.logger, mod.name, e)
	def connectionMade(self):
		self._apirunner("connectionMade")
	def irc_PART(self, prefix, params):
		self._apirunner("irc_PART", {"prefix": prefix, "params": params})
	def irc_JOIN(self, prefix, params):
		self._apirunner("irc_JOIN", {"prefix": prefix, "params": params})
	def irc_PRIVMSG(self, prefix, params):
		self._apirunner("irc_PRIVMSG", {"prefix": prefix, "params": params})
	def irc_NAMES(self, prefix, params):
		self._apirunner("irc_NAMES", {"prefix": prefix, "params": params})
	def irc_USER(self, prefix, params):
		self.user=params[0]
		self.hostname=params[2]
		self.realname=params[3]
		self._apirunner("irc_USER", {"prefix": prefix, "params": params})
		#self.userlist=[
		#		(self.user, self.getHostmask(), "server", self.name, "G", 1, "realname")
		#		]
	def irc_MODE(self, prefix, params):
		self._apirunner("irc_MODE", {"prefix": prefix, "params": params})
	def irc_NICK(self, prefix, params):
		self.name=params[0]
		self.sendMessage("NICK", prefix=self.getHostmask())
		self._apirunner("irc_NICK", {"prefix": prefix, "params": params})
	def irc_WHO(self, prefix, params):
		self._apirunner("irc_WHO", {"prefix": prefix, "params": params})
	def irc_QUIT(self, prefix, params):
		self._apirunner("irc_QUIT", {"prefix": prefix, "params": params})
		self.connected=False
	def connectionLost(self, reason):
		self._apirunner("irc_QUIT", {"reason": reason})
		self.connected=False
	def irc_PASS(self, prefix, params):
		self._apirunner("irc_PASS", {"prefix": prefix, "params": params})
	def irc_PING(self, prefix, params):
		self._apirunner("irc_PING", {"prefix": prefix, "params": params})
	def irc_PART(self, prefix, params):
		self._apirunner("irc_PART", {"prefix": prefix, "params": params})
	def irc_TOPIC(self, prefix, params):
		self._apirunner("irc_TOPIC", {"prefix": prefix, "params": params})
	def irc_WHOIS(self, prefix, params):
		self._apirunner("irc_WHOIS", {"prefix": prefix, "params": params})
	def irc_OPER(self, prefix, params):
		self._apirunner("irc_OPER", {"prefix": prefix, "params": params})
	def irc_LIST(self, prefix, params):
		self._apirunner("irc_LIST", {"prefix": prefix, "params": params})
	def getHostmask(self):
		return "%s!%s@%s"%(self.name, self.user, self.hostname)
	def sendmsg(self, user, channel, msg):
		if self.connected:
			self.privmsg(user, channel, msg)

class ircServerFactory(protocol.ServerFactory):
	def __init__(self, bot):
		self.protocol=server
		self.bot=bot
	def buildProtocol(self, addr):
		proto=self.protocol(self.bot)
		proto.connected=True
		proto.factory=self
		self.bot.server=proto
		return proto
