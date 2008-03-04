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
# (c) 2007 by Alexander Schier
#

import chatMod
import os.path,pickle

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.karma={}
		self.karmapath=self.bot.getPathConfig("file", datadir, "karma.dat", "karmaMod", self.bot.network)
		if os.path.exists(self.karmapath):
			karmafile=open(self.karmapath, "r")
			self.karma=pickle.load(karmafile)
			karmafile.close()
		self.verbose=self.bot.getBoolConfig("karmaMod.verbose", "true")
		self.freestyle=self.bot.getBoolConfig("karmaMod.freestyle", "true")

	def command(self, user, channel, command, options):
		up=False
		what=None
		reason=None

		#return on why/who karma up/down
		num_reasons=5
		num_user=5

		tmp=options.split("#",1)
		options=tmp[0].strip()
		if len(tmp)==2:
			reason=tmp[1]

		if command == "karma":
			if options == "":
				self.bot.sendmsg(channel, "Nutzen: !karma name++ oder !karma name--")
				return
			else:
				if options[-2:]=="++":
					up=True
					what=options[:-2]
				elif options[-2:]=="--":
					up=False
					what=options[:-2]
				else:
					self.tell_karma(options, channel)
					return
			self.do_karma(what, up, reason, user)
			if self.verbose:
				self.tell_karma(what, channel)
		elif command == "why-karmaup" or command == "wku":
			options.strip()
			reasons=""
			if options in self.karma.keys():
				num=min(num_reasons, len(self.karma[options][3]))
				while num > 0:
					num-=1
					reasons+=" .. "+self.karma[options][3][-num]
				reasons=reasons[4:]
				self.bot.sendmsg(channel, reasons)
		elif command == "why-karmadown" or command == "wkd":
			options.strip()
			reasons=""
			if options in self.karma.keys():
				num=min(num_reasons, len(self.karma[options][4]))
				while num > 0:
					num-=1
					reasons+=" .. "+self.karma[options][4][-num]
				reasons=reasons[4:]
				self.bot.sendmsg(channel, reasons)
		elif self.freestyle:
			if options[-2:]=="++":
				up=True
				what=command+" "+options[:-2]
			elif options[-2:]=="--":
				up=False
				what=command+" "+options[:-2]
			elif command[-2:]=="++":
				up=True
				what=command[:-2]
			elif command[-2:]=="--":
				up=False
				what=command[:-2]
			self.do_karma(what, up, reason, user)
			if self.verbose:
				self.tell_karma(what, channel)

	def tell_karma(self, what, channel):
		self.bot.sendmsg(channel, "Karma: "+what+": "+str(self.get_karma(what))) 
	def get_karma(self, what):
		if not what in self.karma.keys():
			self.karma[what]=[0,{},{},[],[]] #same as below!
		return self.karma[what][0]
	def do_karma(self, what, up, reason, user):
		user=user.split("!")[0]
		if not what in self.karma.keys():
			self.karma[what]=[0,{},{},[],[]] #score, who-up, who-down, why-up, why-down
		if up:
			self.karma[what][0]=int(self.karma[what][0])+1
			if not user in self.karma[what][1].keys():
				self.karma[what][1][user]=1
			else:
				self.karma[what][1][user]+=1
			if reason:
				self.karma[what][3].append(str(reason))
		else:
			self.karma[what][0]=int(self.karma[what][0])-1
			if not user in self.karma[what][2].keys():
				self.karma[what][2][user]=-1
			else:
				self.karma[what][2][user]-=1
			if reason:
				self.karma[what][4].append(str(reason))
	def karma_up(self, what, reason=None):
		return self.do_karma(what, True, reason)
	def karma_down(self, what, reason=None):
		return self.do_karma(what, False, reason)
	def connectionLost(self, reason):
		karmafile=open(self.karmapath, "w")
		pickle.dump(self.karma, karmafile)
		karmafile.close()

