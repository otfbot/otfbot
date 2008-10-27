import sys, traceback

#TODO: we do not have ipc anymore, and self.network only applys to ircClientPlugins

class pluginSupport:
	pluginSupportName="[UNSET]"
	pluginSupportPath="[UNSET]"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		self.getClient=lambda network: root.getNamedServices()['ircClient'].namedServices[network].args[2].protocol
		self.getClientNames=lambda : [connection.name for connection in root.getNamedServices()['ircClient'].services]
		self.getServer=lambda network: root.getNamedServices()['ircServer'].namedServices[network].args[2].protocol
		self.getServers=lambda : [connection for connection in root.getNamedServices()['ircServer'].services]
	def importPlugin(self, name):
		if not self.classes:
			self.classes=[]
		for c in self.classes:
			if c.__name__ == name:
				return c
		self.classes.append(__import__(self.pluginSupportPath.replace("/", ".")+"."+name, fromlist=['*']))
		self.classes[-1].datadir = self.config.get("datadir", "data")+"/"+self.classes[-1].__name__
		self.logger.debug("Imported plugin "+self.classes[-1].__name__)		
		return self.classes[-1]
	def startPlugins(self):
		"""
			initializes all known plugins
		"""
		for pluginName in self.config.get(self.pluginSupportName+"PluginsEnabled", [], "main", set_default=False):
			self.startPlugin(pluginName)

	def startPlugin(self, pluginName):
			pluginClass=self.importPlugin(pluginName)
			if hasattr(pluginClass, "Plugin"): #and hasattr(pluginClass.Plugin.ircClientPlugin) (?)
				try:
					#TODO: no network in this abstract class
					#self.logger.info("starting %s for network %s"%(pluginClass.__name__, self.network))
					mod=pluginClass.Plugin(self)
					self.plugins[pluginClass.__name__]=mod
					self.plugins[pluginClass.__name__].setLogger(self.logger)
					self.plugins[pluginClass.__name__].name=pluginClass.__name__
					self.plugins[pluginClass.__name__].config=self.config
					if hasattr(self, "network"): #needed for reload!
						self.plugins[pluginClass.__name__].network=self.network
					if hasattr(self.plugins[pluginClass.__name__], "start"):
						self.plugins[pluginClass.__name__].start()
				except Exception, e:
					self.logerror(self.logger, pluginClass.__name__, e)

	def reloadPluginClass(self, pluginClass):
			self.logger.info("reloading class "+pluginClass.__name__)
			reload(pluginClass)
	def restartPlugin(self, pluginName, network):
		if network in self.ipc.getall() and pluginName in self.ipc[network].plugins.keys():
			self.ipc[network].stopPlugin(pluginName)
			c=None
			#this is not optimal, because each plugin needs to iterate over all classes
			for c in self.classes:
				if c.__name__==pluginName:
					break
			self.ipc[network].startPlugin(c)

	def reloadPlugins(self, all=True):
		"""
			call this to reload all plugins
		"""
		for chatPlugin in self.classes:
			self.reloadPluginClass(chatPlugin)
		if all: #global
			for network in self.ipc.getall().keys():
				for plugin in self.ipc[network].plugins.keys():
					self.restartPlugin(plugin, network)
		else:
			for chatPlugin in self.plugins.values():
				self.restartPlugin(chatPlugin.name, self.network)
	
	def stopPlugin(self, pluginName):
		if not pluginName in self.plugins.keys():
			return
		chatPlugin=self.plugins[pluginName]
		self.logger.info("stopping %s for network %s"%(pluginName, self.network))
		try:
			chatPlugin.stop()
		except Exception, e:
			self.logerror(self.logger, chatPlugin.name, e)
		del(self.plugins[pluginName])
		del(chatPlugin)
	class WontStart(Exception):
		pass
	class DependencyMissing(Exception):
		pass
	def logerror(self, logger, plugin, exception):
		""" format a exception nicely and pass it to the logger
			@param logger: the logger instance to use
			@param plugin: the plugin in which the exception occured
			@type plugin: string
			@param exception: the exception
			@type exception: exception
		"""
		if type(exception) == self.DependencyMissing:
			logger.error("Dependency missing in plugin %s: %s is not active."%(plugin, str(exception)))
			return
		elif type(exception) == self.WontStart:
			logger.info('Plugin "%s" will not start because "%s".'%(plugin, str(exception)))
			return
		logger.error("Exception in Plugin "+plugin+": "+str(exception))
		tb_list = traceback.format_tb(sys.exc_info()[2])
		for entry in tb_list:
			for line in entry.strip().split("\n"):
				logger.error(line)
	def _apirunner(self,apifunction,args={}):
		"""
			Pass all calls to plugin callbacks through this method, they 
			are checked whether they should be executed or not.
			
			Example C{self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})}
			
			@type	apifunction: string
			@param	apifunction: the name of the callback function
			@type	args:	dict
			@param	args:	the arguments for the callback
		"""
		for plugin in self.plugins.values():
			#self.logger.debug("running "+apifunction+" for plugin "+str(mod))
			#if a channel is present, check if the plugin is disabled for the channel.
			if hasattr(self, "network"):
				if args.has_key("channel"):
					args['channel']=args['channel'].lower()
					if plugin.name in self.config.get("pluginsDisabled",[],"main",self.network,args["channel"], set_default=False):
						return
				if plugin.name in self.config.get("pluginsDisabled", [], "main", self.network):
					return
			try:
				if hasattr(plugin, apifunction):
					getattr(plugin, apifunction)(**args)
			except Exception, e:
				self.logerror(self.logger, plugin.name, e)
