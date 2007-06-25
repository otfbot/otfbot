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

""" Control the bot during runtime """
class configShell:
	""" Implements a shell-like Interface for manipulating the configuration """
	DESTROY_ME=234
	def __init__(self, bot):
		"""
			@type bot: a L{Bot}-Instance
		"""
		self.bot=bot
		self.configlevel=[]

	def _getlevellist(self):
		""" get a list of items at the current level
			@return: a list of items in the current level 
			@rtype: list
		"""
		if len(self.configlevel) == 0:
			return self.bot.getNetworks()
		elif len(self.configlevel) == 1:
			return self.bot.getChannels(self.configlevel[0])
		else:
			return self.bot.getSubOptions(self.configlevel)
	
	def _ls(self):
		""" get the content of the current level
			@rtype: string
		"""
		return " | ".join(self._getlevellist())
		
	def _cd(self, string):
		""" change into C{string}
			@param string: the item to change into (might be a network, a channel, a module or a level above (..))
			@type string: string
		"""
		if string == ".." and len(self.configlevel)>=0:
			self.configlevel.pop()
		else:
			num=int(string)
			if 0 < num and num < len(self._getlevellist())+1:
				self.configlevel.append(self._getlevellist()[num-1])
			else:
				return "No such setting: "+str(num)
	
	def _get(self,string):
		""" get the value of a certain item
			@param string: the identifier of the item to get
			@type string: string
			@return: the value of the requested item
			@rtype: string
		"""
		msg=string.split(" ")
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
			return "Syntax: config get key [modul] [network] [channel]"
		else:
			#self.logger.debug(".".join(msg))
			#self.logger.debug(res)
			return ".".join(msg)+"="+res
	
	def _set(self, item, value):
		"""
			should set C{item} to C{value}
			@param item: the item to update
			@type item: string
			@param value: the value to set
			@type value: string
			@note: this function does currently nothing.
		"""
		#FIXME: 
		#msg=msg[4:]
		#tmp=msg.split("=")
		#if len(tmp) != 2:
		#	self.bot.sendmsg(nick, "Syntax: config set key=value")
		#	return
		#self.bot.setConfig(tmp[0], tmp[1])
		return "function is out of order"
	
	def input(self, request):
		""" Pass all input to this function
		
			this function accepts the input, handles it to the right function and returns the result
			@param request: the command and argument
			@type request: string
			@rtype: string
			@return: the result of the command
		"""
		tmp = request.strip().split(" ",1)
		if len(tmp) == 1:
			command = tmp[0]
			argument = ""
		else:
			(command, argument) = tmp
		if command == "ls":
			return self._ls()
		elif command == "cd":
			return self._cd(argument)
		elif command == "quit":
			return self.DESTROY_ME
		elif command == "get":
			return self._get(argument)
		elif command == "set":
			return self._set(argument)
		else:
			return "config shell: '"+command+"' is not a valid command"
			#self.bot.sendmsg(nick, "Syntax: config [get <key> [modul] [network] [channel]|set <key=value>]")


class controlInterface:
	""" allows to control the behaviour of the bot during runtime
	
		this class only does the work, you need another class, most suitable is a bot-module, to have a userinterface
	"""
	def __init__(self, bot):
		"""
			@type bot: a L{Bot} Instance
		"""
		self.bot=bot
		self.configshell=None
	
	def _output(self, string):
		""" helper function which set the encoding to utf8
		"""
		return unicode(string).encode("utf-8")
	
	def input(self, request):
		""" Pass your command to this function and get the output
			@param request: command and arguments
			@type request: string
			@rtype: string
			@return: the output of the command
		"""
		tmp = request.strip().split(" ",1)
		if len(tmp) == 1:
			command=tmp[0]
			argument=""
		else:
			(command, argument) = tmp
		if self.configshell:
			output = self.configshell.input(request)
			if (output == self.configshell.DESTROY_ME):
				self.configshell=None
				return self._output("Leaving configshell ...")
			else:
				return self._output(output)
		else:
			try:
				return self._output(getattr(self,"_cmd_"+command)(argument))
			except AttributeError, e:
				return self._output("no such command: "+str(command))
			
	def _cmd_config(self,argument):
		self.configshell=configShell(self.bot)
		return "Entering configshell ..."
	def _cmd_help(self,argument):
		commands = []
		for c in dir(self):
			if c[:5] == "_cmd_":
				commands.append(c[5:])
		return "Available commands: "+" ".join(commands)
	def _cmd_reload(self,argument):
		self.bot.reloadModules()
		return "Reloading all modules ..."
	def _cmd_listmodules(self,argument):
		module=[]
		for mod in self.bot.mods:
			module.append(mod.name)
		return " ".join(module)
	def _cmd_stop(self,argument):
		conns=self.bot.factory._getnetworkslist()
		for c in conns:
			self.bot.factory._getnetwork(c).quit()
		return "Disconnecting from all networks und exiting ..."
	def _cmd_disconnect(self,argument):
		conns=self.bot.factory._getnetworkslist()
		if argument != "":
			if argument in conns:
				self.bot.factory._getnetwork(argument).quit()
				return "Disconnecting from "+str(argument)
			else:
				return "Not connected to "+str(argument)
		else:
			self.bot.quit("Bye.")
			return "Disconnecting from current network. Bye."
	def _cmd_connect(self,argument):
		args = argument.split(" ")
		if len(args) < 1 or len(args) > 2:
			return "Usage: connect irc.network.tld [port]"
		else:
			if len(args) == 2:
				port=args[1]
			else:
				port=6667
			c = self.bot.getReactor().connectTCP(args[0],port,self.bot.factory)
			return "Connecting to "+str(c)
	def _cmd_listnetworks(self,argument):
		return "Currently connected to: "+" ".join(self.bot.factory._getnetworkslist())
	def _cmd_currentnetwork(self,argument):
		return "Current network: "+self.bot.network
	def _cmd_changenetwork(self,argument):
		self.bot=self.bot.getFactory()._getnetwork(argument)
		return "changed network to "+self.bot.network
	def _cmd_listchannels(self,argument):
		return "Currently in: "+" ".join(self.bot.channels)
	def _cmd_changenick(self,argument):
		if argument == "":
			return "Usage: changenick newnick"
		else:
			self.bot.setNick(argument)
	def _cmd_join(self,argument):
		if argument == "":
			return "Usage: join channel"
		else:
			self.bot.join(argument)
			return "Joined "+str(argument)
	def _cmd_part(self,argument):
		args=argument.split(" ",1)
		if len(args) == 0:
			return "Usage: part channel [message]"
		else:
			if len(args) > 1:
				partmsg=args[1]
			else:
				partmsg=""
			self.bot.leave(args[0],partmsg)
			return "Left "+args[0]
	def _cmd_kick(self,argument):
		args=argument.split(" ",2)
		if len(args) < 2:
			return "Usage: kick channel user [message]"
		else:
			if len(args) == 2:
				self.bot.kick(args[0],args[1])
			else:
				self.bot.kick(args[0],args[1],args[3])
			return "Kicked "+args[1]+" from "+args[0]+"."