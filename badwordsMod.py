# -*- coding: iso-8859-1 -*-
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

import random, re
import functions

def default_settings():
	settings={};
	settings['badwordsMod_file']='badwords.txt'
	return settings
		
class chatMod:
	def __init__(self, bot):
		self.bot=bot
		self.badwordsFile=bot.getConfig("badwordsMod_file", "badwords.txt")
		self.badwords=functions.loadList(self.badwordsFile)
		self.channels = {}
		
	def joined(self, channel):
		self.channels[channel]=1
		
	def part(self, channel):
		self.channels[channel]=1

	def msg(self, user, channel, msg):
		if channel == self.bot.nickname:
			if msg == "!reload-badwords":
				self.badwords=functions.loadList(self.badwordsFile)
		else:
			for word in self.badwords:
				if self.channels.has_key(channel) and word != "" and re.search(word, msg, re.I) and user.split("!")[0]!=self.bot.nick:
					self.logger.info("kicking "+user.split("!")[0]+" for badword: "+word)
					self.bot.kick(channel, user.split("!")[0], "Badword: "+word)
