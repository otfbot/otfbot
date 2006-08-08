#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along
#with this program; if not, write to the Free Software Foundation, Inc.,
#51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Chat Bot"""

from twisted.protocols import irc
from twisted.internet import reactor, protocol

import os, random, string, re, threading, time, sys
import functions
import generalMod, commandsMod, identifyMod, rdfMod, badwordsMod, answerMod, logMod, kiMod, authMod, configMod, modeMod, marvinMod

classes = [ identifyMod, generalMod, authMod, configMod, logMod, commandsMod, answerMod, badwordsMod, rdfMod, kiMod, modeMod, marvinMod ]

config={}
def setConfig(option, value):
	config[option]=value
	writeConfig()
		
def getConfig(option, defaultvalue=""):
	if not config.has_key(option):
		setConfig(option, defaultvalue)
	return config[option]
	
def loadConfig(myconfigfile):
	myconfig=functions.loadProperties(myconfigfile)
	if not len(myconfig):
		for myclass in classes:
			try:
				modconfig=myclass.default_settings()
				for item in modconfig.keys():
					myconfig[item]=modconfig[item]
			except AttributeError:
				pass
		myconfig['server']=''
		myconfig['channel']=''
		myconfig['nickname']='chatBot'
		#write it
		file=open(configfile, "w")
		options=myconfig.keys()
		options.sort()
		for option in options:
			file.write(option+"="+myconfig[option]+"\n")
		file.close()
		print "Default Settings loaded."
		print "Edit config.txt to configure the bot."
		sys.exit(0)


	return myconfig
		
def writeConfig():
	file=open(configfile, "w")
	options=config.keys()
	options.sort()
	for option in options:
		file.write(option+"="+config[option]+"\n")
	file.close()


class Bot(irc.IRCClient):
	"""A Chat Bot"""
	def __init__(self):
		#list of mods, which the bot should use
		#you may need to configure them first
		self.classes = classes

		self.mods = []
		self.numMods = 0

		#loadConfig()

		self.nickname=self.getConfig("nickname", "chatBot")
		self.startMods()
		
	def startMods(self):
		for chatModule in self.classes:
			self.mods.append( chatModule.chatMod(self) )
			try:
				self.mods[-1].start()
			except AttributeError:
				pass

	def setConfig(self, option, value):
		return setConfig(option, value)
	def getConfig(self, option, defaultvalue=""):
		return getConfig(option, defaultvalue)
	def loadConfig(self):
		return loadConfig(configfile)
	def writeConfig(self):
		return writeConfig()

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
			#print "Unicode Decode Error with String:",msg
			#Try with Fallback encoding
			msg=unicode(msg, fallback).encode(self.getConfig("encoding", "UTF-8"))
		except UnicodeEncodeError:
			pass
			#print "Unicode Encode Error with String:",msg
			#use msg as is
			
		self.msg(channel, msg)
		self.privmsg(self.nickname, channel, msg)
		
	def sendme(self, channel, action, encoding="iso-8859-15"):
		"""msg function, that converts from iso-8859-15 to a encoding given in the config"""
		action=unicode(action, encoding).encode(self.getConfig("encoding", "UTF-8"))
			
		self.me(channel, action)
		self.action(self.nickname, channel, action)

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)
		for mod in self.mods:
			try:
				mod.connectionMade()
			except AttributeError:
				pass

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self)
		for mod in self.mods:
			try:
				mod.connectionLost(reason)
			except AttributeError:
				pass
	
	def signedOn(self):
		print "connected"
		self.join(self.factory.channel)
		for mod in self.mods:
			try:
				mod.signedOn()
			except AttributeError:
				pass
		
	def joined(self, channel):
		for mod in self.mods:
			try:
				mod.joined(channel)
			except AttributeError:
				pass
	
	def privmsg(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.msg(user, channel, msg)
			except AttributeError:
				pass

		if channel == self.nickname and msg == "!reload":
			for chatModule in self.classes:
				print "core: reloading "+chatModule.__name__
				reload(chatModule)
			for chatMod in self.mods:
				try:
					chatMod.stop()
				except AttributeError:
					pass
			self.mods=[]
			self.startMods()


	def noticed(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.noticed(user, channel, msg)
			except AttributeError:
				pass
				
	def action(self, user, channel, msg):
		for mod in self.mods:
			try:
				mod.action(user, channel, msg)
			except AttributeError:
				pass

	def modeChanged(self, user, channel, set, modes, args):
		for mod in self.mods:
			try:
				mod.modeChanged(user, channel, set, modes, args)
			except AttributeError:
				pass
	def userKicked(self, kickee, channel, kicker, message):
		for mod in self.mods:
			try:
				mod.userKicked(kickee, channel, kicker, message)
			except AttributeError:
				pass

	def userJoined(self, user, channel):
		for mod in self.mods:
			try:
				mod.userJoined(user, channel)
			except AttributeError:
				pass
				
	def userLeft(self, user, channel):
		for mod in self.mods:
			try:
				mod.userLeft(user, channel)
			except AttributeError:
				pass
				
	def userRenamed(self, oldname, newname):
		for mod in self.mods:
			try:
				mod.userRenamed(oldname, newname)
			except AttributeError:
				pass
				
	def topicUpdated(self, user, channel, newTopic):
		for mod in self.mods:
			try:
				mod.topicUpdated(user, channel, newTopic)
			except AttributeError:
				pass
		
	

class BotFactory(protocol.ClientFactory):
	"""The Factory for the Bot"""
	protocol = Bot

	def __init__(self, channel):
		self.channel = channel
	def clientConnectionLost(self, connector, reason):
		#print "connection lost: ", reason
		connector.connect()
		#reactor.stop() #for !stop
	def clientConnectionFailed(self, connector, reason):
		print "connection failed: ", reason
		reactor.stop()

if len(sys.argv)==2:
	configfile=sys.argv[1]
else:
	configfile="config.txt"
config=loadConfig(configfile)

f = BotFactory(getConfig("channel", "#bot-test"))
reactor.connectTCP(getConfig("server", "irc.insiderz.de"), 6667, f);
reactor.run()
