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
# (c) 2007 by Robert Weidlich
#

import random, re, string
import chatMod
from control import configShell, controlInterface

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.control={}
	
	def query(self, user, channel, msg):
		nick=user.split("!")[0]
		if self.control.has_key(user):
			self.bot.sendmsg(nick,self.control[user].input(msg))

	def command(self, user, channel, command, options):
		if command == "control" and self.bot.auth(user) > 7:
			self.control[user]=controlInterface(self.bot)
		if self.bot.auth(user) > -1 and command == "reload": #TODO: make "!" configurable
			for chatMod in self.bot.mods:
				if chatMod.name == options:
					chatMod.reload()
					self.logger.info("Reloading Settings of "+chatMod.name)