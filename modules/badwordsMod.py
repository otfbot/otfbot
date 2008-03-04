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

import random, re
import chatMod, functions

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.badwordsFile=bot.getPathConfig("file", datadir, "badwords.txt","badwordsMod")
		self.badwords=functions.loadList(self.badwordsFile)

	def reload(self):
		self.badwords=functions.loadList(self.badwordsFile)

	def msg(self, user, channel, msg):
		for word in self.badwords:
			if channel in self.bot.channels and word != "" and re.search(word, msg, re.I):
				self.logger.info("kicking "+user.split("!")[0]+" for badword: "+word)
				self.bot.kick(channel, user.split("!")[0], "Badword: "+word)
