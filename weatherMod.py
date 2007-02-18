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
# (c) 2005, 2006 by Alexander Schier
# (c) 2007 by Robert Weidlich
#


### Parsers ###
import xml.sax
import xml.sax.handler
import urllib

class weatherParserOne(xml.sax.handler.ContentHandler):
	"""Parses the answer of the CityCode Search"""
	def __init__(self):
		self.content = []
		
		self.inSearch = 0;
		self.inLoc = 0;
		
		self.currentLoc = -1;
		self.currentLocText = "";

	def startElement(self, name, attributes):
		if name == "search":
			self.inSearch = 1
		if name == "loc":
			self.inLoc = 1
			self.currentLoc += 1
			self.content.append({'code':attributes.getValue('id')})


	def characters(self, data):
		if self.inSearch:
			if self.inLoc:
				self.currentLocText += data

	def endElement(self, name):
		if name == "search":
			self.inSearch = 0;
		if name == "loc":
			self.content[self.currentLoc]['text'] = self.currentLocText
			self.currentLocText = ""
			self.inLoc = 0;

def getLocationCode(location):
	"""wrapperfunction for the weatherParserOne"""
	try:
		parser = xml.sax.make_parser()
		handler = weatherParserOne()
		parser.setContentHandler(handler)
		parser.parse("http://xoap.weather.com/search/search?where="+urllib.quote_plus(location))
		return handler.content
	except xml.sax._exceptions.SAXParseException:
		print "weatherParserOne: Parse Exception"
		return []

class weatherParserTwo(xml.sax.handler.ContentHandler):
	"""Parses the actual weatherdata into a dict"""
	def __init__(self):
		self.content = {}
		
		self.inChannel = 0;
		self.inItem = 0;
		self.Item = "";
		self.inSub = 0;
		self.Sub = "";
		
		self.currentText = "";

	def startElement(self, name, attributes):
		if name == "channel":
			self.inChannel = 1
		if name == "item":
			self.inItem = 1
		if name in ["title","description","lastBuildDate","ttl"] and not self.inItem:
			self.inSub = 1
			self.Sub = name
		if name in ["yweather:location", "yweather:units","yweather:wind","yweather:atmosphere","yweather:astronomy","yweather:condition","geo:lat","geo:long"]:
			vals={}
			for attr in attributes.getNames():
				vals[attr]=attributes.getValue(attr)
			self.content[name.split(":")[1]] = vals
		print name

	def characters(self, data):
		if self.inChannel:
			if self.inItem:
				pass
			if self.inSub:
				self.currentText += data

	def endElement(self, name):
		if name == "channel":
			self.inChannel = 0;
		if name == "item":
			self.inItem = 0;
		if name == self.Sub:
			self.inSub = 0;
			self.content[self.Sub] = self.currentText
			self.currentText = ""
			self.inSub = 0;

def getWeather(location):
	"""wrapperfunction for weatherParserTwo"""
	try:
		parser = xml.sax.make_parser()
		handler = weatherParserTwo()
		parser.setContentHandler(handler)
		codes = getLocationCode(location)
		if len(codes) < 1:
			return [{'error':'No Location found'}]
		parser.parse("http://xml.weather.yahoo.com/forecastrss/"+str(code)+"_c.xml")
		return handler.content
	except xml.sax._exceptions.SAXParseException:
		print "weatherParserTwo: Parse Exception"
		return []

### otfBot-Modulecode ####

import string, re, functions, time
import chatMod


def default_settings():
	settings={};
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		self.time=time.time()
		self.commands = ["wetter"]
		
	def msg(self, user, channel, msg):
		nick=user.split("!")[0]
		cmd=msg.split(" ")[0][1:]
		if cmd in self.commands and (time.time() - self.time) < 5:
			self.bot.sendmsg(channel,"Wait a minute ...")
		elif cmd in self.commands:
			self.time = time.time()
			if cmd == "wetter":
				c = getWeather(" ".join(msg.split(" ")[1:]))
				if c.has_key('error'):
					self.bot.sendmsg(channel,"No such Location found")
				self.bot.sendmsg(channel,"Weather for "+str(c['location']['city'])+" ("+str(c['location']['country'])+"): "+str(c['condition']['text'])+", "+str(c['condition']['temp'])+str(c['units']['temperature']))
