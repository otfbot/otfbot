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

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.users={}

	def query(self, user, channel, msg):
		"""
		Authentification for some access-levels.
		User, password and access level can be found in the userdb.
		in default the path to the userdb is data/authMod/userdb.yaml,
		but you can specify your own path by setting the authMod.userdb
		option in the config file to your path.
		
		The user-file has to look like this:
			"
			networkname:
			  username: password(md5-hash!),access-level
			"
		You can specify as many networks and users as you want.
		"""
		#user=user.split("!")[0]
		import yaml,md5
		if msg[0:9] == "identify ":
			yamlfile = open(self.bot.getConfig("userdb","data/authMod/userdb.yaml","authMod"),"r")
			a = ""
			for i in yamlfile.readlines():
				a = a + i
			users = yaml.load(a)
			users = users[self.network]
			if users[msg.split(" ")[1].lower()].split(",")[0] == md5.md5(msg.split(" ",2)[2]).hexdigest():
				self.bot.sendmsg(user.split("!")[0], "Password accepted")
				self.logger.info("User "+str(user)+" successfully identified with password as user " + str(msg.split(" ")[1]))
				self.users[user] = int(users[msg.split(" ")[1].lower()].split(",")[1])
				self.bot.sendmsg(user.split("!")[0], "You has been identifyed as user " + str(msg.split(" ")[1]) + " with access level " + str(users[msg.split(" ")[1].lower()].split(",")[1]))
				self.logger.info("User "+str(user)+" now has access level " + str(users[msg.split(" ")[1].lower()].split(",")[1]))

	def auth(self, user):
		#user=user.split("!")[0]
		"""
		Returns the access-level of the given user.
		"""
		try:
			return self.users[user]
		except:
			return 0
