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
from lib import chatMod

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		#self.bot.depends("serverMod")
		self.enabled=self.bot.config.getBool("active", False, "humanMod") and self.bot.config.get("active", False, "serverMod")
		if not self.enabled:
			raise self.bot.WontStart("humanMod is disabled.")
		
	def msg(self, user, channel, msg):
		if not self.enabled:
			return
		for server in self.bot.root.getNamedServices()['ircServer'].services():
			server=server.args[2].protocol
			if server.connected:
				server.sendmsg(user, "#"+self.network+"-"+channel, msg)
	def query(self, user, channel, msg):
		if not self.enabled:
			return
		#TODO FIXME: this is a workaround. the external irc client does not recognize own messages from queries (xchat)
		#or are just the parameters wrong? so it will show the foreign nick, but prefix the message with <botnick>
		for server in self.bot.root.getNamedServices()['ircServer'].services():
			server=server.args[2].protocol
			if not server.connected:
				return
			if string.lower(user) == string.lower(self.bot.nickname):
				server.sendmsg(self.network+"-"+channel, server.name, "< %s> "%self.bot.nickname+msg)
			else:
				#server.sendmsg(self.network+"-"+user, self.bot.server.name, msg)
				server.sendmsg(self.network+"-"+user, server.name, "< %s> "%user.split("!")[0]+msg)
	def irc_RPL_ENDOFNAMES(self, prefix, params):
		if not self.enabled:
			return
		for server in self.bot.root.getNamedServices()['ircServer'].services():
			server=server.args[2].protocol
			if server.connected:
				sendNames(server, self.network, params[1])
