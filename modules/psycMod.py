# OtfBot module to allow the botowner to control the bot with psyc commands
#
# Otfbot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Otfbot is distributed in the hope that it will be useful,
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

import string, re
import chatMod, functions

def default_settings():
	settings={};
	settings['psycmod.psyccommand']='!psyc'
	settings['psycmod.psyccmdchar']='!psyc'
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot

	def command(self, user, channel, command, options):
		user = user.split("!")[0] #only nick
		if self.bot.auth(user) > 5 and command="psyc":
			self.bot.sendmsg(channel, self.bot.getConfig('psycmod.psyccmdchar', '+')+options)
