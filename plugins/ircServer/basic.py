from lib import chatMod
from twisted.words.protocols import irc
class Plugin(chatMod.chatMod):
	def __init__(self, server):
		self.server=server
		self.first=True
	#def irc_USER(self, prefix, params):
	def irc_PING(self, prefix, params):
		self.server.sendMessage("PONG", ":"+params[0])
	def irc_USER(self, prefix, params):
		self.server.user=params[0]
		self.server.hostname=params[2]
		self.server.realname=params[3]
	def irc_NICK(self, prefix, params):
		self.server.name=params[0]
		if self.first:
			self.server.sendMessage(irc.RPL_WELCOME, ":connected to OTFBot IRC", prefix="localhost")
			self.server.sendMessage(irc.RPL_YOURHOST, ":Your host is %(serviceName)s, running version %(serviceVersion)s" % {"serviceName": self.server.transport.server.getHost(),"serviceVersion": "VERSION"},prefix="localhost")
			self.server.sendMessage(irc.RPL_MOTD, ":Welcome to the Bot-Control-Server", prefix="localhost")
			self.first=False
	def irc_QUIT(self, prefix, params):
		self.server.connected=False
