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

try:
	from twisted.words.protocols import irc
except ImportError:
	from twisted.protocols import irc

from twisted.internet import reactor, protocol

import os, random, string, re, threading, time, sys, traceback
import functions, config
import generalMod, commandsMod, identifyMod, badwordsMod, answerMod, logMod, authMod, configMod, modeMod, marvinMod , kiMod

classes = [ identifyMod, generalMod, authMod, configMod, logMod, commandsMod, answerMod, badwordsMod, modeMod, marvinMod ]
modchars={'a':'!','o':'@','h':'%','v':'+'}

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--config",dest="configfile",metavar="FILE",help="Location of configfile",type="string")
parser.add_option("-d","--debug",dest="debug",metavar="LEVEL",help="Show debug messages of level LEVEL (10, 20, 30, 40 or 50)", type="int")
(options,args)=parser.parse_args()
if options.debug and options.debug not in (10,20,30,40,50):
	parser.error("Unknown value for --debug")

import logging
# Basic settings for logging
# logging to logfile
#filelogger = logging.RotatingFileHandler('otfbot.log','a',20480,5)
filelogger = logging.FileHandler('otfbot.log','a')
logging.getLogger('').setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
filelogger.setFormatter(formatter)
logging.getLogger('').addHandler(filelogger)
#corelogger.addHandler(filelogger)

if options.debug:
	#logging to stdout
	console = logging.StreamHandler()
	logging.getLogger('').setLevel(options.debug)
	formatter = logging.Formatter('%(asctime)s %(name)-10s %(module)-18s %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)
	#corelogger.addHandler(console)
corelogger = logging.getLogger('core')


theconfig=None
def setConfig(option, value, module=None, network=None, channel=None):
	theconfig.set(option, value, module, network, channel)
	writeConfig()
		
def getConfig(option, defaultvalue="", module=None, network=None, channel=None):
	return theconfig.get(option, defaultvalue, module, network, channel)
def getBoolConfig(option, defaultvalue="", module=None, network=None, channel=None):
	if theconfig.get(option, defaultvalue, module, network, channel) in ["true", "on", "1"]:
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
		
		file=open(myconfigfile, "w")
		file.write(myconfig.exportxml())
		file.close()
		#no logger here: the user needs to read this on console, not in logfile
		print "Default Settings loaded."
		print "Edit config.xml to configure the bot."
		sys.exit(0)
	return myconfig
		
def logerror(logger, module, exception):
	logger.error("Exception in Module "+module+": "+str(exception))
	tb_list = traceback.format_tb(sys.exc_info()[2])
	for entry in tb_list:
		for line in entry.strip().split("\n"):
			logger.error(line)
	
def writeConfig():
	file=open(configfile, "w")
	#options=config.keys()
	#options.sort()
	#for option in options:
	#	file.write(option+"="+config[option]+"\n")
	file.write(theconfig.exportxml())
	file.close()


class Bot(irc.IRCClient):
	"""A Chat Bot"""
	def __init__(self):
		#list of mods, which the bot should use
		#you may need to configure them first
		self.classes = classes
		self.users={}
	
		self.mods = []
		self.numMods = 0

		self.versionName="OtfBot"
		self.versionNum=" svn 20"
		self.logging = logging
		self.logger = logging.getLogger("core")
		self.logger.info("Starting chatBotööä")
		self.startMods()
		
	def startMods(self):
		for chatModule in self.classes:
			self.mods.append( chatModule.chatMod(self) )
			self.mods[-1].setLogger(self.logger)
			self.mods[-1].name = chatModule.__name__
			try:
				self.mods[-1].start()
			except AttributeError:
				pass
          	
	def setConfig(self, option, value, module=None, network=None, channel=None):
		return setConfig(option, value, module, network, channel)
	def getConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		return getConfig(option, defaultvalue, module, network, channel)
	def getBoolConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		return getBoolConfig(option, defaultvalue, module, network, channel)
	def loadConfig(self):
		return loadConfig(configfile)
	def writeConfig(self):
		return writeConfig()
	def getUsers(self):
		return self.users

	def auth(self, user):
		"""test if the user is privileged"""
		for mod in self.mods:
			try:
				retval=mod.auth(user)
				if retval == 1:
					return 1
			except AttributeError:
				pass
		return 0
	
	
	def sendmsg(self, channel, msg, encoding="iso-8859-15", fallback="iso-8859-15"):
		"""msg function, that converts from iso-8859-15 to a encoding given in the config"""
		try:
			msg=unicode(msg, encoding).encode(self.getConfig("encoding", "UTF-8"))
		except UnicodeDecodeError:
			#self.logger.debug("Unicode Decode Error with String:"+str(msg))
			#Try with Fallback encoding
			msg=unicode(msg, fallback).encode(self.getConfig("encoding", "UTF-8"))
		except UnicodeEncodeError:
			pass
			#self.logger.debug("Unicode Encode Error with String:"+str(msg))
			#use msg as is
			
		self.msg(channel, msg)
		self.privmsg(self.nickname, channel, msg)
		
	def sendme(self, channel, action, encoding="iso-8859-15"):
		"""msg function, that converts from iso-8859-15 to a encoding given in the config"""
		action=unicode(action, encoding).encode(self.getConfig("encoding", "UTF-8"))
			
		self.me(channel, action)
		self.action(self.nickname, channel, action)

	def connectionMade(self):
		self.network=self.factory.network
		self.channels=self.factory.channels
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
			try:
				mod.connectionMade()
			except Exception, e:
				logerror(self.logger, mod.name, e)

	def connectionLost(self, reason):
		self.logger.info("lost connection: "+str(reason))
		irc.IRCClient.connectionLost(self)
		for mod in self.mods:
			try:
				mod.connectionLost(reason)
			except Exception, e:
				logerror(self.logger, mod.name, e)
	
	def signedOn(self):
		self.logger.info("signed on "+self.network)

		for channel in self.factory.channels:
			if(getBoolConfig("enabled", "false", "main", self.factory.network, channel)):
				self.join(unicode(channel).encode("iso-8859-1"))
		for mod in self.mods:
			try:
				mod.signedOn()
			except Exception, e:
				logerror(self.logger, mod.name, e)
		
	def joined(self, channel):
		self.logger.info("joined "+channel)
		self.users[channel]={}
		for mod in self.mods:
			try:
				mod.joined(channel)
			except Exception, e:
				logerror(self.logger, mod.name, e)
			
	def left(self, channel):
		self.logger.info("left "+channel)
		del self.users[channel]
		for mod in self.mods:
			try:
				mod.left(channel)
			except Exception, e:
				logerror(self.logger, mod.name, e)

	def privmsg(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.privmsg(user, channel, msg)
			except Exception, e:
				logerror(self.logger, mod.name, e)
			try:
				mod.msg(user, channel, msg)
			except Exception, e:
				logerror(self.logger, mod.name, e)

		if channel == self.nickname and msg == "!reload":
			for chatModule in self.classes:
				self.logger.info("reloading "+chatModule.name)
				reload(chatModule)
			for chatMod in self.mods:
				try:
					chatMod.stop()
				except Exception, e:
					logerror(self.logger, mod.name, e)
			self.mods=[]
			self.startMods()
		if msg == "!who":
			self.sendLine("WHO "+channel)
		if msg[:6] == "!whois":
			self.sendLine("WHOIS "+msg[7:])
		if msg == "!user":
			self.sendmsg(channel,str(self.users))

	def irc_unknown(self, prefix, command, params):
		#self.logger.debug(str(prefix)+" : "+str(command)+" : "+str(params))
		if command == "RPL_NAMREPLY":
			for nick in params[3].strip().split(" "):
				if nick[0] in "@%+!":
					s=nick[0]
					nick=nick[1:]
				else:
					s=" "
				self.users[params[2]][nick]={'modchar':s}
		for mod in self.mods:
			try:
				mod.irc_unknown(prefix, command, params)
			except Exception, e:
				logerror(self.logger, mod.name, e)
	

	def noticed(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.noticed(user, channel, msg)
			except Exception, e:
				logerror(self.logger, mod.name, e)
				
	def action(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.action(user, channel, msg)
			except Exception, e:
				logerror(self.logger, mod.name, e)

	def modeChanged(self, user, channel, set, modes, args):
		for mod in self.mods:
			try:
				mod.modeChanged(user, channel, set, modes, args)
			except Exception, e:
				logerror(self.logger, mod.name, e)
		#if modes == "b" and set == True:
		#	self.mode(channel,False,"b",None,None,args[0])
		#	#self.mode(channel,True,"m")
		#TODO: this should also handle the removal of modes and double modes (+vho)
		if modes in "aohv":
			self.users[channel][args[0]]['modchar'] = modchars[modes]

	def userKicked(self, kickee, channel, kicker, message):
		for mod in self.mods:
			try:
				mod.userKicked(kickee, channel, kicker, message)
			except Exception, e:
				logerror(self.logger, mod.name, e)

	def userJoined(self, user, channel):
		self.users[channel][user.split("!")[0]]={'modchar':' '}
		for mod in self.mods:
			try:
				mod.userJoined(user, channel)
			except Exception, e:
				logerror(self.logger, mod.name, e)
				
	def userLeft(self, user, channel):
		del self.users[channel][user.split("!")[0]]
		for mod in self.mods:
			try:
				mod.userLeft(user, channel)
			except Exception, e:
				logerror(self.logger, mod.name, e)
	
	def userQuit(self, user, quitMessage):
		for mod in self.mods:
			try:
				mod.userQuit(user, quitMessage)
			except Exception, e:
				logerror(self.logger, mod.name, e)
		for chan in self.users:
			if self.users[chan].has_key(user):
				del self.users[chan][user]
	def yourHost(self, info):
		pass
	
	def ctcpQuery(self, user, channel, messages):
		(query,t) = messages[0]
		answer = None
		#if query == "VERSION":
		#	answer = "chatBot - a python IRC-Bot"
		if answer: 
			self.ctcpMakeReply(user.split("!")[0], [(query,answer)])
			self.logger.info("Answered to CTCP "+query+" Request from "+user.split("!")[0])

		
	def userRenamed(self, oldname, newname):
		for chan in self.users:
			if self.users[chan].has_key(oldname):
				self.users[chan][newname]=self.users[chan][oldname]
				del self.users[chan][oldname]
		for mod in self.mods:
			try:
				mod.userRenamed(oldname, newname)
			except Exception, e:
				logerror(self.logger, mod.name, e)
				
	def topicUpdated(self, user, channel, newTopic):
		for mod in self.mods:
			try:
				mod.topicUpdated(user, channel, newTopic)
			except Exception, e:
				logerror(self.logger, mod.name, e)
	
	def lineReceived(self, line):
		#self.logger.debug(str(line))
		if line.split(" ")[1] == "JOIN" and line[1:].split(" ")[0].split("!")[0] != self.nickname:
			self.userJoined(line[1:].split(" ")[0],line.split(" ")[2][1:])
			#self.joined(line[1:].split(" ")[0],line.split(" ")[2][1:])
		elif line.split(" ")[1] == "PART":
			self.userLeft(line[1:].split(" ")[0],line.split(" ")[2])
		elif line.split(" ")[1] == "QUIT":
			self.userQuit(line[1:].split(" ")[0],line.split("QUIT :")[1])
		else:
			irc.IRCClient.lineReceived(self,line)
			
class BotFactory(protocol.ClientFactory):
	"""The Factory for the Bot"""
	protocol = Bot

	def __init__(self, networkname, channels):
		self.network=networkname
		self.channels = channels
	def clientConnectionLost(self, connector, reason):
		pass
		#connector.connect()
		#reactor.stop() #for !stop
	def clientConnectionFailed(self, connector, reason):
		reactor.stop()

try:
	configfile=parser.configfile
except AttributeError:
	configfile="config.xml"
theconfig=loadConfig(configfile)

networks=theconfig.getNetworks()
if networks:
	for network in networks:
		if(getBoolConfig('enabled', 'unset', 'main', network)):
			channels=theconfig.getChannels(network)
			if not channels:
				channels=[]
			for channel in channels:
				if(not getBoolConfig('enabled','unset','main', network)):
					channels.remove(channel)
			f = BotFactory(network, channels)
			reactor.connectTCP(unicode(network).encode("iso-8859-1"), 6667, f);
	reactor.run()
