import sys, traceback

class pluginSupport:
    pluginSupportName="[UNSET]"
    pluginSupportPath="[UNSET]"
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        self.callbacks={}
        self.classes=[]
        self.plugins={}
        #XXX: the dependency should be more explicit?
        self.config = root.getServiceNamed('config')
    def _getClassName(self, clas):
        return clas.__name__[8:] #cut off "plugins."
        
    def register_pluginsupport_commands(self):
        # Make sure to have this method!
        if not "register_ctl_command" in dir(self):
            self.register_ctl_command = lambda x, y, z: None
        self.register_ctl_command(self.startPlugin)
        self.register_ctl_command(self.stopPlugin)
        self.register_ctl_command(self.restartPlugin)
        self.register_ctl_command(lambda: self.plugins.keys(), name="listPlugins")

    def depends(self, dependency):
        raise self.DependencyMissing(dependency)
    def depends_on_module(self, dependency):
        try:
            __import__(dependency)
        except ImportError:
            raise self.ModuleMissing(dependency)
    def depends_on_service(self, dependency):
        if not self.root.getServiceNamed(dependency):
            raise self.ServiceMissing(dependency)
    def depends_on_plugin(dependency):
        if not self.plugins.has_key(dependency):
            raise self.PluginMissing(dependency)
    
    def importPlugin(self, name):
        if not self.classes:
            self.classes=[]
        for c in self.classes:
            if c.__name__ == name:
                return c
        self.classes.append(__import__(self.pluginSupportPath.replace("/", ".")+"."+name, fromlist=['*']))
        self.classes[-1].datadir = self.config.get("datadir", "data")+"/"+self._getClassName(self.classes[-1])
        self.logger.debug("Imported plugin "+self._getClassName(self.classes[-1]))
        return self.classes[-1]

    def callbackRegistered(self, module, callbackname):
        if not self.callbacks.has_key(callbackname):
            return False
        for item in self.callbacks[callbackname]:
            if item[0]==module:
                return True
        return False
    def registerCallback(self, module, callbackname, priority=10):
        if not self.callbacks.has_key(callbackname):
            self.callbacks[callbackname]=[]
        #if the module has already registered for the callback, do not reregister
        if not self.callbackRegistered(module, callbackname):
            self.callbacks[callbackname].append((module, priority))
            self.callbacks[callbackname].sort(cmp=lambda a, b: b[1]-a[1])
    def unregisterCallback(self, module, callbackname):
        if not self.callbacks.has_key(callbackname):
            return
        for index in len(self.callbacks[callbackname]):
            if self.callbacks[callbackname][0]==module:
                self.callbacks[callbackdname].remove(self.callbacks[callbackname][index])
        
    def startPlugins(self):
        """
            initializes all known plugins
        """
        for pluginName in self.config.get(self.pluginSupportName+"Plugins", [], "main", set_default=False):
            #if we are an ircClient with network attribute, disable loading of plugins network-wide
            if hasattr(self, "network") and not pluginName in self.config.get("pluginsDisabled", [], "main", self.network):
                self.startPlugin(pluginName)

    def startPlugin(self, pluginName):
            pluginClass=self.importPlugin(pluginName)
            if hasattr(pluginClass, "Plugin"): #and hasattr(pluginClass.Plugin.ircClientPlugin) (?)
                try:
                    mod=pluginClass.Plugin(self)
                    self.plugins[self._getClassName(pluginClass)]=mod
                    self.plugins[self._getClassName(pluginClass)].setLogger(self.logger)
                    self.plugins[self._getClassName(pluginClass)].name=self._getClassName(pluginClass)
                    self.plugins[self._getClassName(pluginClass)].config=self.config
                    if hasattr(self, "network"): #needed for reload!
                        self.plugins[self._getClassName(pluginClass)].network=self.network
                    if hasattr(self.plugins[self._getClassName(pluginClass)], "start"):
                        self.plugins[self._getClassName(pluginClass)].start()
                except Exception, e:
                    self.logerror(self.logger, self._getClassName(pluginClass), e)
                    return None #exception occured (e.g. dependency missing, or initialization error)
            return self.plugins[self._getClassName(pluginClass)]

    def reloadPluginClass(self, pluginClass):
            self.logger.info("reloading class "+self._getClassName(pluginClass))
            reload(pluginClass)

    def restartPlugin(self, pluginName):
        if pluginName in self.plugins.keys():
            self.stopPlugin(pluginName)
            self.startPlugin(pluginName)

    def reloadPlugins(self):
        """
            call this to reload all plugins
        """
        for chatPlugin in self.classes:
            self.reloadPluginClass(chatPlugin)
        for chatPlugin in self.plugins.values():
            self.restartPlugin(chatPlugin.name)
    
    def stopPlugin(self, pluginName):
        if not pluginName in self.plugins.keys():
            return
        chatPlugin=self.plugins[pluginName]
        self.logger.info("stopping %s" % (pluginName,))
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
    class ModuleMissing(DependencyMissing):
        pass
    class ServiceMissing(DependencyMissing):
        pass
    class PluginMissing(DependencyMissing):
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
            logger.warning("Dependency missing in plugin %s: %s is not active."%(plugin, str(exception)))
            return
        elif type(exception) == self.WontStart:
            logger.info('Plugin "%s" will not start because "%s".'%(plugin, str(exception)))
            return
        logger.error("Exception in Plugin "+plugin+": "+repr(exception))
        tb_list = traceback.format_tb(sys.exc_info()[2])
        for entry in tb_list:
            for line in entry.strip().split("\n"):
                logger.error(line)
    def _apirunner(self,apifunction,args={}):
        """
            Pass all calls to plugin callbacks through this method, they 
            are checked whether they should be executed or not.
            
            Example C{self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})}
            
            @type    apifunction: string
            @param    apifunction: the name of the callback function
            @type    args:    dict
            @param    args:    the arguments for the callback
        """
        if not self.callbacks.has_key(apifunction):
            return
        for plugin_and_priority in self.callbacks[apifunction]:
            plugin=plugin_and_priority[0] #(module, priority)
            #self.logger.debug("running "+apifunction+" for plugin "+str(mod))
            #if a channel is present, check if the plugin is disabled for the channel.
            #network wide pluginsDisabled is handled by startPlugins
            if hasattr(self, "network"):
                if args.has_key("channel"):
                    args['channel']=args['channel'].lower()
                    if plugin.name in self.config.get("pluginsDisabled",[],"main",self.network,args["channel"], set_default=False):
                        continue
            try:
                result=getattr(plugin, apifunction)(**args)
                #TODO: this should be extended something like this:
                #a function can return None (further processing) or
                #(result, statuscode), where statuscode is a constant:
                # - NO_FURTHER_PROCESSING (return result)
                # - FURTHER_PROCESSING_THIS_RESULT (returns result, after invocing all other plugins)
                # - FURTHER_PROCESSING (invoce all other plugins, return the result from the last plugin,
                #   which returned something
                #TODO: there may be conflicting statuscodes, so we need priorities in statuscodes and maybe
                #      detection of such problems on registerCallback

                #and this is the very simple form, just for now:
                if result: #stop further execution on first plugin which returns something
                    return result
            except Exception, e:
                self.logerror(self.logger, plugin.name, e)
