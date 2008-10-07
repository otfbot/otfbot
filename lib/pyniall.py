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

import random, yaml
class pyNiall:
	def __init__(self):
		self.words=[">"] #[word1, word2, word3, ...]
		self.next={0: set()} #id: [next-id1, next-id2, ...]
		self.prob={} #(id, next-id): times seen (probabilty = this / total)

		#these can be calculated from the vars above
		self.prev={-1: set()} #id: [prev-id1, prev-id2, ...]
		self.rank={} #{id: totalrank}

	def _addRelation(self, word1, word2):
		"""
		#adds "hello world" and "hello user" without endrelation
		>>> n=pyNiall()
		>>> n._addRelation(">", "hello")
		>>> n._addRelation("hello", "world")
		>>> n._addRelation(">", "hello")
		>>> n._addRelation("hello", "user")
		>>> n.words
		['>', 'hello', 'world', 'user']
		>>> n.next
		{0: set([1]), 1: set([2, 3]), 2: set([]), 3: set([])}
		>>> n.prev
		{1: set([0]), 2: set([1]), 3: set([1]), -1: set([])}
		>>> n.prob
		{(0, 1): 2, (1, 2): 1, (1, 3): 1}
		>>> n.rank
		{1: 2, 2: 1, 3: 1}
		"""
		if not word1 in self.words:
			print "Error in Database: word1 not in words"
			return
		index1=self.words.index(word1)

		#create word if needed
		if not word2 in self.words:
			self.words.append(word2) #create word (and index)
			index2=self.words.index(word2)
			self.next[index2]=set() #create empty association set
		else:
			index2=self.words.index(word2) #get index

		#add next relation
		if not index2 in self.next[index1]: #not associated, yet
			self.next[index1].add(index2) #add
			self.prob[(index1, index2)]=1 #first time
		else:
			self.prob[(index1, index2)]+=1

		#add previous relation
		if not index2 in self.prev.keys():
			self.prev[index2]=set([index1])
		else:
			self.prev[index2].add(index1)

		#totalrank of word
		if not index2 in self.rank.keys():
			self.rank[index2]=1
		else:
			self.rank[index2]+=1

	def _addEndRelation(self, word):
		"""
		>>> n=pyNiall()
		>>> n._addRelation(">", "hello")
		>>> n._addRelation("hello", "world")
		>>> n._addEndRelation("world") #"hello world"

		>>> n._addRelation(">", "hello")
		>>> n._addEndRelation("hello") #"hello"
		>>> n.next
		{0: set([1]), 1: set([2, -1]), 2: set([-1])}
		>>> n.prev
		{1: set([0]), 2: set([1]), -1: set([1, 2])}
		>>> n.prob
		{(0, 1): 2, (1, 2): 1, (2, -1): 1, (1, -1): 1}
		>>> n.rank #the same as in _addRelation
		{1: 2, 2: 1}
		"""
		index=self.words.index(word)

		#calculate next
		if not -1 in self.next[index]:
			self.next[index].add(-1)
			self.prob[(index, -1)]=1
		else:
			self.prob[(index, -1)]+=1

		#calculate prev
		if not index in self.prev[-1]:
			self.prev[-1].add(index)

	def _rankWord(self, word):
		"""
		rank a word by length and probability
		"""
		rank=0
		length=len(word)
		rank=self.rank[self.words.index(word)]
		return rank+length*0.7

	def _createRandomSentence(self, index, sentence, forward=True):
		candidates=[]
		if forward:
			for index2 in self.next[index]:
				candidates+=[index2]*self.prob[(index, index2)]
		else:
			for index2 in self.prev[index]:
				candidates+=[index2]*self.prob[(index2, index)]
		newindex=random.choice(candidates)
		if newindex==0: #sentence start
			return sentence.strip()
		if newindex==-1: #sentence end
			#return sentence
			return (sentence+" "+self.words[index]).strip()
		if forward:
			if index==0: #no ">" included
				return self._createRandomSentence(newindex, "")
			return self._createRandomSentence(newindex, sentence+" "+self.words[index])
		else:
			if index==-1: #no sentence end included
				return self._createRandomSentence(newindex, "", False)
			#attention: here we use index2, so the current word is NOT part of the sentence,
			#while the current word IS part of the sentence when scanning forward.
			#so we can use forward+" "+backward to build a sentence
			return self._createRandomSentence(newindex, self.words[newindex]+" "+sentence, False).strip()
	
	def _createReply(self, msg):
		words=msg.strip().split(" ")
		bestword=None
		bestwordrank=0
		for word in words:
			#no fresh learned words as context! (else the bot just echos)
			if not self.rank[self.words.index(word)]>1:
				continue
			rank=self._rankWord(word)
			if rank>bestwordrank:
				bestwordrank=rank
				bestword=word
		if bestword:
			index=self.words.index(bestword)
			return self._createRandomSentence(index, "", False)+" "+self._createRandomSentence(index, "")
		else:
			return _createRandomSentence(0, "")


	def learn(self, msg):
		words=msg.lower().split(" ")
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
		if len(self.words)<200: #if we reply with context to early, the bot just echos
			return self._createRandomSentence(0, "")
		else:
			return self._createReply(msg.lower()).strip()

	def import_brain(self, data):
		tmp=yaml.load_all(data)
		self.words=tmp.next()
		self.next=tmp.next()
		self.prob=tmp.next()

		#calculate the optional fields
		for id in self.next.keys():
			for id2 in self.next[id]:
				if id2 in self.prev:
					self.prev[id2].add(id)
				else:
					self.prev[id2]=set([id])
		for (a,b) in self.prob.keys():
			if b!=-1 and b in self.rank:
				self.rank[b]+=self.prob[(a,b)]
			else:
				self.rank[b]=self.prob[(a,b)]

	def export_brain(self):
		return yaml.dump_all([self.words, self.next, self.prob])

if __name__ == "__main__":
	import doctest
	doctest.testmod()
