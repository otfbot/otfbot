import random, re

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

def default_settings():
	settings={};
	settings['identifyMod_password']=''
	settings['identifyMod_setBotFlag']='true'
	return settings
		
class chatMod:
	def __init__(self, bot):
		self.bot=bot
		self.password = bot.getConfig("identifyMod_password", "")

	def signedOn(self):
		if self.password != "":
			self.logger.info("identifying to nickserv")
			self.bot.sendmsg("nickserv", "identify "+self.password)
		if self.bot.getConfig("identifyMod_setBotFlag", "true")=="true":
			self.logger.info("setting usermode +b")
			self.bot.mode(self.bot.nickname, 1, "B")
