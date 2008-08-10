import chatMod
class chatMod(chatMod.chatMod):
	pass
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
			elif words[0]=="say":
				self.server.bot.ipc[words[1]].sendmsg(words[2], " ".join(words[3:]))
			else:
				print words
