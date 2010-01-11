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
# (c) 2009 by Thomas Wiegart
#

import pickle,time,os
from otfbot.lib import chatMod

class Plugin(chatMod.chatMod):
	def __init__(self, bot):
		self.bot = bot
		try:
			os.mkdir(datadir)
		except OSError:
			pass
		try:
			f = file(datadir + "/users", "rb")
			self.userdata = pickle.load(f)
			f.close()
		except IOError:
			self.userdata = [{}]
		self.bot.root.getServiceNamed('scheduler').callLater(60, self.save_data) #TODO: call this only on exit
		
	def joined(self,channel):
		try:
			self.userdata[0][channel]
		except KeyError:
			self.userdata[0][channel] = {}
	
	def msg(self, user, channel, msg):
		if channel[0] == "#":
			self.userdata[0][channel][user.split("!")[0].lower()] = {'msg':msg, 'time':time.time()}
	
	def command(self, user, channel, command, options):
		self.logger.info(channel)
		if command == "seen":
			try:
				zeit = self.userdata[0][channel][options.lower()]['time']
				msg = self.userdata[0][channel][options.lower()]['msg']
				self.bot.sendmsg(channel,"user " + options + " was last seen on " + str(time.strftime("%a, %d %b %Y %H:%M:%S",time.localtime(zeit))) + " saying '" + msg + "'.")
			except:
				self.bot.sendmsg(channel,"user " + options + " is unknown")
	
	def stop(self):
		self.save_data()
	
	def save_data(self):
		f = file(datadir + "/users", "wb")
		pickle.dump(self.userdata, f)
		f.close()
		self.bot.root.getServiceNamed('scheduler').callLater(60, self.save_data)
