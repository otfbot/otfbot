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

from jc import Game
import chatMod

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.game=Game()
		self.gamechannel=""

	def query(self, user, channel, msg):
		(command, options)=msg.split(" ", 1)
		self.command(user, self.gamechannel, command, options)
	def command(self, user, channel, command, options):
		user=user.split("!")[0]
		if command=="newgame":
			self.gamechannel=channel
		if True: #command in ['nimm', 'zweifel', 'ich', 'remove', 'newgame', 'startgame', 'zahl']:
			lines=self.game.input(user, command, options)
			for line in lines:
				if line[1]==True:
					self.bot.sendmsg(channel, line[0])
				else:
					self.bot.sendmsg(user, line[0])
			