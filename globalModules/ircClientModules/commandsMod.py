# This file is part of OtfBot.
#
# Otfbot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Otfbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OtfBot; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
# (c) 2005, 2006, 2007 by Alexander Schier
#

import string, re
import chatMod, functions

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		self.channels=[]

	def connectionMade(self):
		self.reload()
		
	def joined(self, channel):
		self.commands[channel]=functions.loadProperties(self.bot.getPathConfig("file", datadir, "commands.txt", "commandsMod", self.bot.network, channel))
	
	def command(self, user, channel, command, options):
		user = user.split("!")[0] #only nick
		answer=self.respond(channel, user, command, options)
		if answer != "":
			if answer[0] == ":":
				self.bot.sendmsg(channel, answer[1:], self.bot.getConfig("commandsMod.fileencoding", "iso-8859-15"))
			else:
				self.bot.sendme(channel, answer, self.bot.getConfig("commandsMod.fileencoding", "iso-8859-15"))

	def start(self):
		self.commands={}
		self.commands["general"]=functions.loadProperties(self.bot.getPathConfig("file", datadir, "commands.txt","commandsMod"))
		self.commands["network"]=functions.loadProperties(self.bot.getPathConfig("file", datadir, "commands.txt","commandsMod", self.bot.network))
		for chan in self.bot.channels:
			self.joined(chan)

	def reload(self):
		self.start()
	
	def getCommand(self, channel, cmd):
		if not self.commands.has_key(channel):
			self.commands[channel]={}
		if self.commands.has_key(channel) and self.commands[channel].has_key(cmd):
			return self.commands[channel][cmd]
		elif self.commands.has_key("network") and self.commands["network"].has_key(cmd):
			return self.commands["network"][cmd]
		elif self.commands.has_key("general") and self.commands["general"].has_key(cmd):
			return self.commands["general"][cmd]
		else:
			return ""

	def respond(self, channel, user, command, options):
		"""
		respond to a command, substituting USER by the actual user
		and OTHER by the given options

		>>> c=chatMod(None)
		>>> c.commands={} #just for the example to work
		>>> c.commands['general']={"test": "USER wanted a test", "test_": "USER wanted to show OTHER how it works"}
		>>> c.commands['network']={}
		>>> #example begins here:
		>>> c.respond("", "testuser", "test", "")
		'testuser wanted a test'
		>>> c.respond("", "testuser", "test", "you")
		'testuser wanted to show you how it works'
		"""
		answer = ""
		if len(options) >1:
			answer=self.getCommand(channel, command+"_")
			answer = re.sub("OTHER", options, answer)
		else:
			answer=self.getCommand(channel, command)
		answer = re.sub("USER", user, answer)
				
		if len(answer)>0 and answer[-1] == "\n":
			return answer[0:-1]
		else:
			return answer
