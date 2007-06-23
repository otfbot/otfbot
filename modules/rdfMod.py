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

import threading, time
import chatMod, rdfParser


def default_settings():
	settings={};
	settings['rdfMod.wait']='5' #XXX: works only global at the moment
	settings['rdfMod.numRdfs']='0'
	settings['rdfMod.rdf1']='http://you/need/to/set/this/in/a/channel/not/global/example.rss'
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):

		self.end = 0
		self.read = {}
		self.bot = bot
		self.logger = self.bot.logging.getLogger("rdfMod")
		
		self.wait=60 * float(bot.getConfig("wait", "5", "rdfMod"))
		self.rdfUrls=[]
		self.rdfChannels={}
		self.bot.scheduler.callLater(10, self.run)
		self.sleeped=0

				
	def run(self):
		if self.sleeped>=self.wait:
			for rdfUrl in self.rdfUrls:
				self.postNews(rdfUrl)
				self.sleeped=0
		if not self.end:
			#splits the waittime, to support stop()
			self.sleeped+=10
			self.bot.scheduler.callLater(10, self.run)

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
		for channel in self.rdfChannels[rdfUrl]:
			for url in unread:
				self.bot.sendmsg(channel.encode("UTF-8"), (url+" - "+rdf['elements'][url]).encode("UTF-8"), "UTF-8");
		unread = []#mark all as read
		i = 0

	def connectionLost(self, reason):
		self.stop()

	def stop(self):
		self.logger.info("Got Stop Signal.")
		self.end=1

	def connectionMade(self):
		"""made connection to server"""
		bot=self.bot
		(general, networks, channels)=self.bot.hasConfig("numRdfs", "rdfMod")
		for (network, channel) in channels:
			numRdfs=int(bot.getConfig("numRdfs", 0, "rdfMod", network, channel))
			for num in range(0, numRdfs):
				rdfUrl=bot.getConfig("rdf"+str(num+1), "", "rdfMod", network, channel)
				if rdfUrl != "":
					#self.rdfChannels[rdfUrl]=(network, channel)
					if(network==self.bot.network):
						if not rdfUrl in self.rdfChannels.keys():
							self.rdfChannels[rdfUrl]=[channel]
						else:
							self.rdfChannels[rdfUrl].append(channel)
						if not rdfUrl in self.rdfUrls:
							self.rdfUrls.append(rdfUrl)
					

		for rdfUrl in self.rdfUrls: #create emtpy lists
			self.read[rdfUrl] = {}

		for rdfUrl in self.rdfUrls:
			#print "rdfMod: initial load of", rdfUrl #DEBUG
			rdf = rdfParser.parse(rdfUrl)
			#mark all urls as read on startup
			#this prevents the bot from printing the newest 3 headlines on join.
			#if you want to get the 3 headlines, disable this, 
			#and put the sleep function in run() at end of the loop.
			for key in rdf['links']:
				if not self.read[rdfUrl].has_key(key):#sort unread
					self.read[rdfUrl][key] = 1 #but read for all later jobs
