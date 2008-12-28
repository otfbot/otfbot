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
import time
from twisted.application import internet, service

class botService(service.MultiService):
	""" allows to control the behaviour of the bot during runtime
	
		this class only does the work, you need another class, most suitable is a bot-module, to have a userinterface
	"""
	name="control"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		service.MultiService.__init__(self)

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
		self.parent.getServiceNamed("config").loadConfig()
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
				self.parent.getServiceNamed("config").set(setting, yaml.load(" ".join(args[3:])), module, args[0][8:], args[1][8:])
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[0][8:], args[1][8:])
			except ValueError:
				return "Error: your setting is not in the module.setting form"
		elif len(args)>=3 and len(args[0])>=8 and args[0][:8]=="network=":
			try:
				(module, setting)=args[1].split(".", 1)
				self.parent.getServiceNamed("config").set(setting, yaml.load(" ".join(args[2:])), module, args[0][8:])
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[0][8:])
			except ValueError:
				return "Error: your setting is not in the module.setting form"
		elif len(argument):
			try:
				(module, setting)=args[0].split(".", 1)
				self.parent.getServiceNamed("config").set(args[0], yaml.load(" ".join(args[1:])), module)
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module)
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
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module, set_default=False)
			elif len(args)==2:
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[1], set_default=False)
			elif len(args)==3:
				return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[1], args[2], set_default=False)
		except ValueError:
			return "Error: your setting is not in the module.setting form"
	
	def _cmd_stop(self,argument):
		reactor.stop()
		return "Disconnecting from all networks und exiting ..."

	def _cmd_network_disconnect(self,argument):
		args = argument.split(" ")
		if len(args)==1:
			if argument in self.parent.getServiceNamed("ircClient").namedServices:
				self.parent.getServiceNamed("ircClient").removeService(
					self.parent.getServiceNamed("ircClient").getServiceNamed(argument)
				)
				return "Disconnecting from %s." % argument
			else:
				return "Not connected to %s." % argument
		else:
			return "Usage: disconnect <network>"

	def _cmd_network_connect(self,argument):
		args = argument.split(" ")
		if len(args)==1:
			self.parent.getServiceNamed("ircClient").connect(args[0])
			return "Connecting to "+str(argument)
		else:
			return "Usage: connect <network>"

	def _cmd_network_ping(self, argument):
		args=argument.split(" ")
		if args[0] in self.parent.getServiceNamed("ircClient").namedServices:
			self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.sendLine("PING %f"%time.time())
			return "pinging network %s" % args[0]
		else:
			return "no network named %s known" % args[0]

	def _cmd_network_list(self,argument):
		nwks = ", ".join(self.parent.getServiceNamed("ircClient").namedServices.keys())
		return "Currently connected to: %s." % nwks

	def _cmd_changenick(self,argument):
		args = argument.split(" ")
		if len(args) != 2:
			return "Usage: changenick <network> <newnick>"
		else:
			self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.setNick(args[1])
			return "I am now known on %s as %s " % tuple(args)

	def _cmd_channel_list(self,argument):
		args=argument.split(" ")
		if len(args) == 1 and args[0] != "":
			ch=self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.channels
			return "Currently in: %s." % ", ".join(ch)
		if len(args) == 1 and args[0] == "":
			ch=[]
			for net in self.parent.getServiceNamed("ircClient").namedServices.keys():
				for c in self.parent.getServiceNamed("ircClient").getServiceNamed(net).protocol.channels:
					ch.append(net+":"+c)
			return "Currently in: %s." % ", ".join(ch)
		else:
			return "Usage: channel list [network]"

	def _cmd_channel_join(self,argument):
		args=argument.split(" ",1)
		if len(args) < 2 or len(args) > 3:
			return "Usage: join <network> <channel> [key]"
		else:
			if len(args) == 2:
				self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.join(args[1])
			else:
				self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.join(args[1],args[2])
			return "Joined %s " % args[1]

	def _cmd_channel_part(self,argument):
		args=argument.split(" ",2)
		if len(args) < 2:
			return "Usage: channel part <network> <channel> [message]"
		if len(args) > 2:
			partmsg=args[2]
		else:
			partmsg=""
		channel=args[1]
		self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.leave(channel,partmsg)
		return "Left %s " % channel

	def _cmd_channel_kick(self,argument):
		msg=""
		args=argument.split(" ",3)
		if len(args) < 3:
			return "Usage: channel kick <network> <channel> <user> [message]"
		else:
			channel=args[0]
			user=args[1]
			if len(args) == 3:
				msg = args[3]
		if msg:
			self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.kick(channel,user,msg)
		else:
			self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.kick(channel,user)
		return "Kicked %s from %s." % (user, channel)

	def _cmd_channel_say(self,argument):
		args=argument.split(" ",2)
		if len(args) < 3:
			return "Usage: channel say <network> <channel>|<user> <message>"
		channel=args[1]
		msg=args[2]
		self.parent.getServiceNamed("ircClient").getServiceNamed(args[0]).protocol.sendmsg(channel,msg)
		return " "



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
