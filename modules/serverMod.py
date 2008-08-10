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

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.mods=[]
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
		for mod in self.mods:
			#if (args.has_key("channel") and args["channel"] in self.channels and mod.name in self.getConfig("modsEnabled",[],"main",self.network,args["channel"])) or not args.has_key("channel") or args["channel"] not in self.channels:
			try:
				getattr(mod,apifunction)(**args)
			except Exception, e:
				pass #self.logerror(self.logger, mod.name, e)
	def start(self):
		if not self.bot.getBoolConfig("active", "False", "serverMod"):
			return
		self.server=server(self.bot)
		for c in self.bot.classes:
			if hasattr(c, "serverMod"):
				self.mods.append(c.serverMod(self.server))
				self.mods[-1].name=c.__name__
			self._apirunner("start")
		reactor.listenTCP(6667, ircServerFactory(self.bot))

class ircServerFactory(protocol.ServerFactory):
	def __init__(self):
		self.protocol=server

class serverMod:
	def __init__(self, server):
		pass
	def start(self):
		print "Hello World!"

class server(IRCUser):
	def __init__(self, bot):
		self.bot=bot
		self.name="nickname"
		self.user="user"
		self.firstnick=True
		self._apirunner=self.bot._apirunner
	def connectionMade(self):
		pass
	def irc_PART(self, prefix, params):
		self.part(self.getHostmask(), params[0])
	def irc_JOIN(self, prefix, params):
		self.join(self.getHostmask(), params[0])
		self.irc_NAMES("", params)
	def irc_PRIVMSG(self, prefix, params):
		print params
	def irc_NAMES(self, prefix, params):
		self.names(self.name, params[0], [self.name, "er", "sie"])
	def irc_USER(self, prefix, params):
		self.user=params[0]
		self.hostname=params[2]
		self.realname=params[3]
		self.userlist=[
				(self.user, self.getHostmask(), "server", self.name, "G", 1, "realname")
				]
	def irc_MODE(self, prefix, params):
		pass
	def irc_NICK(self, prefix, params):
		self.name=params[0]
		if self.firstnick:
			self.userlist=[
				(self.user, self.getHostmask(), "server", self.name, "G", 1, "realname")
			]
			self.irc_JOIN("", ["#control"])
			self.firstnick=False
		self.name=params[0]
		self.sendMessage("NICK", prefix=self.getHostmask())
	def irc_WHO(self, prefix, params):
		self.who(self.name, params[0], self.userlist)
	def getHostmask(self):
		return "%s!%s@%s"%(self.name, self.user, self.hostname)

class ircServerFactory(protocol.ServerFactory):
	def __init__(self, bot):
		self.protocol=server
		self.bot=bot
	def buildProtocol(self, addr):
		proto=self.protocol(self.bot)
		return proto
