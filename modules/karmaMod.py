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
# (c) 2007 by Alexander Schier
#

import chatMod
import functions

class chatMod(chatMod.chatMod):
	def default_settings():
		settings={};
		settings['karmaMod.file']=datadir+'/karma.txt'
		return settings

	def __init__(self, bot):
		self.bot=bot
		self.karma={}
		self.karma=functions.loadProperties(self.bot.getConfig("file", datadir+"/karma.txt", "karmaMod", self.bot.network))

	def command(self, user, channel, command, options):
		if command == "karma":
			if options == "":
				self.bot.sendmsg(channel, "Nutzen: !karma name++ oder !karma name--")
			else:
				if (options[-2:]=="++" or options[-2:]=="--") and not options[:-2] in self.karma.keys():
					self.karma[options[:-2]]=0
				elif not options in self.karma.keys():
					self.karma[options]=0
				if options[-2:]=="++":
					self.karma[options[:-2]]=self.karma[options[:-2]]+1
				elif options[-2:]=="--":
					self.karma[options[:-2]]=self.karma[options[:-2]]-1
				else:
					self.bot.sendmsg(channel, "Karma: "+options+": "+str(self.karma[options])) 
	def connectionLost(self, reason):
		file=open(self.bot.getConfig("file", datadir+"/karma.txt", "karmaMod", self.bot.network), "w")
		for user in self.karma.keys():
			file.write(user+"="+str(self.karma[user])+"\n")
		file.close()

