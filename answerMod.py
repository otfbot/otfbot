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
	settings['answerMod_fileencoding']='iso-8859-15'
	settings['answerMod_file']='answers.txt'
	return settings
		
class chatMod:
	def __init__(self, bot):
		self.bot = bot

		self.answersFile=bot.getConfig("answerMod_file", "answers.txt")
		self.answers = functions.loadProperties(self.answersFile)
		self.channels={}
		
	def joined(self, channel):
		self.channels[channel]=1
	
	def msg(self, user, channel, msg):
		user = user.split("!")[0] #only nick
		if(self.channels.has_key(channel)): #Do not respond to server messages
			if msg == "!reload-answers":
				self.logger.info("reloading")
				self.reload()
				return
			answer = self.respond(user, msg)
			if answer != "":
				self.bot.sendmsg(channel, answer, self.bot.getConfig("answerMod_fileencoding", "iso-8859-15"))

	def reload(self):
		self.answers = functions.loadProperties(self.answersFile)

	def respond(self, user, msg):
		answer = ""
		for key in self.answers.keys():
			if re.search(key, msg, re.I):
				answer = self.answers[key]
				answer = re.sub("USER", user, answer)
				answer = re.sub("MESSAGE", msg, answer)
		if len(answer)>0 and answer[-1] == "\n":
			return answer[0:-1]
		else:
			return answer
