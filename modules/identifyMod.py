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
# (c) 2005-2007 by Alexander Schier
# (c) 2006, 2006 by Robert Weidlich
#

import random, re, time
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.sent_identification=False

	def connectionMade(self):
		self.password = str(self.bot.getConfig("password", "", "identifyMod", self.bot.network))
	
	def signedOn(self):
		self.identify()
		
	def identify(self):
		if self.password != "":
			self.logger.info("identifying to nickserv")
			self.bot.sendmsg("nickserv", "identify "+self.password)
			self.sent_identification=True
		if self.bot.getBoolConfig("setBotFlag", "True", "identifyMod", self.bot.network):
			self.logger.info("setting usermode +b")
			self.bot.mode(self.bot.nickname, 1, "B")
			
	def noticed(self, user, channel, msg):
		user=user.split("!")[0]
		if (user.lower() == "nickserv" and self.sent_identification):
			self.logger.debug(user+": "+msg)
