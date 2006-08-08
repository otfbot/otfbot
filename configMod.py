import random, re

#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along
#with this program; if not, write to the Free Software Foundation, Inc.,
#51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
class chatMod:
	def __init__(self, bot):
		self.bot=bot

	def msg(self, user, channel, msg):
		if self.bot.auth(user) and channel==self.bot.nickname:
			user=user.split("!")[0]
			if msg[0:6] == "config":
				msg=msg[7:]
				if msg[0:3] == "get":
					msg=msg[4:]
					print msg
					self.bot.sendmsg(user, msg+"="+self.bot.getConfig(msg, ""))
				elif msg[0:3] == "set":
					msg=msg[4:]
					tmp=msg.split("=")
					if len(tmp) != 2:
						self.bot.sendmsg(user, "Syntax: config set key=value")
						return
					self.bot.setConfig(tmp[0], tmp[1])
				else:
					self.bot.sendmsg(user, "Syntax: config [get <key>|set <key=value>]")
