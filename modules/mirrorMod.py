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
# (c) 2008 by Alexander Schier
#

import random, re
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot

	def msg(self, user, channel, msg):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "< %s> %s"%(user.split("!")[0],msg))
	def action(self, user, channel, message):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "* %s %s "%(user.split("!")[0], message))
	def kickedFrom(self, channel, kicker, message):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "%s was kicked from %s by %s [%s]"%(self.bot.nickname, channel, kicker, message))
	def userKicked(self, kickee, channel, kicker, message):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "%s was kicked from %s by %s [%s]"%(kickee, channel, kicker, message))
	def userJoined(self, user, channel):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "%s has joined %s"%(user.split("!")[0], channel))
	def userLeft(self, user, channel):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "%s has left %s"%(user.split("!")[0], channel))
	def userQuit(self, user, quitMessage):
		for (network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			if self.network == network:
				(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
				self.bot.ipc[target_network].sendmsg(target_channel, "%s has quit [%s]"%(user.split("!")[0], quitMessage))
	def userRenamed(self, oldname, newname):
		for (network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			if self.network == network:
				(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
				self.bot.ipc[target_network].sendmsg(target_channel, "%s is now known as %s"%(oldname, newname))
	def modeChanged(self, user, channel, set, modes, args):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			sign="+"
			if not set:
				sign="-"
			self.bot.ipc[target_network].sendmsg(target_channel, "mode/"+channel+" ["+sign+modes+" "+" ".join(args)+"] by "+user.split("!")[0])
	def joined(self, channel):
		if (self.network, channel) in self.bot.hasConfig("mirrorto", "mirrorMod")[2]:
			(target_network, target_channel)=self.bot.getConfig("mirrorto", "unset", "mirrorMod", self.network, channel).split("-", 1)
			self.bot.ipc[target_network].sendmsg(target_channel, "joined %s"%(channel))
