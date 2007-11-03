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


def default_settings():
	settings={};
	return settings
		
class chatMod(chatMod.chatMod):
	def __init__(self, bot):

		self.bot = bot
		self.end = False
		self.logger = self.bot.logging.getLogger("rdfMod")
		
		self.rdfHeadlines={} #map url -> [(url, headline), ...]
		self.readUrls={} #map channel->[url, url, ...]
		self.rdfLastLoaded={} #map url->timestamp

	def joined(self, channel):
		numRdfs=int(self.bot.getConfig("numRdfs", 0, "rdfMod", self.bot.network, channel))
		if numRdfs > 0:
			self.logger.debug("Found "+str(numRdfs)+" RDF-Urls:")
			for i in xrange(1,numRdfs+1):
				rdfUrl=self.bot.getConfig("rdf"+str(i)+".url", "", "rdfMod", self.bot.network, channel)
				rdfWait=float(self.bot.getConfig("rdf"+str(i)+".wait", "5.0", "rdfMod", self.bot.network, channel))
				rdfPostMax=int(self.bot.getConfig("rdf"+str(i)+".postmax", "3", "rdfMod", self.bot.network, channel))
				self.bot.scheduler.callLater(rdfWait, self.postNews, channel, rdfUrl, rdfWait, rdfPostMax)

				self.readUrls[channel]=[]
				self.rdfLastLoaded[rdfUrl]=0
				self.rdfHeadlines[rdfUrl]=[]

				self.logger.debug(str(i)+": "+rdfUrl+" (update every "+str(rdfWait)+" minutes).")
				
	def postNews(self, channel, rdfUrl, rdfWait, rdfPostMax=3):
		"""load News if needed and Post them to a channel"""
		if self.end:
			return
		self.logger.debug("RDF-Check for "+channel+" and url "+rdfUrl)
		if self.rdfLastLoaded[rdfUrl] < int(time.time()-(rdfWait*60)): #last load older than the wait of this rdf for this channel
			self.logger.debug("loading new Headlines")
			rdf=rdfParser.parse(rdfUrl)
			self.rdfHeadlines[rdfUrl]=[]
			for key in rdf['links']:
				self.rdfHeadlines[rdfUrl].append((key, rdf['elements'][key]))
			self.rdfLastLoaded[rdfUrl]=int(time.time())

		
		#post urls
		numPostUrls=rdfPostMax
		for (url, headline) in self.rdfHeadlines[rdfUrl]:
			if not url in self.readUrls[channel]:
				if numPostUrls > 0:
					numPostUrls-=1
					self.bot.sendmsg(channel.encode("UTF-8"), (url+" - "+headline).encode("UTF-8"), "UTF-8");
					#self.readUrls[channel].append(url) #with this line, all urls will be posted, but the queue may get longer and longer
				self.readUrls[channel].append(url) #with this line, we will throw away all new urls, which are more than rdfPostMax
		self.logger.debug("posted "+str(rdfPostMax-numPostUrls)+" new URLs")

		self.bot.scheduler.callLater(rdfWait, self.postNews, channel, rdfUrl, rdfWait*60, rdfPostMax) #recurse


	def connectionLost(self, reason):
		self.stop()

	def stop(self):
		self.logger.info("Got Stop Signal.")
		self.end=1

	def connectionMade(self):
		"""made connection to server"""
		bot=self.bot
