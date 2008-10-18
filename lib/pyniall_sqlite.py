# -*- coding: utf-8 -*-
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  0211
#
# (c) 2008 by Alexander Schier

import random, sqlite, os
class pyNiall:
	def __init__(self, dbname):
		if not os.path.exists(dbname):
			init_db(dbname)
		self.db=sqlite.connect(dbname)
		self.cur=self.db.cursor()

	def _addRelation(self, word1, word2):
		self.cur.execute("SELECT id FROM words WHERE word=%s", [word1])
		index1=self.cur.fetchall()[0][0]

		#create word if needed
		self.cur.execute("SELECT id FROM words WHERE word=%s", [word2])
		result=self.cur.fetchall()
		if len(result):
			index2=result[0][0]
		else:
			self.cur.execute("INSERT INTO words VALUES (null, %s)", [word2])
			index2=self.cur.lastrowid

		#add next relation
		self.cur.execute("SELECT ranking FROM relations WHERE word1_id=%s AND word2_id=%s", (index1, index2))
		result=self.cur.fetchall()
		if not len(result):
			self.cur.execute("INSERT INTO relations VALUES (%s, %s, 1)", (index1, index2))
		else:
			ranking=result[0][0]
			self.cur.execute("UPDATE relations SET ranking=%s WHERE word1_id=%s AND word2_id=%s", (ranking+1, index1, index2))

	def _addEndRelation(self, word):
		self.cur.execute("SELECT id FROM words WHERE word=%s", [word])
		index=self.cur.fetchall()[0][0]

		#calculate next
		self.cur.execute("SELECT ranking FROM relations WHERE word1_id=%s AND word2_id=-1", [index])
		result=self.cur.fetchall()
		if not len(result):
			self.cur.execute("INSERT INTO relations VALUES (%s, -1, 1)", [index])
		else:
			self.cur.execute("UPDATE relations SET ranking=%s WHERE word1_id=%s and word2_id=-1", (result[0][0], index))

	def _rankWord(self, word):
		"""
		rank a word by length and probability
		"""
		rank=0
		length=len(word)
		return self._getWordRank(word)+length*0.7

	def _getWordRank(self, word):
		self.cur.execute("SELECT id FROM words WHERE word=%s", word)
		id=self.cur.fetchall()[0][0]
		self.cur.execute("SELECT ranking FROM relations WHERE word2_id=%s", id)
		result=self.cur.fetchall()
		rank=0
		for row in result:
			rank+=row[0]
		return rank

	def _createRandomSentence(self, index, sentence, forward=True):
		candidates=[]
		if forward:
			self.cur.execute("SELECT word2_id, ranking FROM relations WHERE word1_id=%s", [index])
		else:
			self.cur.execute("SELECT word1_id, ranking FROM relations WHERE word2_id=%s", [index])
		result=self.cur.fetchall()
		for row in result:
			candidates+=[row[0]]*row[1]

		newindex=random.choice(candidates)
		if newindex==0: #sentence start
			return sentence.strip()
		if newindex==-1: #sentence end
			#return sentence
			self.cur.execute("SELECT word FROM words WHERE id=%s", index)
			word=self.cur.fetchall()[0][0]
			return (sentence+" "+word).strip()
		if forward:
			if index==0: #no ">" included
				return self._createRandomSentence(newindex, "")
			self.cur.execute("SELECT word FROM words WHERE id=%s", index)
			word=self.cur.fetchall()[0][0]
			return self._createRandomSentence(newindex, sentence+" "+word)
		else:
			if index==-1: #no sentence end included
				return self._createRandomSentence(newindex, "", False)
			#attention: here we use index2, so the current word is NOT part of the sentence,
			#while the current word IS part of the sentence when scanning forward.
			#so we can use forward+" "+backward to build a sentence
			self.cur.execute("SELECT word FROM words WHERE id=%s", newindex)
			word=self.cur.fetchall()[0][0]
			return self._createRandomSentence(newindex, word+" "+sentence, False).strip()
	
	def _createReply(self, msg):
		words=msg.strip().split(" ")
		bestword=None
		bestwordrank=0
		for word in words:
			#no fresh learned words as context! (else the bot just echos)
			rank=self._getWordRank(word)
			if not rank>1:
				continue
			rank=self._rankWord(word)
			if rank>bestwordrank:
				bestwordrank=rank
				bestword=word
		if bestword:
			self.cur.execute("SELECT id FROM words WHERE word=%s", [bestword])
			index=self.cur.fetchall()[0][0]
			return self._createRandomSentence(index, "", False)+" "+self._createRandomSentence(index, "")
		else:
			return self._createRandomSentence(0, "")


	def learn(self, msg):
		words=msg.split(" ")
		oldword=">"
		for word in words:
			word=word.strip()
			if len(word):
				self._addRelation(oldword, word)
				oldword=word
		if oldword != ">":
			self._addEndRelation(oldword)

	def reply(self, msg):
		self.learn(msg)
		return self._createReply(msg).strip()
	def cleanup(self):
		self.db.commit()
		#self.db.close()

def init_db(name):
	db=sqlite.connect(name)
	cur=db.cursor()
	cur.execute('CREATE TABLE words (id INTEGER PRIMARY KEY, word VARCHAR(255))')
	cur.execute('CREATE TABLE relations (word1_id INTEGER, word2_id INTEGER, ranking INTEGER)')
	cur.execute('INSERT INTO words VALUES (0, ">")')
	cur.close()
	db.commit()
	db.close()

if __name__ == "__main__":
	import doctest
	doctest.testmod()
