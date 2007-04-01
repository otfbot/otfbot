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

import random, re, string
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.configshell=False
		self.configlevel=[]
	
	def configgetlevellist(self):
		if len(self.configlevel) == 0:
			return self.bot.getNetworks()
		elif len(self.configlevel) == 1:
			return self.bot.getChannels(self.configlevel[0])
		else:
			return self.bot.getSubOptions(self.configlevel)
	
	def msg(self, user, channel, msg):
		nick=user.split("!")[0]
		if self.bot.auth(user) > 7 and string.lower(channel)==string.lower(self.bot.nickname):
			if msg[0:6] == "config":
				self.configshell=True
				self.configlevel=[]
				self.bot.sendmsg(nick,"Entering configshell ...")
			elif self.configshell:
				if msg[0:2] == "ls":
					out=""
					lst=self.configgetlevellist()
					for i in range(1,len(lst)):
						out=out+str(i)+" "+lst[i-1]+" | "
					self.bot.sendmsg(nick,out.encode("utf-8"))
				elif msg[0:2] == "cd":
					if msg[3:5] == ".." and len(self.configlevel)>=0:
						self.configlevel.pop()
					else:
						num=int(msg[3:])
						if 0 < num and num < len(self.configgetlevellist())+1:
							self.configlevel.append(self.configgetlevellist()[num-1])
						else:
							self.bot.sendmsg(nick,"No such setting: "+str(num))
				elif msg[0:4] == "quit":
					self.configshell=False
					self.bot.sendmsg(nick,"Leaving configshell ...")
				elif msg[0:3] == "get":
					msg=msg[4:]
					msg=msg.split(" ")
					#self.logger.debug(msg)
					if len(msg) == 4:
						res=self.bot.getConfig(msg[0], "",msg[1],msg[2],msg[3])
					elif len(msg) == 3:
						res=self.bot.getConfig(msg[0], "", msg[1], msg[2])
					elif len(msg) == 2:
						res=self.bot.getConfig(msg[0], "", msg[1])
					elif len(msg) == 1:
						res=self.bot.getConfig(msg[0], "")
					if len(msg) == 0 or len(msg) > 4:
						self.bot.sendmsg(nick, "Syntax: config get key [modul] [network] [channel]")
					else:
						#self.logger.debug(".".join(msg))
						#self.logger.debug(res)
						self.bot.sendmsg(nick, ".".join(msg).encode("utf-8")+"="+res.encode("utf-8"))
				elif msg[0:3] == "set":
					#FIXME: 
					#msg=msg[4:]
					#tmp=msg.split("=")
					#if len(tmp) != 2:
					#	self.bot.sendmsg(nick, "Syntax: config set key=value")
					#	return
					#self.bot.setConfig(tmp[0], tmp[1])
					self.bot.sendmsg(nick, "function is out of order")
				else:
					self.bot.sendmsg(nick, "Syntax: config [get <key> [modul] [network] [channel]|set <key=value>]")
			elif msg[0:4] == "help":
				self.bot.sendmsg(nick,"Available administrationcommands: reload, stop|quit, disconnect [network], connect network [port], listnetworks, changenick newnick, join channel, part channel [message], listchannels")
			elif msg[0:6] == "reload":
				self.bot.sendmsg(nick,"Reloading all modules ...")
				self.bot.reloadModules()
			elif msg[0:11] == "listmodules":
				module=[]
				for mod in self.bot.mods:
					module.append(mod.name)
				self.bot.sendmsg(nick,str(module))
			elif msg[0:4] == "stop" or msg[0:4] == "quit":
				self.bot.sendmsg(nick,"Disconnecting from all networks und exiting ...")
				conns=self.bot.getConnections()
				for c in conns:
					conns[c].disconnect()
			elif msg[0:10] == "disconnect":
				args = msg[10:].split(" ")
				conns=self.bot.getConnections()
				if len(args) == 2:
					if conns.has_key(args[1]):
						self.bot.sendmsg(nick,"Disconnecting from "+str(conns[args[1]].getDestination()))
						conns[args[1]].disconnect()
					else:
						self.bot.sendmsg(nick,"Not connected to "+str(args[1]))
				else:
					self.bot.sendmsg(nick,"Disconnecting from current network. Bye.")
					self.bot.quit("Bye.")
			elif msg[0:7] == "connect":
				args = msg[7:].split(" ")
				if len(args) < 2 or len(args) > 3:
					self.bot.sendmsg(nick,"Usage: connect irc.network.tld [port]")
				else:
					if len(args) == 3:
						port=args[2]
					else:
						port=6667
					self.bot.addConnection(args[1],port)
					self.bot.sendmsg(nick,"Connecting to "+str(self.bot.getConnections()[args[1]].getDestination()))
			elif msg[0:12] == "listnetworks":
				ne=""
				for n in self.bot.getConnections():
					ne=ne+" "+n
				self.bot.sendmsg(nick,"Currently connected to:"+unicode(ne).encode("utf-8"))
			elif msg[0:12] == "listchannels":
				ch=""
				for c in self.bot.channel:
					ch=ch+" "+c
				self.bot.sendmsg(nick,"Currently in:"+unicode(ch).encode("utf-8"))
			elif msg[0:10] == "changenick":
				args=msg.split(" ")
				if len(args) < 2:
					self.bot.sendmsg(nick,"Usage: changenick newnick")
				else:
					self.bot.setNick(args[1])
			elif msg[0:4] == "join":
				args=msg.split(" ")
				if len(args) < 2:
					self.bot.sendmsg(nick,"Usage: join channel")
				else:
					self.bot.join(args[1])
					self.bot.sendmsg(nick,"Joined "+str(args[1]))
			elif msg[0:4] == "part":
				args=msg.split(" ")
				if len(args) == 1:
					self.bot.sendmsg(nick,"Usage: part channel [message]")
				else:
					if len(args) > 2:
						partmsg=" ".join(args[2:])
					else:
						partmsg=""
					self.bot.leave(args[1],partmsg)
					self.bot.sendmsg(nick,"Left "+args[1])
			elif msg[0:4] == "kick":
				args=msg.split(" ")
				if len(args) < 3:
					self.bot.sendmsg(nick,"Usage: kick channel user [message]")
				else:
					if len(args) == 3:
						self.bot.kick(args[1],args[2])
					else:
						self.bot.kick(args[1],args[2]," ".join(args[3:]))
					self.bot.sendmsg(nick,"Kicked "+args[2]+" from "+args[1]+".")
		#elif channel==self.bot.nickname:
		#	self.bot.sendmsg(nick,"Not authorized")
		elif self.bot.auth(user) > -1 and msg[0] == "!": #TODO: make "!" configurable
			if msg[1:7] == "reload":
				if len(msg.split(" ")) == 2:
					for chatMod in self.bot.mods:
						if chatMod.name == msg.split(" ")[1]:
							try:
								chatMod.reload()
								self.logger.info("Reloading Settings of "+chatMod.name)
							except Exception, e:
								self.logger.error("Error while reloading "+chatMod.name)
