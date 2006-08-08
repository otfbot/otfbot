import threading, time
import rdfParser

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

def default_settings():
	settings={};
	settings['rdfMod_wait']='5'
	settings['rdfMod_numRdfs']='0'
	settings['rdfMod_rdf1']='http://localhost/example.rss'
	return settings
		
class chatMod(threading.Thread):
	def __init__(self, bot):
		threading.Thread.__init__(self)

		self.end = 0
		self.read = {}
		self.bot = bot
		self.channel = ""

		self.wait=60 * float(bot.getConfig("rdfMod_wait", "5"))
		self.rdfUrls=[]
		numRdfs=int(bot.getConfig("rdfMod_numRdfs", "0"))
		if numRdfs < 1: #no rdfs or invalid Numer(negative)
			self.end=1 #do not run this Mod
			print "rdfMod: no Rdfs"
		#import the rdfUrls
		for num in range(0, numRdfs):
			self.rdfUrls.append(bot.getConfig("rdfMod_rdf"+str(num+1)))

		for rdfUrl in self.rdfUrls: #create emtpy lists
			self.read[rdfUrl] = {}

		for rdfUrl in self.rdfUrls:
			#print "rdfMod: initial load of", rdfUrl #DEBUG
			rdf = rdfParser.parse(rdfUrl)
			#mark all urls as read on startup
			#this prevents the bot from printing the newest 3 headlines on join.
			#if you want to get the 3 headlines, disable this, 
			#and put the sleep function ind run() at end of the loop.
			for key in rdf['links']:
				if not self.read[rdfUrl].has_key(key):#sort unread
					self.read[rdfUrl][key] = 1 #but read for all later jobs
				
	def run(self):
		while(not self.end):
			#splits the waittime, to support stop()
			#can be at end, too
			i=0
			while(not self.end and i<self.wait):
				time.sleep(10)
				i+=10
				
			if not self.end:
				for rdfUrl in self.rdfUrls:
					self.postNews(rdfUrl)
		print "rdfMod: successfully stopped."

	def postNews(self, rdfUrl):
		unread =[]
		#print "rdfMod: checking of", rdfUrl #DEBUG
		rdf = rdfParser.parse(rdfUrl)
		#print rdf
		for key in rdf['links']:
			if not self.read[rdfUrl].has_key(key):#sort unread
				unread.append(key) #unread for us
				self.read[rdfUrl][key] = 1 #but read for all later jobs
		
		if len(unread) > 3: #if there are more than three new ones, we only want the newest
			unread = unread[:3] 
		#print "rdfMod:", str(len(unread)), "new items" #DEBUG
		for url in unread:
			self.bot.sendmsg(self.channel, (url+" - "+rdf['elements'][url]).encode("UTF-8"), "UTF-8");
		unread = []#mark all as read
		i = 0

	def joined(self, channel):
		if self.channel == "": #only the first channel
			self.channel = channel
	def msg(self, user, channel, msg):
		#if channel == self.bot.nickname: 
		if self.bot.auth(user):
			if msg == "!stop" or msg == "!rdfstop": #in query
				self.stop()
	def connectionLost(self, reason):
		self.stop()

	def stop(self):
		print "rdfMod: Got Stop Signal."
		self.end=1

