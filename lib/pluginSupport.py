class pluginSupport:
	#def __init__(self, *args, **kwargs):
	#	pass
	def importPlugin(self, name):
		if not self.classes:
			self.classes=[]
		for c in self.classes:
			if c.__name__ == name:
				return c
		self.classes.append(__import__(name))
		self.classes[-1].datadir = self.config.getConfig("datadir", "data", self.network)+"/"+self.classes[-1].__name__
		self.logger.debug("Imported plugin "+self.classes[-1].__name__)		
		return self.classes[-1]
	def startPlugins(self):
		"""
			initializes all known plugins
		"""
		for pluginName in self.config.getConfig("pluginsEnabled", [], "main", self.network, set_default=False):
			self.startPlugin(pluginName)

	def startPlugin(self, pluginName):
			pluginClass=self.importPlugin(pluginName)
			if hasattr(pluginClass, "Plugin"): #and hasattr(pluginClass.Plugin.ircClientPlugin) (?)
				try:
					self.logger.info("starting %s for network %s"%(pluginClass.__name__, self.network))
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
