# -*- coding: UTF-8 -*-
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
#

import string, re, random, time, atexit, os.path
import urllib, urllib2, socket
import chatMod, functions

MEGAHAL=1
NIALL=1
try:
	import mh_python
except ImportError:
	MEGAHAL=0
try:
	import niall
except ImportError:
	NIALL=0

class responder:
	"""a prototype of a artificial intelligence responder. 
	It does nothing at all, but it contains all the methods
	needed to extend it for a ai-responder"""
	def __init__(self):
		pass
	def learn(self, string):
		"""learns a new string, without responding"""
		pass
	def reply(self, msg):
		"""reply to a string, potentially learning it"""
		return ""
	def cleanup(self):
		"""cleanup before shutdown, if needed"""
		pass

def ascii_string(msg):
	"""
	make sure, the string uses only ascii chars
	(at the moment it removes any char but a-ZA-Z@. and space)

	Example:

	>>> ascii_string("Umlaute: äöüÜÖÄß!")
	'Umlaute aeoeueUeOeAess'
	"""
	msg=re.sub("ö", "oe", msg)
	msg=re.sub("ü", "ue", msg)
	msg=re.sub("ä", "ae", msg)
	msg=re.sub("ß", "ss", msg)
	msg=re.sub("Ö", "Oe", msg)
	msg=re.sub("Ü", "Ue", msg)
	msg=re.sub("Ä", "Ae", msg)
	return re.sub("[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@. ]", "", msg)

class udpResponder(responder):
	def __init__(self, bot):
		self.bot=bot
		self.host=self.bot.getConfig("host", "", "kiMod", self.bot.network)
		self.remoteport=int(self.bot.getConfig("remoteport", "", "kiMod", self.bot.network))
		self.localport=int(self.bot.getConfig("localport", "", "kiMod", self.bot.network))
		self.socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.settimeout(10)
		self.socket.bind(("", self.localport))
	def learn(self, msg):
		self.socket.sendto(msg, (self.host, self.remoteport))
		self.socket.recvfrom(8*1024)
	def reply(self, msg):	
		self.socket.sendto(msg, (self.host, self.remoteport))
		return ascii_string(self.socket.recvfrom(8*1024)[0].strip())

class webResponder(responder):
	def __init__(self, bot):
		self.bot=bot
	def learn(self, msg):
		url=self.bot.getConfig("url", "", "kiMod", self.bot.network)
		urllib2.urlopen(url+urllib.quote(msg)).read()
	def reply(self, msg):	
		url=self.bot.getConfig("url", "", "kiMod", self.bot.network)
		return ascii_string(urllib2.urlopen(url+urllib.quote(msg)).read())

class niallResponder(responder):
	def __init__(self, bot):
		niall.init()
		niall.set_callbacks(bot.logger.info, bot.logger.warning, bot.logger.error)
		niall.load_dictionary("niall.dict")
	def learn(self, msg):
		try:
			msg=ascii_string(unicode(msg, "UTF-8").encode("iso-8859-15"))
		except UnicodeEncodeError:
			return
			#pass
		except UnicodeDecodeError:
			return
			#pass
		if msg:
			niall.learn(str(msg))
			niall.save_dictionary("niall.dict")
	def reply(self, msg):
		try:
			msg=ascii_string(unicode(msg, "UTF-8").encode("iso-8859-15"))
		except UnicodeEncodeError:
			return
			#pass
		except UnicodeDecodeError:
			return
			#pass
		reply=unicode(niall.reply(str(msg)), "iso-8859-15").encode("UTF-8")
		if reply==None:
			reply=""
		if msg:
			niall.learn(str(msg))
		return reply
	def cleanup(self):
		#niall.save_dictionary("niall.dict")
		niall.free()

class megahalResponder(responder):
	"""implements a responder based on the megahal ai-bot"""
	def __init__(self, bot):
		"""starts the megahal program"""
		mh_python.setnobanner()
		mh_python.setdir(datadir)
		mh_python.initbrain()
		self.bot=bot
	def learn(self, msg):
		"""learns msg without responding
		@type	msg:	string
		@param	msg:	the string to learn
		"""
		try:
			msg=unicode(msg, "UTF-8").encode("iso-8859-15")
		except UnicodeEncodeError:
			return
			#pass
		except UnicodeDecodeError:
			return
			#pass
		mh_python.learn(msg)
	def reply(self, msg):
		"""replies to msg, and learns it
		@param	msg: the string to reply to
		@type	msg: string
		@rtype: string
		@returns the answer of the megahal bot
		"""
		try:
			string=unicode(msg, "UTF-8").encode("iso-8859-15")
		except UnicodeEncodeError:
			return ""
			#pass
		except UnicodeDecodeError:
			return ""
			#pass
		return unicode(mh_python.doreply(string), "iso-8859-15").encode("UTF-8")

	def cleanup(self):
		"""clean megahal shutdown"""
		mh_python.cleanup()



class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		if hasattr(self.bot, "nickname"): #on reload, because "connectionMade" is not invoked for a reloaded kiMod
			self.lnickname=string.lower(self.bot.nickname)

	def start(self):
		self.channels=[]
		self.wordpairsFile=self.bot.getPathConfig("wordpairsFile", datadir, "wordpairs.txt")#XXX: this needs to be utf-8 encoded
		self.wordpairs=functions.loadProperties(self.wordpairsFile)
		self.nicklist=[string.lower(self.bot.getConfig("nickname", "otfbot", "main", self.bot.network))]

		module=self.bot.getConfig("module", "megahal", "kiMod", self.bot.network)
		self.logger.debug("kiMod: using module "+module+",megahal="+str(MEGAHAL)+",niall="+str(NIALL))
		if module=="niall":
			if NIALL:
				self.responder=niallResponder(self.bot)
				self.logger.info("kiMod: using niall module")
			else:
				self.logger.warning("Cannot use niall. Module niall not availible.")
				if MEGAHAL:
					self.logger.info("Using Megahal instead")
					self.responder=megahalResponder(self.bot)
				else:
					self.logger.info("Using no KI.")
					self.responder=responder() #null responder
		elif module=="megahal":
			if MEGAHAL:
				self.responder=megahalResponder(self.bot)
			else:
				self.logger.warning("Cannot use megahal. Module mh_python not availible.")
				self.responder=responder() #null responder
				#Fallback
				if NIALL:
					self.logger.warning("Trying niall instead.")
					self.responder=niallResponder(self.bot)
		elif module=="web":
			self.responder=webResponder(self.bot)
		elif module=="udp":
			self.responder=udpResponder(self.bot)
		atexit.register(self.responder.cleanup)

	def joined(self, channel):
		self.channels.append(channel)
	def query(self, user, channel, msg):
		user=user.split("!")[0]
		if user[0:len(self.lnickname)]==self.lnickname:
			return
		if string.lower(user) in self.bot.getConfig("ignore", "", "kiMod", self.bot.network).split(","):
			return
		reply=self.responder.reply(msg)
		if not reply:
			return
		number=random.randint(1,1000)
		chance=int(self.bot.getConfig("answerQueryPercent", "70", "kiMod", self.bot.network))*10
		delay=len(reply)*0.3*float(self.bot.getConfig("wait", "2", "kiMod", self.bot.network)) #a normal user does not type that fast
		if number < chance:
			#self.bot.sendmsg(user, reply, "UTF-8")
			self.bot.scheduler.callLater(delay, self.bot.sendmsg, user, reply, "UTF-8")
	def msg(self, user, channel, msg):
		user=user.split("!")[0]
		if not user in self.nicklist:
			self.nicklist.append(string.lower(user))
		if string.lower(user) in self.bot.getConfig("ignore", "", "kiMod", self.bot.network, channel).split(","):
			return

		if user == self.bot.nickname:
			return
		#if not channel in self.channels: 
		#	return
		if msg[0]=="!":
			return
			

		reply=""

		#bot answers random messages
		number=random.randint(1,1000)
		chance=int(float(self.bot.getConfig("randomPercent", "0", "kiMod", self.bot.network, channel))*10)
		israndom=0
		if number < chance:
			israndom=1
		#bot answers if it hears its name
		ishighlighted=self.lnickname in string.lower(msg)
			

		#test, if it starts with user:
		for nick in self.nicklist:
			if string.lower(msg[0:len(nick)])==nick:
				msg=msg[len(nick)+1:] #cut of len of nick + one char (":", ",", " ", etc.)

		if len(msg) and msg[0]==" ": 
			msg=msg[1:]

		channel=string.lower(channel)
		if ishighlighted or israndom:
			reply=self.responder.reply(msg)
		else:
			self.responder.learn(msg)

		if reply:
			#reply=re.sub(" "+self.bot.nickname, " "+user, reply) #more secure to match only the name
			reply=re.sub(self.lnickname, user, str(reply), re.I) 
			for key in self.wordpairs.keys():
				reply=re.sub(key, self.wordpairs[key], reply, re.I)
			
			reply=re.sub("Http", "http", reply, re.I) #fix for nice urls

			if reply==string.upper(reply): #no UPPERCASE only Posts
				reply=string.lower(reply)
			delay=len(reply)*0.3*float(self.bot.getConfig("wait", "2", "kiMod", self.bot.network, channel)) #a normal user does not type that fast
			number=random.randint(1,1000)
			chance=int(self.bot.getConfig("answerPercent", "50", "kiMod", self.bot.network, channel))*10
			if israndom:
				#self.bot.sendmsg(channel, reply, "UTF-8")
				self.bot.scheduler.callLater(delay, self.bot.sendmsg, channel, reply, "UTF-8")
			elif number < chance: #apply answerPercent only on answers
				#self.bot.sendmsg(channel, user+": "+reply, "UTF-8")
				self.bot.scheduler.callLater(delay, self.bot.sendmsg, channel, user+": "+reply, "UTF-8")

	def connectionMade(self):
		self.lnickname=string.lower(self.bot.nickname)
	def connectionLost(self, reason):
		self.responder.cleanup()

	def stop(self):
		self.responder.cleanup()

if __name__ == "__main__":
	import doctest
	doctest.testmod()
