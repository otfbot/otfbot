# This file is part of OtfBot.
# -*- coding: utf-8 -*-
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
# (c) 2008 by Robert Weidlich
#

import urllib2, re, string
import chatMod
import urlutils
from HTMLParser import HTMLParser
from HTMLParser import HTMLParseError

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		self.parser = titleExtractor()
		self.autoTiny=self.bot.config.get("autotiny", False, "urlMod", self.bot.network)
		self.autoTinyLength=int(self.bot.config.get("autoLength", "50", "urlMod", self.bot.network))
		self.autoPreview=self.bot.config.get("autopreview", False, "urlMod", self.bot.network)
		self.autoServerinfo=self.bot.config.get("autoserverinfo", False, "urlMod", self.bot.network)

	def command(self, user, channel, command, options):
		response = ""
		self.parser= titleExtractor()
		headers=None
		if "preview" in command:
			if not headers:
				headers=urlutils.get_headers(options)
			try:
				if headers['content-type'].lower()[:9] == "text/html":
					self.parser.feed(urlutils.download(options))
					if self.parser.get_result() != "":
						response += self.parser.get_result()
			except HTMLParseError, e:
				self.logger.debug(e)
				del self.parser
				self.parser=titleExtractor()
			self.parser.reset()
		if "tinyurl" in command:
			response += " ("+urlutils.download("http://tinyurl.com/api-create.php?url="+options)+")"
		if "serverinfo" in command:
			if not headers:
				headers=urlutils.get_headers(options)
			response += " (Server: %s)"%headers['server']
		if command == "googlefight":
			words=options.split(":")
			if len(words) == 2:
				data1=urlutils.download('http://www.google.de/search?hl=de&q="%s"'%words[0].replace(" ","+"))
				data2=urlutils.download('http://www.google.de/search?hl=de&q="%s"'%words[1].replace(" ","+"))

				count1="0"
				count2="0"
				match=re.match(".*<b>1</b> - <b>10</b>.*?<b>([0-9\.]*)</b>.*", data1, re.S)
				if match:
					count1=match.group(1)
				else:
					print data1
				match=re.match(".*<b>1</b> - <b>10</b>.*?<b>([0-9\.]*)</b>.*", data2, re.S)
				if match:
					count2=match.group(1)

				if(int(re.sub("\.", "", count1))>int(re.sub("\.", "", count2))):
					self.bot.sendmsg(channel, "Google Fight!: %s siegt ueber %s (%s zu %s Treffer)"%(words[0], words[1], str(count1), count2))
				else:
					self.bot.sendmsg(channel, "Google Fight!: %s siegt ueber %s (%s zu %s Treffer)"%(words[1], words[0], str(count2), count1))
			else:
				self.bot.sendmsg(channel, "!googlefight wort1:wort2")
		if response != "":
			self.bot.sendmsg(channel, "[Link Info] "+response)

	def msg(self, user, channel, msg):
		mask=0		
		# http://www.truerwords.net/2539
		regex=re.match(".*((ftp|http|https):(([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2}){2,}(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?([A-Za-z0-9$_+!*();/?:~-])).*", msg)
		if regex:
			url=regex.group(1)
			if string.lower(user.split("!")[0]) != string.lower(self.bot.nickname):
				cmd=""
				if not "tinyurl.com" in url and len(url) > self.autoTinyLength and self.autoTiny:
					cmd+="+tinyurl"
				if self.autoPreview:
					cmd+="+preview"
				if self.autoServerinfo:
					cmd+="+serverinfo"
				self.command(user, channel, cmd, url)

			
class titleExtractor(HTMLParser):
        intitle=False
        title=""
        def handle_starttag(self, tag, attrs):
                if tag == "title":
                        self.intitle=True
                else:
                        self.intitle=False
        def handle_endtag(self, tag):
                if tag == "title":
                        self.intitle=False
        def handle_data(self, data):
                if self.intitle:
                        self.title = data
        def get_result(self):
                return self.title
