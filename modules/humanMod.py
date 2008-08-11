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
#

import chatMod, string
from twisted.internet import protocol, reactor
from twisted.words.protocols import irc
from twisted.words import service
from twisted.protocols import basic

class serverMod:
	def __init__(self, server):
		self.server=server
		self.mychannels=[]
		self.first=True
	def irc_NICK(self, prefix, params):
		if not self.first:
			return
		self.first=False
		for network in self.server.bot.ipc.getall():
			bot=self.server.bot.ipc[network]
			for channel in bot.channels:
				self.server.join(self.server.getHostmask(), "#"+network+"-"+channel)
				self.server.names(self.server.name, "#"+network+"-"+channel, [self.server.bot.users[channel][nickname]['modchar'].strip()+nickname for nickname in self.server.bot.users[channel].keys()])
				self.mychannels.append("#"+network+"-"+channel)
	def irc_PRIVMSG(self, prefix, params):
		if params[0][0]=="#":
			if params[0] in self.mychannels:
				(network, channel)=params[0][1:].split("-",1)
				self.server.bot.ipc[network].sendmsg(channel, params[1])
		elif "-" in params[0]:
			#query. TODO: network-nick here too, to get the network
			(network, nick)=params[0].split("-", 1)
			self.server.bot.ipc[network].sendmsg(nick, params[1])
	def irc_JOIN(self, prefix, params):
		try:
			(network, channel)=params[0][1:].split("-", 1) #[1:] and (a,b) can raise ValueErrors
			if network in self.server.bot.ipc.getall():
				self.server.bot.ipc[network].join(channel)
				self.server.join(self.server.getHostmask(), "#%s-%s"%(network, channel))
				self.server.names(self.server.name, "#"+network+"-"+channel, [self.server.bot.users[channel][nickname]['modchar'].strip()+nickname for nickname in self.server.bot.users[channel].keys()])
				self.mychannels.append("#%s-%s"%(network, channel))
		except ValueError:
			pass
	def irc_PART(self, prefix, params):
		try:
			(network, channel)=params[0][1:].split("-", 1) #[1:] and (a,b) can raise ValueErrors
			if network in self.server.bot.ipc.getall():
				self.server.bot.ipc[network].part(channel)
				self.server.part(self.server.getHostmask(), "#%s-%s"%(network, channel))
				self.mychannels.remove("#%s-%s"%(network, channel))
		except ValueError:
			pass

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.enabled=self.bot.getBoolConfig("active", "False", "humanMod")
		if not self.enabled:
			return
		
	def msg(self, user, channel, msg):
		for server in self.bot.ipc.servers:
			if server.connected:
				server.sendmsg(user, "#"+self.network+"-"+channel, msg)
	def query(self, user, channel, msg):
		#TODO FIXME: this is a workaround. the external irc client does not recognize own messages from queries (xchat)
		#or are just the parameters wrong? so it will show the foreign nick, but prefix the message with <botnick>
		for server in self.bot.ipc.servers:
			if not server.connected:
				return
			if string.lower(user) == string.lower(self.bot.nickname):
				server.sendmsg(self.network+"-"+channel, server.name, "< %s> "%self.bot.nickname+msg)
			else:
				#server.sendmsg(self.network+"-"+user, self.bot.server.name, msg)
				server.sendmsg(self.network+"-"+user, server.name, "< %s> "%user.split("!")[0]+msg)
