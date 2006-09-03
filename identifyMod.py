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
# (c) 2006 by Robert Weidlich
#

import random, re, time
import chatMod
from threading import Thread

def default_settings():
	settings={};
	settings['identifyMod.password']=''
	settings['identifyMod.setBotFlag']='true'
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot

	def connectionMade(self):
		self.password = str(self.bot.getConfig("password", "", "identifyMod", self.bot.network))
	
	def dowhois(self):
		time.sleep(1)
		self.bot.sendLine("WHOIS "+str(self.bot.nickname))

	def signedOn(self):
		if self.password != "":
			self.logger.info("identifying to nickserv")
			self.bot.sendmsg("nickserv", "identify "+self.password, "iso-8859-1")
			Thread(target=self.dowhois).start()
			self.whois=True
		if self.bot.getBoolConfig("setBotFlag", "True", "identifyMod", self.bot.network):
			self.logger.info("setting usermode +b")
			self.bot.mode(self.bot.nickname, 1, "B")
	
	def irc_unknown(self, prefix, command, params):
		if command == "RPL_WHOISUSER" and params[0] == self.bot.nickname and self.whois:
			self.mywhois=True
			self.ident=False
		if command in ['307','320'] and self.mywhois and params[0] == self.bot.nickname:
			self.logger.info("Identification was successful")
			self.ident=True
		if command == "RPL_ENDOFWHOIS" and params[0] == self.bot.nickname and self.mywhois:
			if self.ident==False:
				self.logger.warn("Identification failed")
			self.mywhois=False
			self.whois=False
