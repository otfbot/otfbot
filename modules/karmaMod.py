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
# (c) 2007 by Alexander Schier
#

import chatMod
import functions

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.karma={}
		self.karma=functions.loadProperties(datadir+self.bot.getConfig("file", self.bot.getConfig("karmaMod.file", "/karma.txt"), "karmaMod", self.bot.network))
		self.verbose=self.bot.getBoolConfig("karmaMod.verbose", "true")
		self.freestyle=self.bot.getBoolConfig("karmaMod.freestyle", "true")

	def command(self, user, channel, command, options):
		if self.freestyle:
			if options[-2:]=="++":
				what=command+" "+options[:-2]
				self.karma_up(what)
				self.tell_karma(what, channel)
			elif options[-2:]=="--":
				what=command+" "+options[:-2]
				self.karma_down(what)
				self.tell_karma(what, channel)
			elif command[-2:]=="++":
				self.karma_up(command[:-2])
				self.tell_karma(command[:-2], channel)
			elif command[-2:]=="--":
				self.karma_down(command[:-2])
				self.tell_karma(command[:-2], channel)
		elif command == "karma":
			if options == "":
				self.bot.sendmsg(channel, "Nutzen: !karma name++ oder !karma name--")
			else:
				if options[-2:]=="++":
					self.karma_up(options[:-2])
					if self.verbose:
						self.tell_karma(options[:-2], channel)
				elif options[-2:]=="--":
					self.karma_down(options[:-2])
					if self.verbose:
						self.tell_karma(options[:-2], channel)
				else:
					self.tell_karma(options, channel)
	def tell_karma(self, what, channel):
		self.bot.sendmsg(channel, "Karma: "+what+": "+str(self.get_karma(what))) 
	def get_karma(self, what):
		if not what in self.karma.keys():
			self.karma[what]=0
		return self.karma[what]
	def do_karma(self, what, up):
		if not what in self.karma.keys():
			self.karma[what]=0
		if up:
			self.karma[what]=int(self.karma[what])+1
		else:
			self.karma[what]=int(self.karma[what])-1
	def karma_up(self, what):
		return self.do_karma(what, True)
	def karma_down(self, what):
		return self.do_karma(what, False)
	def connectionLost(self, reason):
		file=open(datadir+self.bot.getConfig("file", self.bot.getConfig("karmaMod.file", "/karma.txt"), "karmaMod", self.bot.network), "w")
		for user in self.karma.keys():
			file.write(user+"="+str(self.karma[user])+"\n")
		file.close()

