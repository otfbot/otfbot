#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import string, re, random, time, functions

MEGAHAL=1
CITE=1
try:
	import mh_python
except ImportError:
	MEGAHAL=0
try:
	import MySQLdb
except ImportError:
	CITE=0

def default_settings():
	settings={};
	settings['kiMod_module']='megahal'
	
	settings['kiMod_mysqlHost']=''
	settings['kiMod_mysqlUser']=''
	settings['kiMod_mysqlPasswd']=''
	settings['kiMod_mysqlDB']='chatbot'
	settings['kiMod_keywordsTable']='keywords'
	settings['kiMod_stringsTable']='strings'
	
	settings['kiMod_wordpairsFile']='wordpairs.txt'
	settings['kiMod_randomPercent']='0'
	settings['kiMod_answerPercent']='50'
	settings['kiMod_answerQueryPercent']='70'
	settings['kiMode_maxStrings']='1000'
	return settings
		
class responder:
	def __init__(self):
		pass
	def learn(self, string):
		pass
	def reply(self, msg):
		return ""
	def cleanup(self):
		pass

class megahalResponder(responder):
	def __init__(self, bot):
		mh_python.initbrain()
		self.bot=bot
	def learn(self, msg):
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
		mh_python.cleanup()

class citeResponder(responder):
	def __init__(self, bot):
		self.host=bot.getConfig("kiMod_mysqlHost", "")
		self.user=bot.getConfig("kiMod_mysqlUser", "")
		self.passwd=bot.getConfig("kiMod_mysqlPasswd", "")
		self.database=bot.getConfig("kiMod_mysqlDB", "chatbot")
		self.keywordsTable=bot.getConfig("kiMod_keywordsTable", "keywords")
		self.stringsTable=bot.getConfig("kiMod_stringsTable", "strings")
		self.maxStrings=int(bot.getConfig("kiMod_maxStrings", "1000"))
		
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
			self.cursor.execute("CREATE TABLE "+self.keywordsTable+"(keyword TEXT, stringid INT);");
			self.logger.info("created keywords table:"+self.keywordsTable)
		if not self.stringsTable in tables:
			self.cursor.execute("CREATE TABLE "+self.stringsTable+"(id INT AUTO_INCREMENT, string TEXT, PRIMARY KEY(id));");
			self.logger.info("created strings table:"+self.stringsTable)

	def learn(self, string):
		cursor=self.cursor;
		words=self.getwords(string)
		self.cursor.execute("SELECT id FROM "+self.stringsTable+" WHERE string = '"+string+"';")
		if len(words) >1 and not len(self.cursor.fetchall()): #Do not learn single word / do not leran something twice
			self.cursor.execute("INSERT INTO "+self.stringsTable+" (string) VALUES (\""+re.sub("\"", "\\\"", string)+"\");")
			self.cursor.execute("SELECT LAST_INSERT_ID();")
			id=(self.cursor.fetchall())[0][0];
			if id>self.maxStrings:
				self.cursor.execute("DELETE FROM "+self.stringsTable+" WHERE id < "+str(id-self.maxStrings));
			for word in words:
				if word!="":
					self.cursor.execute("INSERT INTO "+self.keywordsTable+" VALUES (\""+word+"\","+str(id)+");")
				if id>self.maxStrings:
					self.cursor.execute("DELETE FROM "+self.keywordsTable+" WHERE stringid < "+str(id-self.maxStrings));

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
			self.cursor.execute("SELECT stringid FROM "+self.keywordsTable+" WHERE keyword LIKE '%"+topword+"%';")
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
			self.cursor.execute("SELECT string FROM "+self.stringsTable+" WHERE id='"+str(id)+"';")
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



class chatMod:
	def __init__(self, bot):
		self.bot=bot
		self.logger = bot.logging.getLogger("core.kiMod")
		self.channels=[]
		self.wordpairsFile=bot.getConfig("kiMod_wordpairsFile", "wordpairs.txt")#XXX: this needs to be utf-8 encoded
		self.wordpairs=functions.loadProperties(self.wordpairsFile)

		module=bot.getConfig("kiMod_module", "megahal")
		self.lnickname=string.lower(bot.nickname)
		if module=="cite":
			if CITE:
				try:
					self.responder=citeResponder(bot)
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
					self.responder=megahalResponder(bot)
				else:
					self.responder=responder() #null responder
		elif module=="megahal":
			if MEGAHAL:
				self.responder=megahalResponder(bot)
			else:
				self.logger.error("Cannot use megahal. Module mh_python not availible.")
				self.responder=responder() #null responder
				#Fallback
				if CITE:
					self.logger.warning("Trying citeDB instead.")
					try:
						self.responder=citeResponder(bot)
					except "boterror":
						self.logger.error("Error connecting the cite-DB.")

	def joined(self, channel):
		self.channels.append(channel)
	def msg(self, user, channel, msg):
		user=user.split("!")[0]
		if user == self.bot.nickname:
			return
		#if not channel in self.channels: 
		#	return
		if msg[0]=="!":
			return
			

		reply=""
		private=0

		#bot answers random messages
		number=random.randint(1,1000)
		chance=int(float(self.bot.getConfig("kiMod_randomPercent", "0"))*10)
		israndom=0
		if number < chance:
			israndom=1
			
		if self.lnickname==string.lower(channel):
			private=1
			reply=self.responder.reply(msg)
		#elif straing.lower(msg[0:len(self.bot.nickname)])==string.lower(self.bot.nickname) or number<chance:
		elif self.lnickname in string.lower(msg) or israndom:
			if string.lower(msg[:len(self.bot.nickname)])==self.lnickname:
				msg=msg[len(self.bot.nickname)+1:] #+1 for the following ":", " " or ","
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
			reply=re.sub(self.bot.nickname, user, reply, re.I) 
			for key in self.wordpairs.keys():
				reply=re.sub(key, self.wordpairs[key], reply, re.I)
			
			reply=re.sub("Http", "http", reply, re.I) #fix for nice urls
			#time.sleep(len(reply)*0.3*float(self.bot.getConfig("kiMod_wait", "2")))

			if reply==string.upper(reply): #no UPPERCASE only Posts
				reply=string.lower(reply)
			if private:
				number=random.randint(1,1000)
				chance=int(self.bot.getConfig("kiMod_answerQueryPercent", "70"))*10
				if number < chance:
					self.bot.sendmsg(user, reply, "UTF-8")
			else:
				number=random.randint(1,1000)
				chance=int(self.bot.getConfig("kiMod_answerPercent", "50"))*10
				if israndom or number < chance: #apply answerPercent only on answers(check for israndom)
					self.bot.sendmsg(channel, user+": "+reply, "UTF-8")

	def connectionLost(self, reason):
		self.responder.cleanup()

	def stop(self):
		self.responder.cleanup()

