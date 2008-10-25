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
# (c) 2007 Robert Weidlich
#

from twisted.internet import reactor
import logging, logging.handlers
import yaml #needed for parsing dicts from set config

class controlInterface:
	""" allows to control the behaviour of the bot during runtime
	
		this class only does the work, you need another class, most suitable is a bot-module, to have a userinterface
	"""
	def __init__(self, bot):
		"""
			@type bot: a L{Bot} Instance
		"""
		self.bot=bot
		self.subcmd=""
		self.subcmdval=""
	
	def _output(self, out):
		""" helper function which set the encoding to utf8
		"""
		if type(out)==list:
			for i in xrange(len(out)):
				out[i]=unicode(out[i]).encode("UTF-8")
			return out
		else:
			return unicode(out).encode("utf-8")
	
	def input(self, request):
		""" Pass your command to this function and get the output
			@param request: command and arguments
			@type request: string
			@rtype: string
			@return: the output of the command
		"""
		# try to guess, what the user wants
		tmp = request.strip().split(" ")
		# try 1: a command in the current namespace
		func = getattr(self,"_cmd_"+self.subcmd+"_"+tmp[0], None)
		args = " ".join(tmp[1:])
		# try 2: directly called subcommand
		if not callable(func) and len(tmp) > 1:
			func = getattr(self,"_cmd_"+tmp[0]+"_"+tmp[1], None)
			args = " ".join(tmp[2:])
		# try 3: a toplevel command
		if not callable(func):
			func = getattr(self,"_cmd_"+tmp[0], None)
			args = " ".join(tmp[1:])
		# try 4: change the namespace
		if not callable(func):
			found=False;
			for c in dir(self):
				if c[5:5+len(tmp[0])] == tmp[0]:
					self.subcmd=tmp[0]
					return self._output("Changing to namespace "+tmp[0])
		if callable(func):
			return self._output(func(args))
		else:
			return self._output("No such command: "+str(tmp[0]))
			
	def _cmd_help(self,argument):
		commands = []
		for c in dir(self):
			if c[:5] == "_cmd_":
				commands.append(c[5:].replace("_"," "))
		return "Available commands: "+", ".join(commands)

	def _cmd_log_get(self, argument):
		index=1
		num=3
		if len(argument):
			args=argument.split(" ")
			if len(args)==2:
				try:
					index=int(args[1])
				except ValueError:
					pass
			try:
				num=min(int(args[0]), 10)
			except ValueError:
				pass
		for loghandler in logging.getLogger('').handlers:
			if loghandler.__class__ == logging.handlers.MemoryHandler:
				messages=[]
				for entry in loghandler.buffer[-(index + num): -index]:
					messages.append(loghandler.formatter.format(entry))
				return messages

	def _cmd_config(self,argument):
		return "type \"config set\" or \"config get\" for usage information"

	def _cmd_config_reload(self, argument):
		self.bot.loadConfig()
		return "reloaded config from file"

	def _cmd_config_set(self, argument):
		#how this works:
		#args[x][:8] is checked for network= or channel=. channel= must come after network=
		#args[x][8:] is the network/channelname without the prefix
		#" ".join(args[x:]) joins all arguments after network= and channel= to a string from word x to the end of input
		args=argument.split(" ")
		if len(args)>=4 and len(args[0])>=8 and len(args[1])>=8 and args[0][:8]=="network=" and args[1][:8]=="channel=":
			try:
				(module, setting)=args[2].split(".", 1)
				self.bot.setConfig(setting, yaml.load(" ".join(args[3:])), module, args[0][8:], args[1][8:])
				return self.bot.getConfig(setting, "[unset]", module, args[0][8:], args[1][8:])
			except ValueError:
				return "Error: your setting is not in the module.setting form"
		elif len(args)>=3 and len(args[0])>=8 and args[0][:8]=="network=":
			try:
				(module, setting)=args[1].split(".", 1)
				self.bot.setConfig(setting, yaml.load(" ".join(args[2:])), module, args[0][8:])
				return self.bot.getConfig(setting, "[unset]", module, args[0][8:])
			except ValueError:
				return "Error: your setting is not in the module.setting form"
		elif len(argument):
			try:
				(module, setting)=args[0].split(".", 1)
				self.bot.setConfig(args[0], yaml.load(" ".join(args[1:])), module)
				return self.bot.getConfig(setting, "[unset]", module)
			except ValueError:
				return "Error: your setting is not in the module.setting form"
		else:
			return "config set [network=networkname] [channel=#somechannel] setting value"

	def _cmd_config_get(self, argument):
		if len(argument)==0:
			return "config get setting [network] [channel]"
		args=argument.split(" ")
		try:
			(module, setting)=args[0].split(".", 1)
			if len(args)==1:
				return self.bot.getConfig(setting, "[unset]", module, set_default=False)
			elif len(args)==2:
				return self.bot.getConfig(setting, "[unset]", module, args[1], set_default=False)
			elif len(args)==3:
				return self.bot.getConfig(setting, "[unset]", module, args[1], args[2], set_default=False)
		except ValueError:
			return "Error: your setting is not in the module.setting form"
	
	def _cmd_modules_start(self, argument):
		if len(argument)==0:
			return "modules start module [module2] [module3] [...]"
		mods = argument.split(" ")
		for mod in mods:
			for c in self.bot.classes:
				if c.__name__==mod:
					for network in self.bot.ipc.getall():
						self.bot.ipc[network].startMod(c)
		return "started modules"
	def _cmd_modules_stop(self, argument):
		if len(argument)==0:
			return "modules stop module [module2] [module3] [...]"
		mods = argument.split(" ")
		for mod in mods:
			if mod in self.bot.mods: #TODO: this does not work with different mods per network.
				for network in self.bot.ipc.getall():
					self.bot.ipc[network].stopMod(mod)
		return "stopped modules"
	def _cmd_modules_reload(self,argument):
		tmp = argument.split(" ")
		if len(tmp) in [1,2]:
			if tmp[0] in self.bot.ipc.getall().keys():
				if len(tmp) == 1:
					self.bot.ipc[tmp[0]].reloadModules(False)
					return "Reloaded all modules of network "+tmp[0]
				else:
					if tmp[1] in self.bot.mods.keys():
						for c in self.bot.classes:
							if c.__name__==tmp[1]:
								self.bot.reloadModuleClass(c)
								self.bot.restartModule(tmp[1], tmp[0])
								break
			elif tmp[0]=="all":
				if len(tmp) == 1:
					self.bot.reloadModules(True)
					return "reloaded all modules for all networks"
				else:
					if tmp[1] in self.bot.mods.keys(): #any bot instance is ok, because every bot has the same mod classes
						for c in self.bot.classes:
							if c.__name__==tmp[1]:
								self.bot.reloadModuleClass(c)
								for network in self.bot.ipc.getall():
									self.bot.ipc[network].restartModule(tmp[1], network)
									return "restarted module %s"%tmp[1]
								break
			else:
				return "network %s not connected"%tmp[0]
		return "Usage: [modules] reload network/all [modname]"
	def _cmd_modules_list(self,argument):
		module=[]
		for mod in self.bot.mods:
			module.append(mod.name)
		return "The following modules are currently loaded: "+", ".join(module)
	
	def _cmd_stop(self,argument):
		reactor.stop()
		return "Disconnecting from all networks und exiting ..."
	
	def _cmd_network_disconnect(self,argument):
		conns=self.bot.ipc.getall()
		if argument != "":
			if argument in conns:
				self.bot.ipc.get(argument).disconnect()
				return "Disconnecting from "+str(argument)
			else:
				return "Not connected to "+str(argument)
		else:
			self.bot.disconnect()
			return "Disconnecting from current network. Bye."
	def _cmd_network_connect(self,argument):
		args = argument.split(" ")
		if len(args)==1:
			self.bot.setConfig("enabled", True, "main", args[0])
			self.bot.ipc.connectNetwork(args[0])
			return "Connecting to "+str(argument)
		elif len(args)==2:
			self.bot.setConfig("server", args[1], "main", args[0])
			self.bot.setConfig("enabled", True, "main", args[0])
			self.bot.ipc.connectNetwork(words[1])
			return "Connecting to "+str(args[0])
		else:
			return "Usage: connect irc.network.tld [port]"
	def _cmd_network_ping(self, argument):
		args=argument.split(" ")
		if args[0] in self.bot.ipc.getall().keys():
			self.bot.ipc[args[0]].sendLine("PING %f"%time.time())
			return "pinging network %s"%args[0]
	def _cmd_network_list(self,argument):
		return "Currently connected to: "+" ".join(self.bot.ipc.getall())
	def _cmd_network_current(self,argument):
		return "Current network: "+self.bot.network
	def _cmd_network_change(self,argument):
		self.bot=self.bot.ipc.get(argument)
		return "changed network to "+self.bot.network
	
	def _cmd_changenick(self,argument):
		if argument == "":
			return "Usage: changenick newnick"
		else:
			self.bot.setNick(argument)
			return "I am now known as "+argument
	
	def _cmd_channel(self,arg):
		self.subcmd="channel"
		self.subcmdval=arg
		return "Changing to namespace "+arg
	def _cmd_channel_list(self,argument):
		return "Currently in: "+" ".join(self.bot.channels)
	def _cmd_channel_join(self,argument):
		args=argument.split(" ",1)
		if len(args) == 0:
			return "Usage: join channel [key]"
		else:
			if len(args) == 1:
				self.bot.join(args[0])
			else:
				self.bot.join(args[0],args[1])
			return "Joined "+str(argument)
	def _cmd_channel_part(self,argument):
		args=argument.split(" ",1)
		if self.subcmd == "channel" and self.subcmdval != "":
			partmsg=argument
			channel=self.subcmdval
			self.subcmd=""
			self.subcmdval=""
		elif len(args) == 0:
			return "Usage: channel part channel [message]"
		else:
			if len(args) > 1:
				partmsg=args[1]
			else:
				partmsg=""
			channel=args[0]
		self.bot.leave(channel,partmsg)
		return "Left "+channel
	def _cmd_channel_kick(self,argument):
		msg=""
		if self.subcmd == "channel" and self.subcmdval != "":
			args=argument.split(" ",1)
			channel=self.subcmdval
			if len(args) == 0:
				return "Usage: kick user [message]"
			user=args[0]
			if len(args) == 2:
				msg=args[1]
		else:
			args=argument.split(" ",2)
			if len(args) < 2:
				return "Usage: channel kick channel user [message]"
			else:
				channel=args[0]
				user=args[1]
				if len(args) == 3:
					msg = args[3]
		if msg:
			self.bot.kick(channel,user,msg)
		else:
			self.bot.kick(channel,user)
		return "Kicked "+user+" from "+channel+"."
	def _cmd_channel_say(self,argument):
		if self.subcmd == "channel" and self.subcmdval != "":
			channel=self.subcmdval
			msg=argument
		else:
			args=argument.split(" ",1)
			if len(args) < 2:
				return "Usage: channel say channel|user message"
			channel=args[0]
			msg=args[1]
		self.bot.sendmsg(channel,msg)
		return " "
