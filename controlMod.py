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

import random, re
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot

	def msg(self, user, channel, msg):
		nick=user.split("!")[0]
		if self.bot.auth(user) > 7 and channel==self.bot.nickname:
			if msg[0:6] == "config":
				msg=msg[7:]
				if msg[0:3] == "get":
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
						self.logger.debug(".".join(msg))
						self.logger.debug(res)
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
				self.bot.reloadModules()
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
		elif channel==self.bot.nickname:
			self.bot.sendmsg(nick,"Not authorized")
