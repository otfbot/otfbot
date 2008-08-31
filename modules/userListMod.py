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
# (c) 2008 by Robert Weidlich
#
""" keeps track of the users, which are in a channel """
import chatMod
class chatMod(chatMod.chatMod):
	""" abstract class for a botmodule	"""
	def __init__(self, bot):
		self.bot=bot
		self.bot.users={}
		self.modchars={'a':'!','o':'@','h':'%','v':'+'}
		self.modcharvals={'!':4,'@':3,'%':2,'+':1,' ':0}
	def joined(self, channel):
		self.bot.users[channel]={}		
	def connectionMade(self):
		"""made connection to server"""
		pass
	def connectionLost(self,reason):
		"""lost connection to server"""
		pass
	def signedOn(self):
		"""successfully signed on"""
		pass
	def left(self, channel):
		del self.bot.users[channel]
	def modeChanged(self, user, channel, set, modes, args):
		i=0
		for arg in args:
			if modes[i] in self.modchars.keys() and set == True:
				if self.modcharvals[self.modchars[modes[i]]] > self.modcharvals[self.bot.users[channel][arg]['modchar']]:
					self.bot.users[channel][arg]['modchar'] = self.modchars[modes[i]]
			elif modes[i] in self.modchars.keys() and set == False:
				#FIXME: ask for the real mode
				self.bot.users[channel][arg]['modchar'] = ' '
			i=i+1
	def kickedFrom(self, channel, kicker, message):
		left(channel)
	def userKicked(self, kickee, channel, kicker, message):
		userLeft(kickee, channel)
	def userJoined(self, user, channel):
		self.bot.users[channel][user.split("!")[0]]={'modchar':' '}		
	def userLeft(self, user, channel):
		del self.bot.users[channel][user.split("!")[0]]		
	def userQuit(self, user, quitMessage):
		for chan in self.bot.users:
			if self.bot.users[chan].has_key(user):
				del self.bot.users[chan][user]
	def userRenamed(self, oldname, newname):
		for chan in self.bot.users:
			if self.bot.users[chan].has_key(oldname):
				self.bot.users[chan][newname]=self.bot.users[chan][oldname]
				del self.bot.users[chan][oldname]
	def irc_RPL_NAMREPLY(self, prefix, params):
		for nick in params[3].strip().split(" "):
			if nick[0] in "@%+!":
				s=nick[0]
				nick=nick[1:]
			else:
				s=" "
			self.bot.users[params[2]][nick]={'modchar':s}
