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
# (c) 2005, 2006 by Alexander Schier
#

import string, re, functions
import chatMod
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot

	def start(self):
		self.answersFile=datadir+self.bot.getConfig("file", "/answers.txt", "answerMod")
		self.answers = functions.loadProperties(self.answersFile)

	def msg(self, user, channel, msg):
		user = user.split("!")[0] #only nick
		if channel in self.bot.channels: #Do not respond to server messages
			answer = self.respond(user, msg)
			if answer != "":
				self.bot.sendmsg(channel, answer, self.bot.getConfig("fileencoding", "iso-8859-15","answerMod"))

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
