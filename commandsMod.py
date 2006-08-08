#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import string, re, functions

def default_settings():
	settings={};
	settings['commandsMod_fileencoding']='iso-8859-15'
	settings['commandsMod_file']='commands.txt'
	return settings
		
class chatMod:
	def __init__(self, bot):
		self.bot = bot
		self.commandsFile=bot.getConfig("commandsMod_file", "commands.txt")
		self.commands = functions.loadProperties(self.commandsFile)
		
	def joined(self, channel):
		self.channel = channel
	
	def msg(self, user, channel, msg):
		user = user.split("!")[0] #only nick
		if msg[0] == "!":
			if msg == "!reload-commands":
				self.logger.info("reloading")
				self.reload()
				return
			answer = self.respond(user, msg)
			if answer != "":
				self.bot.sendme(channel, answer, self.bot.getConfig("commandsMod_fileencoding", "iso-8859-15"))
			
	def reload(self):
		self.commands = functions.loadProperties(self.commandsFile)

	def respond(self, user, command):
		answer = ""
		for key in self.commands.keys():
			#print command[1:len(key)]
			action = string.lower(command[1:len(key)+1])
			#TODO: "key_" without "key"
			if action == string.lower(key):
				if string.lower(command[1:]) == key: #exact match
					#return self.commands[key]
					#answer = re.sub("USER", user, self.commands[key])
					answer = self.commands[key]
					answer = re.sub("USER", user, answer)
				else: #with nick?
					if self.commands.has_key(key+"_"):
						otherNick = command[len(key)+1:]
						otherNick = otherNick[1:] #strip whitespace between command and nick
						if len(otherNick)>0 and otherNick[-1] == " ": #strip whitespace at end (if any)
							otherNick = otherNick[0:-1]
							
						answer = self.commands[key+"_"]
						answer = re.sub("USER", user, answer)
						answer = re.sub("OTHER", otherNick, answer)
		if len(answer)>0 and answer[-1] == "\n":
			return answer[0:-1]
		else:
			return answer
