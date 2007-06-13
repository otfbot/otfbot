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

import random, re, string
import chatMod
from control import configShell, controlInterface

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.control={}
	
	def msg(self, user, channel, msg):
		nick=user.split("!")[0]
		if self.bot.auth(user) > 7 and string.lower(channel)==string.lower(self.bot.nickname):
			if not self.control.has_key(user):
				self.control[user]=controlInterface(self.bot)
			self.bot.sendmsg(nick,self.control[user].input(msg))

		#elif channel==self.bot.nickname:
		#	self.bot.sendmsg(nick,"Not authorized")
		elif self.bot.auth(user) > -1 and msg[0] == "!": #TODO: make "!" configurable
			if msg[1:7] == "reload":
				if len(msg.split(" ")) == 2:
					for chatMod in self.bot.mods:
						if chatMod.name == msg.split(" ")[1]:
							try:
								chatMod.reload()
								self.logger.info("Reloading Settings of "+chatMod.name)
							except Exception, e:
								self.logger.error("Error while reloading "+chatMod.name)
