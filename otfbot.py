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
# (c) 2005, 2006 by Alexander Schier
# (c) 2006 by Robert Weidlich
# 

"""Chat Bot"""
from twisted.words.protocols import irc

from twisted.internet import reactor, protocol, error, ssl
import os, random, string, re, sys, traceback, atexit
import functions, config, scheduler

###############################################################################
# Parse commandline options
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--config",dest="configfile",metavar="FILE",help="Location of configfile",type="string")
parser.add_option("-d","--debug",dest="debug",metavar="LEVEL",help="Show debug messages of level LEVEL (10, 20, 30, 40 or 50). Implies -f.", type="int", default=0)
parser.add_option("-f","--nodetach",dest="foreground",help="Do not fork into background.",action="store_true", default=False)

parser.add_option("-u","--user",dest="userid",help="if run as root, the bot needs a userid to chuid to.",type="int", default=0)
parser.add_option("-g","--group",dest="groupid",help="if run as root, the bot needs a groupid to chgid to.",type="int", default=0)

(options,args)=parser.parse_args()
if options.debug and options.debug not in (10,20,30,40,50):
	parser.error("Unknown value for --debug")
###############################################################################
#check for root rights
if os.getuid()==0:
	if options.userid and options.userid!=0 and options.groupid and options.groupid!=0:
		from twisted.python.util import switchUID
		#os.chroot(".") #DOES NOT WORK. pwd.getpwuid fails in switchUID, when chrooted.
		switchUID(options.userid, options.groupid)
	else:
		print "Otfbot should not be run as root."
		print "please use -u and -g to specify a userid/groupid"
		sys.exit(1)
###############################################################################
# Detaching from console
if options.foreground == False and not options.debug > 0:
	try:
		import subprocess
		subprocess.Popen([sys.argv[0],"-f"])
		sys.exit(0)
	except ImportError:
		pass
###############################################################################
# Setup Logging
import logging
import logging.handlers
# Basic settings for logging
# logging to logfile
filelogger = logging.handlers.RotatingFileHandler('otfbot.log','a',1048576,5)
#filelogger = logging.FileHandler('otfbot.log','a')
logging.getLogger('').setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
filelogger.setFormatter(formatter)
logging.getLogger('').addHandler(filelogger)
#corelogger.addHandler(filelogger)

if options.debug > 0:
	# logging to stdout
	console = logging.StreamHandler()
	logging.getLogger('').setLevel(options.debug)
	formatter = logging.Formatter('%(asctime)s %(name)-10s %(module)-18s %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)
	#corelogger.addHandler(console)
corelogger = logging.getLogger('core')
corelogger.info("Starting OtfBot - Version svn "+"$Revision$".split(" ")[1])

def logerror(logger, module, exception):
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

###############################################################################

def exithook():
	""" This function is called, when the program terminates. """
	# remove Pidfile
	os.remove(pidfile)
	writeConfig()
	corelogger.info("Bot shutted down")
	corelogger.info("-------------------------")

# Load modules
sys.path.insert(1,"modules")
classes=[]
for file in os.listdir("modules"):
	if len(file)>=3 and file[-3:]==".py":
		classes.append(__import__(file[:-3]))
		classes[-1].datadir = "modules/"+classes[-1].__name__+"-data"
		corelogger.debug("Loading module "+classes[-1].__name__)

###############################################################################
# some config functions
theconfig=None
def setConfig(option, value, module=None, network=None, channel=None):
	theconfig.set(option, value, module, network, channel)
	writeConfig()
		
def hasConfig(option, module=None):
	return theconfig.has(option, module)
def getConfig(option, defaultvalue="", module=None, network=None, channel=None):
	return theconfig.get(option, defaultvalue, module, network, channel)
def getBoolConfig(option, defaultvalue="", module=None, network=None, channel=None):
	if theconfig.get(option, defaultvalue, module, network, channel) in ["True","true","On","on","1"]:
		return True
	return False

def loadConfig(myconfigfile):
	if os.path.exists(myconfigfile):
		myconfig=config.config(logging, myconfigfile)
	else:
		myconfig=config.config(logging)
		for myclass in classes:
			try:
				modconfig=myclass.default_settings()
				for item in modconfig.keys():
					myconfig.set(item, modconfig[item])
			except AttributeError:
				pass
		
		myconfig.set('enabled', 'false', 'main', 'irc.samplenetwork')
		myconfig.set('enabled', 'false', 'main', 'irc.samplenetwork', '#example')
		myconfig.set('nickname', 'OtfBot', 'main')
		myconfig.set('encoding', 'UTF-8', 'main')
		myconfig.set('pidfile','otfbot.pid','main')
		
		file=open(myconfigfile, "w")
		file.write(myconfig.exportxml())
		file.close()
		#no logger here: the user needs to read this on console, not in logfile
		print "Default Settings loaded."
		print "Edit config.xml to configure the bot."
		sys.exit(0)
	return myconfig

def writeConfig():
	file=open(configfile, "w")
	#options=config.keys()
	#options.sort()
	#for option in options:
	#	file.write(option+"="+config[option]+"\n")
	file.write(theconfig.exportxml())
	file.close()


# some constants, can be retrieved from serveranswer while connecting.
modchars={'a':'!','o':'@','h':'%','v':'+'}
modcharvals={'!':4,'@':3,'%':2,'+':1,' ':0}

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
	def __init__(self):
		#list of mods, which the bot should use
		#you may need to configure them first
		self.classes = classes
		self.users={}
		self.channels=[]
		self.network=None
	
		self.mods = []
		self.numMods = 0

		self.versionName="OtfBot"
		self.versionNum="svn "+"$Revision$".split(" ")[1]
		self.logging = logging
		self.logger = logging.getLogger("core")
		self.logger.info("Starting new Botinstance")
		self.scheduler = scheduler.Scheduler(self.getReactor())
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
		for mod in self.mods:
			if (args.has_key("channel") and args["channel"] in self.channels and self.getBoolConfig("enabled","True",mod.name,self.network,args["channel"])) or not args.has_key("channel") or args["channel"] not in self.channels:
				try:
					getattr(mod,apifunction)(**args)
				except Exception, e:
					logerror(self.logger, mod.name, e)
	
	# public API
	def startMods(self):
		"""
			initializes all known modules
		"""
		for chatModule in self.classes:
			#if self.getConfig("enabled","true",chatModule.__name__,self.network)
			self.mods.append( chatModule.chatMod(self) )
			self.mods[-1].setLogger(self.logger)
			self.mods[-1].name = chatModule.__name__
			#try:
			#	self.mods[-1].start()
			#except AttributeError:
			#	pass
		self._apirunner("start")

	# configstuff, should maybe be moved to a config-instance at self.config
	def setConfig(self, option, value, module=None, network=None, channel=None):
		return setConfig(option, value, module, network, channel)
	def hasConfig(self, option, module=None):
		return hasConfig(option, module)
	def getConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		return getConfig(option, defaultvalue, module, network, channel)
	def getBoolConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		return getBoolConfig(option, defaultvalue, module, network, channel)
	def getSubOptions(self, list):
		return theconfig.getsubopts(list)
	def getNetworks(self):
		return theconfig.getNetworks()
	def getChannels(self,net):
		return theconfig.getChannels(net)
	def loadConfig(self):
		return loadConfig(configfile)
	def writeConfig(self):
		return writeConfig()

	def getUsers(self):
		""" Get a list of users
			@rtype: dict
			@return: a dict with the channelnames as keys
		"""
		return self.users
	def getReactor(self):
		""" get the reactor 
			@rtype: twisted.internet.reactor
			@return: the current reactor
		"""
		return reactor
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
		for mod in self.mods:
			try:
				retval=mod.auth(user)
				if retval > level:
					level=retval
			except AttributeError:
				pass
		return level
	
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
		try:
			msg=unicode(msg, encoding).encode(self.getConfig("encoding", "UTF-8", "main"))
		except UnicodeDecodeError:
			#self.logger.debug("Unicode Decode Error with String:"+str(msg))
			#Try with Fallback encoding
			msg=unicode(msg, fallback).encode(self.getConfig("encoding", "UTF-8", "main"))
		except UnicodeEncodeError:
			pass
			#self.logger.debug("Unicode Encode Error with String:"+str(msg))
			#use msg as is
			
		self.msg(channel, msg)
		self.privmsg(self.nickname, channel, msg)
		
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
		action=unicode(action, encoding).encode(self.getConfig("encoding", "UTF-8", "main"))
			
		self.me(channel, action)
		self.action(self.nickname, channel, action)
	
	def reloadModules(self):
		"""
			call this to reload all modules
		"""
		for chatModule in self.classes:
			self.logger.info("reloading "+chatModule.__name__)
			reload(chatModule)
		for chatMod in self.mods:
			try:
				chatMod.stop()
			except Exception, e:
				logerror(self.logger, mod.name, e)
		self.mods=[]
		self.startMods()	
	
	# Callbacks
	def connectionMade(self):
		""" 
			this is called by twisted
			, when the connection to the irc-server was made
		"""
		self.network=self.transport.addr[0]
		tmp=self.getChannels(self.network)
		if tmp:
			self.channels=tmp
		self.nickname=unicode(self.getConfig("nickname", "OtfBot", 'main', self.network)).encode("iso-8859-1")
		if len(self.network.split(".")) < 2:
			nw = self.network
		else:
			nw = self.network.split(".")[-2]
		self.logger = self.logging.getLogger(nw)
		self.logger.info("made connection to "+self.network)
		irc.IRCClient.connectionMade(self)
		for mod in self.mods:
			mod.setLogger(self.logger)
			mod.network=self.network
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
			if(getBoolConfig("enabled", "false", "main", self.network, channel)):
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
		self.setConfig("enabled", "True", "main", self.network, channel)

	def left(self, channel):
		""" called by twisted,
			if we left a channel
			@param channel: the channel we left
			@type channel: string
		"""
		self.logger.info("left "+channel)
		del self.users[channel]
		self.channels.remove(channel)
		self._apirunner("left",{"channel":channel})
		self.setConfig("enabled", "False", "main", self.network, channel) #disable the channel for the next start of the bot

	def isupport(self, options):
		self.logger.debug(options)
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
		if char==self.getConfig("commandChar", "!", "main").encode("UTF-8"):
			tmp=msg[1:].split(" ", 1)
			command=tmp[0]
			if len(tmp)==2:
				options=tmp[1]
			else:
				options=""
			self._apirunner("command",{"user":user,"channel":channel,"command":command,"options":options})
			#return

		if channel.lower() == self.nickname.lower():
			self._apirunner("query",{"user":user,"channel":channel,"msg":msg})
		
		# to be removed
		self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})
		# to be called for messages in channels
		self._apirunner("msg",{"user":user,"channel":channel,"msg":msg})
		#nick = user.split("!")[0]
		#if channel == self.nickname and self.auth(nick) > 9:
		#if msg == "!who":
		#	self.sendLine("WHO "+channel)
		#if msg[:6] == "!whois":
		#	self.sendLine("WHOIS "+msg[7:])
		#if msg == "!user":
		#	self.sendmsg(channel,str(self.users))

	def irc_unknown(self, prefix, command, params):
		""" called by twisted
			for every line that has no own callback
		"""
		#self.logger.debug(str(prefix)+" : "+str(command)+" : "+str(params))
		#parse /names-list which is sent when joining a channel
		if command == "RPL_NAMREPLY":
			for nick in params[3].strip().split(" "):
				if nick[0] in "@%+!":
					s=nick[0]
					nick=nick[1:]
				else:
					s=" "
				self.users[params[2]][nick]={'modchar':s}
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
		self._apirunner("modeChanged",{"user":user,"channel":channel,"set":set,"modes":modes,"args":args})
		i=0
		for arg in args:
			if modes[i] in modchars.keys() and set == True:
				if modcharvals[modchars[modes[i]]] > modcharvals[self.users[channel][arg]['modchar']]:
					self.users[channel][arg]['modchar'] = modchars[modes[i]]
			elif modes[i] in modchars.keys() and set == False:
				#FIXME: ask for the real mode
				self.users[channel][arg]['modchar'] = ' '
			i=i+1

	def userKicked(self, kickee, channel, kicker, message):
		""" called by twisted,
			if a user was kicked
		"""
		self._apirunner("userKicked",{"kickee":kickee,"channel":channel,"kicker":kicker,"message":message})

	def userJoined(self, user, channel):
		""" called by twisted,
			if a C{user} joined the C{channel}
		"""
		self._apirunner("userJoined",{"user":user,"channel":channel})
		self.users[channel][user.split("!")[0]]={'modchar':' '}

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
		for chan in self.users:
			if self.users[chan].has_key(user):
				del self.users[chan][user]

	def yourHost(self, info):
		""" called by twisted
			with information about the IRC-Server we are connected to
		"""
		pass
	
	#def ctcpQuery(self, user, channel, messages):
	#	(query,t) = messages[0]
	#	answer = None
	#	#if query == "VERSION":
	#	#	answer = "chatBot - a python IRC-Bot"
	#	if answer: 
	#		self.ctcpMakeReply(user.split("!")[0], [(query,answer)])
	#		self.logger.info("Answered to CTCP "+query+" Request from "+user.split("!")[0])
		
	def userRenamed(self, oldname, newname):
		""" called by twisted,
			if a user changed his nick
		"""
		for chan in self.users:
			if self.users[chan].has_key(oldname):
				self.users[chan][newname]=self.users[chan][oldname]
				del self.users[chan][oldname]
		self._apirunner("userRenamed",{"oldname":oldname,"newname":newname})

	def topicUpdated(self, user, channel, newTopic):
		""" called by twisted
			if the topic was updated
		"""
		self._apirunner("topicUpdated",{"user":user,"channel":channel,"newTopic":newTopic})

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

class BotFactory(protocol.ReconnectingClientFactory):
	"""The Factory for the Bot"""
	protocol = Bot
	instances = {}

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
			corelogger.info("Not Connected to any network. Shutting down.")
			#TODO: add sth to stop modules
			reactor.stop()
	
	def clientConnectionLost(self, connector, reason):
		clean = error.ConnectionDone()
		if reason.getErrorMessage() == str(clean):
			self._removenetwork(connector.host)
			self._checkforshutdown()
			corelogger.info("Cleanly disconnected from "+connector.host)
		else:
			corelogger.error("Disconnected from "+connector.host+": "+str(reason.getErrorMessage())+".")
			protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		#	connector.connect()
		
	def clientConnectionFailed(self, connector, reason):
		corelogger.error("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
		self._removenetwork(connector.host)
		protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		#self._checkforshutdown()
	
	def buildProtocol(self,addr):
		proto=protocol.ReconnectingClientFactory.buildProtocol(self,addr)
		self._addnetwork(addr.host, proto)
		return proto

try:
	configfile=parser.configfile
except AttributeError:
	configfile="config.xml"
theconfig=loadConfig(configfile)

# writing PID-File
pidfile=theconfig.get('pidfile','otfbot.pid','main')
f=open(pidfile,'w')
f.write(str(os.getpid())+"\n")
f.close()

# registering the exithook function
atexit.register(exithook)

networks=theconfig.getNetworks()
connections={}
if networks:
	f = BotFactory()
	for network in networks:
		if(getBoolConfig('enabled', 'unset', 'main', network)):
			#channels=theconfig.getChannels(network)
			#if not channels:
			#	channels=[]
			#for channel in channels:
			#	if(not getBoolConfig('enabled','unset','main', network)):
			#		channels.remove(channel)
			password=getConfig('password', '', 'main', network)
			if(password!=""):
				f.protocol.password=unicode(password).encode("iso-8859-1")

			if (getBoolConfig('ssl','False','main',network)):
				s = ssl.ClientContextFactory()
				connections[network]=reactor.connectSSL(unicode(network).encode("iso-8859-1"), int(getConfig('port','6697','main',network)), f,s);
			else:
				connections[network]=reactor.connectTCP(unicode(network).encode("iso-8859-1"), int(getConfig('port','6667','main',network)), f)
	reactor.run()
