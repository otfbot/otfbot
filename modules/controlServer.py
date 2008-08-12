import chatMod
import time
from twisted.internet import reactor

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
	def irc_unknown(self, prefix, command, params):
		if command=="PONG":
			if hasattr(self.bot.ipc, "servers"): #only if servermod is active
				for server in self.bot.ipc.servers:
					server.sendmsg(self.bot.nickname+"!bot@localhost", "#control", "%f sec. to %s."%(round(time.time()-float(params[1]), 3), params[0]))
class serverMod:
	def __init__(self, server):
		self.server=server
		self.first=True
	def irc_NICK(self, prefix, params):
		if self.first:
			self.server.join(self.server.getHostmask(), "#control")
			self.server.privmsg(self.server.getHostmask(), "#control", "Welcome to the OTFBot control channel. Type \"help\" for help ;).")
			self.server.names(self.server.name, "#control", ['OtfBot', self.server.name])
	def irc_PRIVMSG(self, prefix, params):
		msg=params[1]
		channel=params[0]
		words=msg.split(" ")
		if channel=="#control":
			if msg=="help":
				self.server.privmsg(self.server.getHostmask(), "#control", "Topics: commands, config. type help <topic> for more help.")
			elif msg=="help commands":
				self.server.privmsg(self.server.getHostmask(), "#control", "\"say servertag #channelname something\" - say something")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"connect servertag\" - connect to a known server")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"connect servertag irc.hostname.example\" - connect to a new server at irc.hostname.example")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"disconnect servertag [quitmessage]\" - disconnect from a server")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"ping servertag\" - ping a server")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"nick servertag newnickname\" - change the nick on a network")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"reload servertag/all\" - reload chat Modules for one/all networks")
				self.server.privmsg(self.server.getHostmask(), "#control", "\"quit\" - Stop the Bot")
			elif words[0]=="say":
				self.server.bot.ipc[words[1]].sendmsg(words[2], " ".join(words[3:]))
			elif words[0]=="connect":
				if len(words)==3:
					self.server.bot.setConfig("server", words[2], "main", words[1])
					self.server.bot.setConfig("enabled", "true", "main", words[1])
					self.server.bot.ipc.connectNetwork(words[1])
				elif len(words)==2:
					self.server.bot.setConfig("enabled", "true", "main", words[1])
					self.server.bot.ipc.connectNetwork(words[1])
			elif words[0]=="disconnect":
				self.server.bot.setConfig("enabled", "false", "main", words[1])
				if len(words)>=2 and words[1] in self.server.bot.ipc.getall():
					if len(words)>=3:
						self.server.bot.ipc[words[1]].quit(" ".join(words[2:]))
					else:
						self.server.bot.ipc[words[1]].quit()
			elif len(words)==2 and words[0]=="ping":
				if words[1] in self.server.bot.ipc.getall():
					self.server.bot.ipc[words[1]].sendLine("PING %f"%time.time())
			elif len(words)==3 and words[0]=="nick":
				try:
					self.server.bot.ipc[words[1]].setNick(words[2])
					self.server.bot.setConfig("nickname", words[2], "main", words[1])
				except ValueError:
					pass
			elif words[0]=="quit":
				reactor.stop()
			elif len(words)==2 and words[0]=="reload":
				if words[1]=="all":
					self.server.bot.reloadModules(True) #all networks
				else:
					if words[1] in self.server.bot.ipc.getall().keys():
						self.server.bot.ipc[words[1]].reloadModules(False)
