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

import string, re, random, time, atexit
import chatMod, functions

MEGAHAL=1
CITE=1
NIALL=1
try:
	import mh_python
except ImportError:
	MEGAHAL=0
try:
	import MySQLdb
except ImportError:
	CITE=0
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

class niallResponder(responder):
	def __init__(self):
		niall.init()
		niall.load_dictionary("niall.dict")
	def learn(self, msg):
		try:
			msg=unicode(msg, "UTF-8").encode("iso-8859-15")
		except UnicodeEncodeError:
			return
			#pass
		except UnicodeDecodeError:
			return
			#pass
		niall.learn(str(msg))
	def reply(self, msg):
		try:
			msg=unicode(msg, "UTF-8").encode("iso-8859-15")
		except UnicodeEncodeError:
			return
			#pass
		except UnicodeDecodeError:
			return
			#pass
		reply=unicode(niall.reply(msg), "iso-8859-15").encode("UTF-8")
		niall.learn(msg)
		return reply
	def cleanup(self):
		niall.save_dictionary("niall.dict")
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

class citeResponder(responder):
	def __init__(self, bot):
		self.host=bot.getConfig("mysqlHost", "", "kiMod", bot.network)
		self.user=bot.getConfig("mysqlUser", "", "kiMod", bot.network)
		self.passwd=bot.getConfig("mysqlPasswd", "", "kiMod", bot.network)
		self.database=bot.getConfig("mysqlDB", "chatbot", "kiMod", bot.network)
		self.keywordsTable=bot.getConfig("keywordsTable", "keywords", "kiMod", bot.network)
		self.stringsTable=bot.getConfig("stringsTable", "strings", "kiMod", bot.network)
		self.maxStrings=int(bot.getConfig("maxStrings", "1000", "kiMod", bot.network))
		self.logger=bot.logger
		
		try:
			self.db=MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.database)
			self.cursor=self.db.cursor()
		except MySQLdb.OperationalError:
			raise "boterror", "Error Connecting the DB"
		self.cursor.execute("SHOW TABLES;");
		tmp=self.cursor.fetchall()
		#get list of tables
		tables=[]
		for i in tmp:
			tables.append(i[0])
		
		#create tables, if needed
		if not self.keywordsTable in tables:
			self.cursor.execute("CREATE TABLE "+MySQLdb.escape_string(self.keywordsTable)+"(keyword TEXT, stringid INT);");
			self.logger.info("created keywords table:"+self.keywordsTable)
		if not self.stringsTable in tables:
			self.cursor.execute("CREATE TABLE "+MySQLdb.escape_string(self.stringsTable)+"(id INT AUTO_INCREMENT, string TEXT, PRIMARY KEY(id));");
			self.logger.info("created strings table:"+self.stringsTable)

	def learn(self, string):
		cursor=self.cursor;
		words=self.getwords(string)
		self.cursor.execute("SELECT id FROM "+MySQLdb.escape_string(self.stringsTable)+" WHERE string = '"+MySQLdb.escape_string(string)+"';")
		if len(words) >1 and not len(self.cursor.fetchall()): #Do not learn single word / do not leran something twice
			self.cursor.execute("INSERT INTO "+MySQLdb.escape_string(self.stringsTable)+" (string) VALUES (\""+MySQLdb.escape_string(string)+"\");")
			self.cursor.execute("SELECT LAST_INSERT_ID();")
			id=(self.cursor.fetchall())[0][0];
			if id>self.maxStrings:
				self.cursor.execute("DELETE FROM "+MySQLdb.escape_string(self.stringsTable)+" WHERE id < "+MySQLdb.escape_string(str(id-self.maxStrings)));
			for word in words:
				if word!="":
					self.cursor.execute("INSERT INTO "+MySQLdb.escape_string(self.keywordsTable)+" VALUES (\""+MySQLdb.escape_string(word)+"\","+MySQLdb.escape_string(str(id))+");")
				if id>self.maxStrings:
					self.cursor.execute("DELETE FROM "+MySQLdb.escape_string(self.keywordsTable)+" WHERE stringid < "+MySQLdb.escape_string(str(id-self.maxStrings)));

	def reply(self, msg):
		#self.learn(msg)
		ids=()
		words=self.getwords(msg)
		notwords=[]
		reply=""
		#try to find the best(long) keyword in database
		while len(words) and len(ids)==0:
			topword=""
			for word in words:
				if len(word) > len(topword):
					topword=word
			#print "Topword: "+topword
			self.cursor.execute("SELECT stringid FROM "+MySQLdb.escape_string(self.keywordsTable)+" WHERE keyword LIKE '%"+MySQLdb.escape_string(topword)+"%';")
			ids=(self.cursor.fetchall());
			if len(ids)==0:
				notwords.append(topword)
			words2=[]
			for word in words:
				if not word in notwords:
					words2.append(word)
			words=words2

		if len(ids):
			id=random.choice(ids)[0] #choose one (if multiple matches)
			self.cursor.execute("SELECT string FROM "+MySQLdb.escape_string(self.stringsTable)+" WHERE id='"+MySQLdb.escape_string(str(id))+"';")
			ret=self.cursor.fetchall()
			if len(ret):
				reply=(ret)[0][0]
		self.learn(msg)
		return reply

	def getwords(self, string):
		#string=re.sub("[.,!?;\"':]", " ", string)
		string=re.sub("[.,!?\"']", " ", string) #save the smileys ;-)
		words=string.split(" ")
		return words
	def cleanup(self):
		pass



class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
	
	def start(self):
		self.logger = self.bot.logging.getLogger("core.kiMod")
		self.channels=[]
		self.wordpairsFile=self.bot.getPathConfig("wordpairsFile", datadir, "wordpairs.txt")#XXX: this needs to be utf-8 encoded
		self.wordpairs=functions.loadProperties(self.wordpairsFile)

		module=self.bot.getConfig("module", "megahal", "kiMod", self.bot.network)
		self.logger.debug("kiMod: using module "+module+",cite="+str(CITE)+",megahal="+str(MEGAHAL)+",niall="+str(NIALL))
		if module=="cite":
			if CITE:
				try:
					self.responder=citeResponder(self.bot)
					self.logger.debug("kiMod: using cite module")
				except "boterror":
					self.logger.error("Error connecting the cite-DB.")
					self.responder=responder() #null responder
					#Fallback
					if MEGAHAL:
						self.logger.warning("kiMod: Using Megahal instead")
						self.responder=megahalResponder(bot)
			else:
				self.logger.error("Cannot use citeDB. Module MySQLdb not availible.")
				if MEGAHAL:
					self.logger.warning("Using Megahal instead")
					self.responder=megahalResponder(self.bot)
				else:
					self.responder=responder() #null responder
		elif module=="megahal":
			if MEGAHAL:
				self.responder=megahalResponder(self.bot)
			else:
				self.logger.error("Cannot use megahal. Module mh_python not availible.")
				self.responder=responder() #null responder
				#Fallback
				if CITE:
					self.logger.warning("Trying citeDB instead.")
					try:
						self.responder=citeResponder(self.bot)
					except "boterror":
						self.logger.error("Error connecting the cite-DB.")
		elif module=="niall":
			if NIALL:
				self.responder=niallResponder()
			else:
				self.responder=responder()
				self.logger.error("Cannot use niall.")
		else:
			self.logger.error("No responder for module %s!"%module)
		atexit.register(self.responder.cleanup)

	def joined(self, channel):
		self.channels.append(channel)
	def msg(self, user, channel, msg):
		user=user.split("!")[0]
		if user == self.bot.nickname:
			return
		if not channel in self.channels: 
			return
		if msg[0]=="!":
			return
			

		reply=""
		private=0

		#bot answers random messages
		number=random.randint(1,1000)
		chance=int(float(self.bot.getConfig("randomPercent", "0", "kiMod", self.bot.network, channel))*10)
		israndom=0
		if number < chance:
			israndom=1
			
		if self.lnickname==string.lower(channel):
			private=1
			reply=self.responder.reply(msg)
		#elif string.lower(msg[0:len(self.bot.nickname)])==string.lower(self.bot.nickname) or number<chance:
		elif (self.lnickname in string.lower(msg)) or israndom:
			if string.lower(msg[:len(self.lnickname)])==self.lnickname:
				msg=msg[len(self.lnickname)+1:] #+1 for the following ":", " " or ","
			if len(msg) and msg[0]==" ": 
				msg=msg[1:]
			reply=self.responder.reply(msg)
		else:
			#TODO: match with nicklist
			if not re.match("^(:|;|http)", msg):
				msg=re.sub("^[^ ]*?[:,;]", "", msg)
				#msg=re.sub("^[a-zA-Z]*?[:;,]", "", msg)
			self.responder.learn(msg)
		if reply!="":
			#reply=re.sub(" "+self.bot.nickname, " "+user, reply) #more secure to match only the name
			reply=re.sub(self.lnickname, user, str(reply), re.I) 
			for key in self.wordpairs.keys():
				reply=re.sub(key, self.wordpairs[key], reply, re.I)
			
			reply=re.sub("Http", "http", reply, re.I) #fix for nice urls

			if reply==string.upper(reply): #no UPPERCASE only Posts
				reply=string.lower(reply)
			delay=len(reply)*0.3*float(self.bot.getConfig("wait", "2", "kiMod", self.bot.network, channel)) #a normal user does not type that fast
			if private:
				number=random.randint(1,1000)
				chance=int(self.bot.getConfig("answerQueryPercent", "70", "kiMod", self.bot.network))*10
				if number < chance:
					#self.bot.sendmsg(user, reply, "UTF-8")
					self.bot.scheduler.callLater(delay, self.bot.sendmsg, user, reply, "UTF-8")
			else:
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

