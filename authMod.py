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
import chatMod

def default_settings():
	settings={};
	settings['authMod.whitelist']=''
	settings['authMod.password']=''
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.whitelist=[]
		for user in self.bot.getConfig("whitelist", "", "authMod").split(","):
			self.whitelist.append(user)
		self.password=self.bot.getConfig("password", "", "authMod")

	def msg(self, user, channel, msg):
		user=user.split("!")[0]
		if channel == self.bot.nickname and msg[0:9]=="identify ":
			if self.password != "" and msg[9:] == self.password:
				self.bot.sendmsg(user, "Password accepted")
				self.logger.info("User "+str(user)+" successfully identified with password")
				self.whitelist.append(user)

	def auth(self, user):
		user=user.split("!")[0]
		if user in self.whitelist:
			return 1
