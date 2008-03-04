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

import urllib, re, string
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		self.autoTiny=self.bot.getConfig("auto", "False", "tinyurlMod", self.bot.network)
		self.autoTinyLength=int(self.bot.getConfig("autoLength", "35", "tinyurlMod", self.bot.network))

	def command(self, user, channel, command, options):
		if command == "tinyurl":
			url=urllib.urlopen("http://tinyurl.com/api-create.php?url="+options)
			self.bot.sendmsg(channel, url.read())
			url.close()
	def msg(self, user, channel, msg):
		if not self.autoTiny:
			return

		#http://www.truerwords.net/2539
		regex=re.match(".*((ftp|http|https):(([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2}){2,}(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?([A-Za-z0-9$_+!*();/?:~-])).*", msg)
		if regex:
			url=regex.group(1)
			if string.lower(user.split("!")[0]) != string.lower(self.bot.nickname) and not "tinyurl.com" in url:
				if len(url) > self.autoTinyLength:
					self.command(user, channel, "tinyurl", url)
