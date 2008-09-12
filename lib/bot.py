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
from twisted.words.protocols import irc
from twisted.internet import reactor
import logging
import logging.handlers
import sys, traceback, string, time
sys.path.insert(1,"lib")
import scheduler
class Bot(irc.IRCClient):
	""" The Protocol of our IRC-Bot
		@ivar mods: contains references to all modules, which are loaded
		@type mods: list
		@ivar users: contains a dict of all users in the channels we are in
		@type users: dict
		@ivar channels: all channels we are currently in
		@type channels: list
		@ivar network: the name of the network we are connected to
		@type network: string
		@ivar logger: a instance of the standard python logger
		@ivar scheduler: a instance of the L{Scheduler}
		@ivar nickname: the nick of the bot
	"""

	def __init__(self, config, classes, network):
		#list of mods, which the bot should use
		#you may need to configure them first
		self.config=config

		self.delConfig=config.delConfig
		self.getConfig=config.getConfig
		self.hasConfig=config.hasConfig
		self.getPathConfig=config.getPathConfig
		self.setConfig=config.setConfig
		self.getBoolConfig=config.getBoolConfig

		self.classes = classes
		self.channels=[]
		self.network=network
		self.realname=self.config.getConfig("realname", "A Bot", "main", self.network)
		self.password=self.config.getConfig('password', None, 'main', network)
		self.nickname=unicode(self.config.getConfig("nickname", "OtfBot", 'main', self.network)).encode("iso-8859-1")
		tmp=self.config.getChannels(self.network)
		if tmp:
			self.channels=tmp
		
		self.mods = {}
		self.numMods = 0
		
		self.versionName="OtfBot"
		self.versionNum="svn "+"$Revision: 177 $".split(" ")[1]
		self.lineRate = 1.0/float(self.config.getConfig("linesPerSecond","2","main",self.network))

		# usertracking
		self.users={}
		self.modchars={'a':'!','o':'@','h':'%','v':'+'}
		self.modcharvals={'!':4,'@':3,'%':2,'+':1,' ':0}

		self.logger = logging.getLogger(self.network)
		self.logger.info("Starting new Botinstance")
		self.scheduler = scheduler.Scheduler()
		self.startMods()
	
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
			#self.logger.debug("running "+apifunction+" for module "+str(mod))
			#if a channel is present, check if the module is disabled for the channel.
			if args.has_key("channel") and mod.name in self.config.getConfig("modsDisabled",[],"main",self.network,args["channel"], set_default=False):
				return
			if mod.name in self.config.getConfig("modsDisabled", [], "main", self.network):
				return
			try:
				if hasattr(mod, apifunction):
					getattr(mod,apifunction)(**args)
			except Exception, e:
				self.logerror(self.logger, mod.name, e)

	def getUsers(self):
		""" Get a list of users
			@rtype: dict
			@return: a dict with the channelnames as keys
		"""
		return self.users
	def getFactory(self):
		""" get the factory
			@rtype: BotFactory
			@return: the current factory
		"""
		return self.factory
	def auth(self, user):
		"""
			call this, to see which rights C{user} has
			@type user: string
			@param user: the full hostmask of the user
			@rtype: int
			@return: the level of access rights (0 = nothing, 10 = everything)
		"""
		level=0
		for mod in self.mods.values():
			try:
				retval=mod.auth(user)
				if retval > level:
					level=retval
			except AttributeError:
				pass
		return level

	class WontStart(Exception):
		pass
	class DependencyMissing(Exception):
		pass
	def depends(self, dependency):
		"""raise an Exception, if the dependency is not active"""
		if not self.mods.has_key(dependency):
			raise self.DependencyMissing(dependency)
	
	def sendmsg(self, channel, msg, encoding="iso-8859-15", fallback="iso-8859-15"):
		"""
			call B{only} this to send messages to channels or users
			it converts the message from iso-8859-15 to a encoding given in the config
			@type	channel:	string
			@param	channel:	send the message to this channel or user
			@type	msg:		string
			@param	msg:		the message to send
			@type	encoding:	string
			@param	encoding:	the encoding of C{msg}
			@type	fallback:	string
			@param	fallback:	try this one as encoding for C{msg}, if C{encoding} doesn't work
		"""
		if not type(msg)==list:
			msg=[msg]
		for line in msg:
			try:
				line=unicode(line, encoding).encode(self.config.getConfig("encoding", "UTF-8", "main"))
			except UnicodeDecodeError:
				#self.logger.debug("Unicode Decode Error with String:"+str(msg))
				#Try with Fallback encoding
				msg=unicode(line, fallback).encode(self.config.getConfig("encoding", "UTF-8", "main"))
			except UnicodeEncodeError:
				pass
				#self.logger.debug("Unicode Encode Error with String:"+str(msg))
				#use msg as is
			
			self.msg(channel, line)
			self.privmsg(self.nickname, channel, line)
			time.sleep(0.5)
		
	def sendme(self, channel, action, encoding="iso-8859-15"):
		"""
			call B{only} this to send actions (/me) to channels
			it converts the message from iso-8859-15 to a encoding given in the config
			@type	channel:	string
			@param	channel:	send the message to this channel or user
			@type	action:		string
			@param	action:		the message to send
			@type	encoding:	string
			@param	encoding:	the encoding of C{msg}
		"""
		if not type(action)==list:
			action=[action]
		for line in action:
			line=unicode(line, encoding).encode(self.config.getConfig("encoding", "UTF-8", "main"))
			
			self.me(channel, line)
			self.action(self.nickname, channel, line)
			time.sleep(0.5)
	
	def reloadModuleClass(self, moduleClass):
			self.logger.info("reloading class "+moduleClass.__name__)
			reload(moduleClass)
	def restartModule(self, moduleName, network):
		if network in self.ipc.getall() and moduleName in self.ipc[network].mods.keys():
			self.ipc[network].stopMod(moduleName)
			c=None
			#this is not optimal, because each module needs to iterate over all classes
			for c in self.classes:
				if c.__name__==moduleName:
					break
			self.ipc[network].startMod(c)

	def reloadModules(self, all=True):
		"""
			call this to reload all modules
		"""
		for chatModule in self.classes:
			self.reloadModuleClass(chatModule)
		if all: #global
			for network in self.ipc.getall().keys():
				for mod in self.ipc[network].mods.keys():
					self.restartModule(mod, network)
		else:
			for chatMod in self.mods.values():
				self.restartModule(chatMod.name, self.network)
	
	def stopMod(self, moduleName):
		if not moduleName in self.mods.keys():
			return
		chatMod=self.mods[moduleName]
		self.logger.info("stopping %s for network %s"%(moduleName, self.network))
		try:
			chatMod.stop()
		except Exception, e:
			self.logerror(self.logger, chatMod.name, e)
		del(self.mods[moduleName])
		del(chatMod)

	def startMods(self):
		"""
			initializes all known modules
		"""
		for chatModule in self.classes:
			if chatModule.__name__ in self.config.getConfig("modsEnabled", [], "main", self.network):
				self.startMod(chatModule)
	def startMod(self, moduleClass):
			if hasattr(moduleClass, "chatMod"):
				try:
					self.logger.info("starting %s for network %s"%(moduleClass.__name__, self.network))
					mod=moduleClass.chatMod(self)
					self.mods[moduleClass.__name__]=mod
					self.mods[moduleClass.__name__].setLogger(self.logger)
					self.mods[moduleClass.__name__].name=moduleClass.__name__
					self.mods[moduleClass.__name__].config=self.config
					if hasattr(self, "network"): #needed for reload!
						self.mods[moduleClass.__name__].network=self.network
					if hasattr(self.mods[moduleClass.__name__], "start"):
						self.mods[moduleClass.__name__].start()
				except Exception, e:
					self.logerror(self.logger, moduleClass.__name__, e)

	# Callbacks
	def connectionMade(self):
		""" 
			this is called by twisted
			, when the connection to the irc-server was made
		"""
		self.logger.info("made connection to "+self.transport.addr[0])
		irc.IRCClient.connectionMade(self)
		self._apirunner("connectionMade")

	def connectionLost(self, reason):
		""" this is called by twisted,
			if the connection to the IRC-Server was lost
			@type reason:	twisted.python.failure.Failure
		"""
		#self.logger.info("lost connection: "+str(reason))
		irc.IRCClient.connectionLost(self)
		self._apirunner("connectionLost",{"reason": reason})
	
	def signedOn(self):
		""" called by twisted,
			when we signed on the IRC-Server
		"""
		self.logger.info("signed on "+self.network+" as "+self.nickname)
		channelstojoin=self.channels
		self.channels=[]
		for channel in channelstojoin:
			if(self.config.getBoolConfig("enabled", "false", "main", self.network, channel)):
				pw = self.config.getConfig("password","", "main", self.network, channel)
				if (pw != ""):
					self.join(unicode(channel).encode("iso-8859-1"),unicode(pw).encode("iso-8859-1"))
				else:
					self.join(unicode(channel).encode("iso-8859-1"))
		self._apirunner("signedOn")

	def joined(self, channel):
		""" called by twisted,
			if we joined a channel
			@param channel: the channel we joined
			@type channel: string
		"""
		self.logger.info("joined "+channel)
		self.channels.append(channel)
		self.users[channel]={}
		self._apirunner("joined",{"channel":channel})
		self.config.setConfig("enabled", True, "main", self.network, channel)

	def left(self, channel):
		""" called by twisted,
			if we left a channel
			@param channel: the channel we left
			@type channel: string
		"""
		self.logger.info("left "+channel)
		self._apirunner("left",{"channel":channel})
		self.users.remove(channel)
		self.channels.remove(channel)
		self.config.setConfig("enabled", "False", "main", self.network, channel) #disable the channel for the next start of the bot

	#def isupport(self, options):
		#self.logger.debug("isupport"+str(options))
	#def bounce(self, info):
		#self.logger.debug("bounce:"+str(info))
	#def myInfo(self, servername, version, umodes, cmodes):
		#self.logger.debug("myinfo: servername="+str(servername)+" version="+str(version)+" umodes="+str(umodes)+" cmodes="+str(cmodes))
	def command(self, user, channel, command, options):
		"""callback for !commands
		@param user: the user, which issues the command
		@type user: string
		@param channel: the channel to which the message was sent or my nickname if it was a private message
		@type channel: string
		@param command: the !command without the !
		@type command: string
		@param options: eventual options specified after !command (e.g. "!command foo")
		@type options: string"""
		self._apirunner("command",{"user":user,"channel":channel,"command":command, "options":options})

	def privmsg(self, user, channel, msg):
		""" called by twisted,
			if we received a message
			@param user: the user, which send the message
			@type user: string
			@param channel: the channel to which the message was sent or my nickname if it was a private message
			@type channel: string
			@param msg: the message
			@type msg: string
		"""
		try:
			char=msg[0].decode('UTF-8').encode('UTF-8')
		except UnicodeDecodeError:
			char=msg[0].decode('iso-8859-15').encode('UTF-8')
		if char==self.config.getConfig("commandChar", "!", "main").encode("UTF-8"):
			tmp=msg[1:].split(" ", 1)
			command=tmp[0]
			if len(tmp)==2:
				options=tmp[1]
			else:
				options=""
			self._apirunner("command",{"user":user,"channel":channel,"command":command,"options":options})
			#return

		# to be removed
		self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})

		#if channel.lower() == self.nickname.lower():
		if channel.lower()[0] in "abcdefghijklmnopqrstuvwxyz":
			self._apirunner("query",{"user":user,"channel":channel,"msg":msg})
			return
		
		# to be called for messages in channels
		self._apirunner("msg",{"user":user,"channel":channel,"msg":msg})

	def irc_unknown(self, prefix, command, params):
		""" called by twisted
			for every line that has no own callback
		"""
		self._apirunner("irc_unknown",{"prefix":prefix,"command":command,"params":params})

	def noticed(self, user, channel, msg):
		""" called by twisted,
			if we got a notice
			@param user: the user which send the notice
			@type user: string
			@param channel: the channel to which the notice was sent (could be our nick, if the message was only sent to us)
			@type channel: string
			@param msg: the message
			@type msg: string
		"""
		self._apirunner("noticed",{"user":user,"channel":channel,"msg":msg})
				
	def action(self, user, channel, message):
		""" called by twisted,
			if we received a action
			@param user: the user which send the action
			@type user: string
			@param channel: the channel to which the action was sent (could be our nick, if the message was only sent to us)
			@type channel: string
			@param msg: the message
			@type msg: string
		"""		
		self._apirunner("action",{"user":user,"channel":channel,"message":message})

	def modeChanged(self, user, channel, set, modes, args):
		""" called by twisted
			if a usermode was changed
		"""
		i=0
		for arg in args:
			if modes[i] in self.modchars.keys() and set == True:
				if self.modcharvals[self.modchars[modes[i]]] > self.modcharvals[self.users[channel][arg]['modchar']]:
					self.users[channel][arg]['modchar'] = self.modchars[modes[i]]
			elif modes[i] in self.modchars.keys() and set == False:
				#FIXME: ask for the real mode
				self.users[channel][arg]['modchar'] = ' '
			i=i+1
		self._apirunner("modeChanged",{"user":user,"channel":channel,"set":set,"modes":modes,"args":args})

	def kickedFrom(self, channel, kicker, message):
		""" called by twisted,
			if the bot was kicked
		"""
		self.logger.info("I was kicked from "+channel+" by "+kicker)
		self._apirunner("kickedFrom",{"channel":channel,"kicker":kicker,"message":message})
		self.channels.remove(channel)
		self.config.setConfig("enabled", "False", "main", self.network, channel) #disable the channel for the next start of the bot
		self.users.remove(channel)

	def userKicked(self, kickee, channel, kicker, message):
		""" called by twisted,
			if a user was kicked
		"""
		self._apirunner("userKicked",{"kickee":kickee,"channel":channel,"kicker":kicker,"message":message})
		del self.users[channel][user.split("!")[0]]		

	def userJoined(self, user, channel):
		""" called by twisted,
			if a C{user} joined the C{channel}
		"""
		self.users[channel][user.split("!")[0]]={'modchar':' '}		
		self._apirunner("userJoined",{"user":user,"channel":channel})

	def userLeft(self, user, channel):
		""" called by twisted,
			if a C{user} left the C{channel}
		"""
		self._apirunner("userLeft",{"user":user,"channel":channel})
		del self.users[channel][user.split("!")[0]]		

	def userQuit(self, user, quitMessage):
		""" called by twisted,
			of a C{user} quits
		"""
		self._apirunner("userQuit",{"user":user,"quitMessage":quitMessage})

	def yourHost(self, info):
		""" called by twisted
			with information about the IRC-Server we are connected to
		"""
		self.logger.debug(str(info))
		pass
	
	def ctcpQuery(self, user, channel, messages):
		""" called by twisted,
			if a C{user} sent a ctcp query
		"""
		self._apirunner("ctcpQuery",{"user":user,"channel":channel,"messages":messages})
		
	def userRenamed(self, oldname, newname):
		""" called by twisted,
			if a user changed his nick
		"""
		self._apirunner("userRenamed",{"oldname":oldname,"newname":newname})
		for chan in self.users:
			if self.users[chan].has_key(oldname):
				self.users[chan][newname]=self.users[chan][oldname]
				del self.users[chan][oldname]		

	def topicUpdated(self, user, channel, newTopic):
		""" called by twisted
			if the topic was updated
		"""
		self._apirunner("topicUpdated",{"user":user,"channel":channel,"newTopic":newTopic})

	def irc_RPL_ENDOFNAMES(self, prefix, params):
		self._apirunner("irc_RPL_ENDOFNAMES",{"prefix":prefix,"params":params})
	def irc_RPL_NAMREPLY(self, prefix, params):
		self._apirunner("irc_RPL_NAMREPLY",{"prefix":prefix,"params":params})
		for nick in params[3].strip().split(" "):
			if nick[0] in "@%+!":
				s=nick[0]
				nick=nick[1:]
			else:
				s=" "
			self.users[params[2]][nick]={'modchar':s}		

	def lineReceived(self, line):
		""" called by twisted
			for every line which was received from the IRC-Server
		"""
		#self.logger.debug(str(line))
		# adding a correct hostmask for join, part and quit
		self._apirunner("lineReceived", {"line":line})
		if line.split(" ")[1] == "JOIN" and line[1:].split(" ")[0].split("!")[0] != self.nickname:
			self.userJoined(line[1:].split(" ")[0],string.lower(line.split(" ")[2][1:]))
			#self.joined(line[1:].split(" ")[0],line.split(" ")[2][1:])
		elif line.split(" ")[1] == "PART" and line[1:].split(" ")[0].split("!")[0] != self.nickname:
			self.userLeft(line[1:].split(" ")[0],line.split(" ")[2])
		elif line.split(" ")[1] == "QUIT":
			self.userQuit(line[1:].split(" ")[0],line.split("QUIT :")[1])
		else:
			irc.IRCClient.lineReceived(self,line)
	
	def sendLine(self, line):
		self._apirunner("sendLine",{"line":line})
		irc.IRCClient.sendLine(self, line)
	def logerror(self, logger, module, exception):
		""" format a exception nicely and pass it to the logger
			@param logger: the logger instance to use
			@param module: the module in which the exception occured
			@type module: string
			@param exception: the exception
			@type exception: exception
		"""
		if type(exception) == self.DependencyMissing:
			logger.error("Dependency missing in module %s: %s is not active."%(module, str(exception)))
			return
		elif type(exception) == self.WontStart:
			logger.info('Module "%s" will not start because "%s".'%(module, str(exception)))
			return
		logger.error("Exception in Module "+module+": "+str(exception))
		tb_list = traceback.format_tb(sys.exc_info()[2])
		for entry in tb_list:
			for line in entry.strip().split("\n"):
				logger.error(line)
	def disconnect(self):
		"""disconnects cleanly from the current network"""
		self._apirunner("stop")
		self.quit('Bye')		
