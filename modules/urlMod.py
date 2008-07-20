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

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		self.parser = titleExtractor()
		self.autoTiny=self.bot.getConfig("autotiny", "False", "urlMod", self.bot.network)
		self.autoTinyLength=int(self.bot.getConfig("autoLength", "50", "urlMod", self.bot.network))
		self.autoPreview=self.bot.getConfig("autopreview", "False", "urlMod", self.bot.network)

	def command(self, user, channel, command, options):
		response = ""
		if command == "preview" or command == "tinyurl+preview":
			try:
				self.parser.feed(urlutils.download(options))
				if self.parser.get_result() != "":
					response += self.parser.get_result()
			except HTMLParseError, e:
				self.logger.debug(e)
				del self.parser
				self.parser=titleExtractor()
			self.parser.reset()
		elif command == "tinyurl" or command == "tinyurl+preview":
			response += " ("+urlutils.download("http://tinyurl.com/api-create.php?url="+options)+")"
		elif command == "googlefight":
			words=options.split(":")
			if len(words) == 2:
				data1=urlutils.download('http://www.google.de/search?hl=de&q="%s"'%words[0])
				data2=urlutils.download('http://www.google.de/search?hl=de&q="%s"'%words[1])

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
				if not "tinyurl.com" in url and len(url) > self.autoTinyLength and self.autoTiny:
					mask+=1
				if self.autoPreview:
					mask+=2
			if mask == 1:
				self.command(user, channel, "tinyurl", url)
			if mask == 2:
				self.command(user, channel, "preview", url)
			if mask == 3:
				self.command(user, channel, "tinyurl+preview", url)
			mask=0


			
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
