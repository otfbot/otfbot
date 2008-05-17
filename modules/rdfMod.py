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
# (c) 2005-2007 by Alexander Schier
#

import chatMod, rdfParser
import time


class chatMod(chatMod.chatMod):
	def __init__(self, bot):

		self.bot = bot
		self.end = False
		self.logger = self.bot.logging.getLogger("rdfMod")
		
		self.rdfHeadlines={} #map url -> [(url, headline), ...]
		self.readUrls={} #map channel->[url, url, ...]
		self.rdfLastLoaded={} #map url->timestamp
		self.callIDs={} #map url -> callLater ID

	def addSource(self, url, channel, minWait, maxWait, factor, postMax):
		""" add a feed
			@param url: the url of the feed
			@param minWait: minimal time between updates
			@param maxWait: maximum time between updates
			@param factor: the factor to increase update delay if no new news were found
			@param postMax: maximum new items to post on update
		"""
		if(minWait > maxWait):
			self.logger.error(url+" maxWait is bigger than minWait. Skipping feed.")
			return
		if factor==0:
			self.logger.error(url+" has a waitFactor of 0. Skipping feed.")
			return
		self.callIDs[url]=self.bot.scheduler.callLater(minWait*60, self.postNewsLoop, channel, url, minWait, minWait, maxWait, factor, postMax)

		self.readUrls[channel]=[]
		self.rdfLastLoaded[url]=0
		self.rdfHeadlines[url]=[]

		self.logger.debug(url+" (update every "+str(minWait)+" - "+str(maxWait)+" minutes), waitFactor "+str(factor)+".")

	def loadSource(self, num, channel):
		rdfUrl=self.bot.getConfig("rdf"+str(num)+".url", "", "rdfMod", self.bot.network, channel)

		rdfMinWait=float(self.bot.getConfig("rdf"+str(num)+".minWait", "5.0", "rdfMod", self.bot.network, channel))
		rdfMaxWait=float(self.bot.getConfig("rdf"+str(num)+".maxWait", "60.0", "rdfMod", self.bot.network, channel))
		rdfWaitFactor=float(self.bot.getConfig("rdf"+str(num)+".waitFactor", "1.5", "rdfMod", self.bot.network, channel))
		rdfPostMax=int(self.bot.getConfig("rdf"+str(num)+".postMax", "3", "rdfMod", self.bot.network, channel))

		self.addSource(rdfUrl, channel, rdfMinWait, rdfMaxWait, rdfWaitFactor, rdfPostMax)

	def joined(self, channel):
		numRdfs=int(self.bot.getConfig("numRdfs", 0, "rdfMod", self.bot.network, channel))
		if numRdfs > 0:
			self.logger.debug("Found "+str(numRdfs)+" RDF-Urls:")
			for i in xrange(1,numRdfs+1):
				self.loadSource(i, channel)
				
	def getWaitTime(self, curWait, minWait, maxWait, factor, hadNew):
		"""
			@type curWait: float
			@param curWait: current wait time
			@type minWait: float
			@param minWait: minimum wait time
			@type maxWait: float
			@param curWait: maximum wait time
			@type maxWait: float
			@param factor: factor (>=1) to increase the delay if no news were found
			@type hadNew: bool
			@param hadNew: set to true, if new news were loaded
		"""
		newWait=1
		if hadNew:
			if curWait != minWait:
				self.logger.debug("new wait-time: "+str(minWait)+ " (minimum)")
			newWait=minWait
		else:
			newWait=curWait*factor
			if newWait > maxWait:
				newWait=manWait
				self.logger.debug("new wait-time: "+str(newWait)+" (maximum)")
			else:
				self.logger.debug("new wait-time: "+str(newWait))
		return newWait
		
	def loadNews(self, url):
		#TO BE REMOVED: this is not needed with one schedulejob per source
		#self.logger.debug("RDF-Check for "+channel+" and url "+url)
		#if self.rdfLastLoaded[url] <= int(time.time()-(curWait*60)): #last load older than the wait of this rdf for this channel

		self.rdfLastLoaded[url]=int(time.time()) #to be removed, too?
		self.logger.debug("loading new Headlines")
		rdf=rdfParser.parse(url)
		self.rdfHeadlines[url]=[]
		for key in rdf['links']:
			self.rdfHeadlines[url].append((key, rdf['elements'][key]))
	def postNews(self, channel, url, rdfPostMax):
		had_new=False #new urls? needed for wait-time modification
		numPostUrls=rdfPostMax
		for (url, headline) in self.rdfHeadlines[url]:
			if not url in self.readUrls[channel]:
				if numPostUrls > 0:
					numPostUrls-=1
					self.bot.sendmsg(channel.encode("UTF-8"), (url+" - "+headline).encode("UTF-8"), "UTF-8");
					#self.readUrls[channel].append(url) #with this line, all urls will be posted, but the queue may get longer and longer
				self.readUrls[channel].append(url) #with this line, we will throw away all new urls, which are more than rdfPostMax
				had_new=True
		self.logger.debug("posted "+str(rdfPostMax-numPostUrls)+" new URLs")
		return had_new
	def postNewsLoop(self, channel, url, curWait=5, minWait=1, maxWait=60, factor=1.5, rdfPostMax=3):
		"""load News if needed and Post them to a channel"""
		if self.end:
			return


		self.loadNews(url)
		had_new=self.postNews(channel, url, rdfPostMax)	

		newWait=self.getWaitTime(curWait, minWait, maxWait, factor, had_new)
		self.callIDs[url]=self.bot.scheduler.callLater(newWait*60, self.postNewsLoop, channel, url, curWait, minWait, maxWait, factor, rdfPostMax) #recurse


	def connectionLost(self, reason):
		self.stop()

	def stop(self):
		self.logger.info("Got Stop Signal.")
		self.end=1

	def connectionMade(self):
		"""made connection to server"""
		bot=self.bot

	def command(self, user, channel, command, options):
		if command=="refresh":
			if self.bot.auth(user) >= 10:
				if options!="":
					num=int(options)
					if num!=0:
						rdfUrl=self.bot.getConfig("rdf"+str(num)+".url", "", "rdfMod", self.bot.network, channel)
						self.callIDs[rdfUrl].cancel()
						self.loadNews(rdfUrl)
						self.postNews(channel, rdfUrl, int(self.bot.getConfig("rdf"+str(num)+".postMax", "", "rdfMod", self.bot.network, channel) ))
						self.loadSource(num, channel)
			else:
				self.logger.debug(user+" has no permission to enforce rdf refresh")
