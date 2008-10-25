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

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.modes={}
		self.modes["op"]={"char": "o", "set": 1}
		self.modes["deop"]={"char": "o", "set": 0}
		self.modes["voice"]={"char": "v", "set": 1}
		self.modes["devoice"]={"char": "v", "set": 0}
		self.modes["halfop"]={"char": "h", "set": 1}
		self.modes["dehalfop"]={"char": "h", "set": 0}

	#def msg(self, user, channel, msg):
	def command(self, user, channel, command, options):
		user=user.split("!")[0]
		if self.bot.auth(user) > 2 and command in self.modes.keys():
			if options != "":
				self.bot.mode(channel, self.modes[command]["set"], self.modes[command]["char"], None, options)
			else:
				self.bot.mode(channel, self.modes[command]["set"], self.modes[command]["char"], None, user)
		if self.bot.auth(user) > 5 and command == "kick":
			if options != "":
				options=options.split(" ",1)
				if len(options) == 1:
					self.bot.kick(channel,options[0])
				elif len(options) == 2:
					self.bot.kick(channel,options[0],options[1])
			else:
				self.bot.kick(channel,user, "Requested.")
