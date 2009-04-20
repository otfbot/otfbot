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
# (c) 2008 by Thomas Wiegart
#

import random, re
import chatMod
from twisted.cred.credentials import UsernamePassword
from twisted.words.iwords import IUser

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.users={}

	def query(self, user, channel, msg):
		"""
		Uses the auth-service to identify a user. 
		If no username is given, the nickname is used.
		"""

		nick=user.split("!")[0]
		if msg[0:9] == "identify ":
			try:
				portal=self.bot.root.getNamedServices()["auth"]
			except KeyError:
				self.logger.error("auth-service unavailable")
				return
			msgs=msg.split(" ")
			if len(msgs) == 2:
				cred=UsernamePassword(nick,msgs[1])
			elif len(msgs) == 3:
				cred=UsernamePassword(msgs[1],msgs[2])
			else:
				 self.bot.sendmsg(nick, "Usage: identify [user] pass")
				 return
			d=portal.login(cred, self.bot.userlist[nick], IUser)
			d.addCallback(lambda args: self.bot.sendmsg(nick, "Successfully logged in as "+str(args[1].name)))
			d.addErrback(lambda failure: self.bot.sendmsg(nick, "Login failed: "+str(failure.getErrorMessage())))
			
	def auth(self, user):
		user=user.split("!")[0]
		"""
		Returns the access-level of the given user.
		"""
		try:
			if hasattr(self.bot.userlist[user], 'avatar'):
				return 10
		except:
			return 0