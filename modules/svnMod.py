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
# (c) 2008 by Thomas Wiegart
#

import pysvn
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self,bot):
		"""
		Config has to look like this:
		samplenetwork:
		  svnMod.svn:
		    samplesvn:
		       channels: '#yourchann'
		       checkinterval: 30 (in Minutes!)
		       url: svn://url.to.your/svn
		"""
		self.bot = bot
		self.callIds = {}
		config = self.bot.getConfig("svnMod.svn","","",self.bot.network)
		for i in config:
			self.bot.scheduler.callLater(60, self.svncheck, config[i]['url'],config[i]['checkinterval'],config[i]['channels'],i)
		
	def svncheck(self,url,interval,channels,name):
		try:
			channels = channels.split(",")
		except:
			channels = [channels]
		lastrevision = 0
		data = pysvn.Client().log(url,limit=1)[0].data
		rev = data['revision'].number
		if rev != lastrevision:
			lastrevision = rev
			for channel in channels:
				self.bot.msg(channel,chr(2) + "[" + name + "]" + chr(2) + " Revision " + str(rev) + " by " + data['author'].encode() + ": " + data['message'].encode().replace("\n","").replace("\r",""))
				#for line in data['message'].encode().split("\n"):
				#	if line.encode() != "":
				#		self.bot.msg(channel,chr(2) + "[" + name + "]" + chr(2) + " " + line.encode())
		self.bot.scheduler.callLater(int(interval)*60, self.svncheck, url,interval,channels,name)
