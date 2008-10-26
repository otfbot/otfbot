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
# (c) 2007 by Robert Weidlich
# (c) 2008 by Alexander Schier
#

import chatMod, string
from twisted.internet import protocol, reactor
from twisted.words.protocols import irc
from twisted.words import service
from twisted.protocols import basic

def sendNames(server, network, channel):
	if network in server.bot.ipc.getall().keys():
		names=[server.bot.ipc[network].users[channel][nickname]['modchar'].strip()+nickname for nickname in server.bot.ipc[network].users[channel].keys()]
		server.names(server.name, "#"+network+"-"+channel, names)

class Plugin(chatMod.chatMod):
	def __init__(self, server):
		self.server=server
		self.mychannels=[]
		self.first=True
	def irc_USER(self, prefix, params):
		if not self.server.bot.mods['humanMod'].enabled:
			return
		if not self.first:
			return
		self.first=False
		for network in self.server.bot.ipc.getall():
			bot=self.server.bot.ipc[network]
			for channel in bot.channels:
				self.server.join(self.server.getHostmask(), "#"+network+"-"+channel)
				if channel in self.server.bot.users.keys():
					sendNames(self.server, network, channel)
				self.mychannels.append("#"+network+"-"+channel)
	def irc_PRIVMSG(self, prefix, params):
		if not self.server.bot.mods['humanMod'].enabled:
			return
		if params[0][0]=="#":
			if params[0] in self.mychannels:
				(network, channel)=params[0][1:].split("-",1)
				self.server.bot.ipc[network].sendmsg(channel, params[1])
		elif "-" in params[0]:
			(network, nick)=params[0].split("-", 1)
			self.server.bot.ipc[network].sendmsg(nick, params[1])
	def irc_JOIN(self, prefix, params):
		if not self.server.bot.mods['humanMod'].enabled:
			return
		try:
			(network, channel)=params[0][1:].split("-", 1) #[1:] and (a,b) can raise ValueErrors
			if network in self.server.bot.ipc.getall():
				if len(params)>=2: #password given
					self.server.bot.setConfig("password",params[1], "main", network, channel)
					self.server.bot.ipc[network].join(channel, params[1])
				else:
					self.server.bot.ipc[network].join(channel)
				self.server.join(self.server.getHostmask(), "#%s-%s"%(network, channel))
				if channel in self.server.bot.users.keys():
					sendNames(self.server, network, channel)
				#else: #should not be needed, every join produces a names list, which is maintained over /nick /part, etc.
				#	self.server.bot.ipc[network].names(channel) #invoke now, names will be in callback on chatMod
				self.mychannels.append("#%s-%s"%(network, channel))
		except ValueError:
			pass
	def irc_PART(self, prefix, params):
		if not self.server.bot.mods['humanMod'].enabled:
			return
		try:
			(network, channel)=params[0][1:].split("-", 1) #[1:] and (a,b) can raise ValueErrors
			if network in self.server.bot.ipc.getall():
				self.server.bot.ipc[network].part(channel)
				self.server.part(self.server.getHostmask(), "#%s-%s"%(network, channel))
				self.mychannels.remove("#%s-%s"%(network, channel))
		except ValueError:
			pass


