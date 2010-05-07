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
# (c) 2009 - 2010 by Alexander Schier
# (c) 2009 - 2010 by Robert Weidlich
#

import sys
import traceback


class pluginSupport:
    """
    inherit from this class to enable support for plugins

    you need to inherit from this class, and set pluginSupportName
    and pluginSupportPath, you need to inherit from
    L{twisted.application.service.MultiService}, too
    """
    pluginSupportName = "[UNSET]"
    pluginSupportPath = "[UNSET]"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.callbacks = {}
        self.classes = []
        self.plugins = {}
        #XXX: the dependency should be more explicit?
        self.config = root.getServiceNamed('config')

    def _getClassName(self, clas):
        return clas.__name__[15:] #cut off "otfbot.plugins."

    def register_pluginsupport_commands(self):
        # Make sure to have this method!
        if not "register_ctl_command" in dir(self):
            self.register_ctl_command = lambda x, y, z: None
        self.register_ctl_command(self.startPlugin)
        self.register_ctl_command(self.stopPlugin)
        self.register_ctl_command(self.restartPlugin)
        self.register_ctl_command(lambda: self.plugins.keys(),
                                                    name="listPlugins")

    def depends(self, dependency, description=""):
        """raises a DependencyMissing exception for dependency"""
        raise self.DependencyMissing(dependency, description)

    def depends_on_module(self, dependency, description=""):
        """
            try to import a module, raise a ModuleException,
            if it cannot be loaded
        """
        try:
            return __import__(dependency)
        except ImportError:
            raise self.ModuleMissing(dependency, description)

    def depends_on_service(self, dependency, description=""):
        """
            depend on a service, raise an ServiceMissing Exception,
            if its not available/enabled/loaded
        """
        if not self.root.getServiceNamed(dependency):
            raise self.ServiceMissing(dependency, description)

    def depends_on_plugin(dependency, description=""):
        """
            depend on another plugin, raise a PluginMissing
            xception, if its not enabled
        """
        if not dependency in self.plugins:
            raise self.PluginMissing(dependency, description)

    def importPlugin(self, name):
        if not self.classes:
            self.classes = []
        for c in self.classes:
            if c.__name__ == name:
                return c
        pkg = self.pluginSupportPath.replace("/", ".") + "." + name
        cls = __import__(pkg, fromlist=['*'])
        cls.datadir = self.config.get("datadir", "data")
        cls.datadir += "/" + self._getClassName(cls)
        self.classes.append(cls)
        self.logger.debug("Imported plugin " + self._getClassName(cls))
        return self.classes[-1]

    def callbackRegistered(self, module, callbackname):
        """
            test, if a module has already registered a callback
            for callbackname
        """
        if callbackname not in self.callbacks:
            return False
        for item in self.callbacks[callbackname]:
            if item[0] == module:
                return True
        return False

    def registerCallback(self, module, callbackname, priority=10):
        """
            register module for a callbackname, with a specified
            priority (higher priority = invoced before callbacks
            from other modules)
        """
        if callbackname not in self.callbacks:
            self.callbacks[callbackname] = []
        # if the module has already registered for the
        # callback, do not register again
        if not self.callbackRegistered(module, callbackname):
            self.callbacks[callbackname].append((module, priority))
            self.callbacks[callbackname].sort(cmp=lambda a, b: b[1] - a[1])

    def unregisterCallback(self, module, callbackname):
        """unregister a callback for a module"""
        if callbackname not in self.callbacks:
            return
        for index in len(self.callbacks[callbackname]):
            if self.callbacks[callbackname][0] == module:
                self.callbacks[callbackdname].remove(
                                        self.callbacks[callbackname][index])

    def startPlugins(self):
        """
            initializes all known plugins
        """
        plugins = self.config.get(
                    self.pluginSupportName + "Plugins",
                    [], "main", set_default=False)
        for plginName in plugins:
            if not plginName in self.config.get("pluginsDisabled", [], "main"):
                self.startPlugin(plginName)

    def startPlugin(self, pluginName):
        """
        start the plugin named pluginName

        start a plugin, by importing pluginSupportName.pluginName,
        instancing the plugin and calling its start() function
        """
        pluginClass = self.importPlugin(pluginName)
        if hasattr(pluginClass, "Plugin"):
        # and hasattr(pluginClass.Plugin.ircClientPlugin) (?)
            try:
                mod = pluginClass.Plugin(self)
                mod.setLogger(self.logger)
                mod.name = self._getClassName(pluginClass)
                mod.config = self.config
                if hasattr(self, "network"): #needed for reload!
                    mod.network = self.network
                if hasattr(mod, "start"):
                    mod.start()
                self.plugins[self._getClassName(pluginClass)] = mod
            except Exception, e:
                self.logerror(self.logger, self._getClassName(pluginClass), e)
                # exception occured (e.g. dependency missing
                # or initialization error)
                return None
        return self.plugins[self._getClassName(pluginClass)]

    def reloadPluginClass(self, pluginClass):
        """reload a pluginClass"""
        self.logger.info("reloading class " + self._getClassName(pluginClass))
        reload(pluginClass)

    def restartPlugin(self, pluginName):
        """stop and start again a plugin"""
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

    def stopPlugins(self):
        """
            stop all Plugins
        """
        for chatPlugin in self.plugins.values():
            self.stopPlugin(chatPlugin.name)

    def stopPlugin(self, pluginName):
        """stop a plugin named pluginName"""
        if not pluginName in self.plugins.keys():
            return
        chatPlugin = self.plugins[pluginName]
        self.logger.info("stopping %s" % (pluginName,))
        try:
            chatPlugin.stop()
        except Exception, e:
            self.logerror(self.logger, chatPlugin.name, e)
        del(self.plugins[pluginName])
        del(chatPlugin)

    class WontStart(Exception):
        """Exception thrown by plugins, which cannot start"""
        pass

    class DependencyMissing(Exception):
        """thrown, if a dependency is missing"""

        def __init__(self, dependency, description):
            self.dependency = dependency
            self.description = description
            msg = "%s missing. %s" % (dependency, description)
            Exception.__init__(self, msg)

    class ModuleMissing(DependencyMissing):
        """through if a module is missing"""
        pass

    class ServiceMissing(DependencyMissing):
        """through if a service is missing"""
        pass

    class PluginMissing(DependencyMissing):
        """through if a plugin is missing"""
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
            msg = "Dependency missing in plugin %s: %s. plugin not started."
            logger.warning(msg % (plugin, str(exception)))
            return
        elif type(exception) == self.WontStart:
            msg = 'Plugin "%s" will not start because "%s".'
            logger.info(msg % (plugin, str(exception)))
            return
        logger.error("Exception in Plugin " + plugin + ": " + repr(exception))
        tb_list = traceback.format_tb(sys.exc_info()[2])[1:]
        for entry in tb_list:
            for line in entry.strip().split("\n"):
                logger.error(line)

    def _apirunner(self, apifunction, args={}):
        """
            Pass all calls to plugin callbacks through this method, they
            are checked whether they should be executed or not.

            Example C{self._apirunner("privmsg",
                                {"user":user,"channel":channel,"msg":msg})}

            @type  apifunction: string
            @param apifunction: the name of the callback function
            @type  args:        dict
            @param args:        the arguments for the callback
        """
        if apifunction not in self.callbacks:
            return
        for plugin_and_priority in self.callbacks[apifunction]:
            plugin = plugin_and_priority[0] #(module, priority)
            # self.logger.debug("running "+apifunction+" for plugin "+str(mod))
            # if a channel is present, check if the plugin is disabled for
            # the channel. Network-wide pluginsDisabled is
            # handled by startPlugins
            if hasattr(self, "network"):
                if "channel" in args:
                    args['channel'] = args['channel'].lower()
                    plugins = self.config.get("pluginsDisabled", [], "main",
                                        self.network, args["channel"],
                                        set_default=False)
                    if plugin.name in plugins:
                        continue
            try:
                result = getattr(plugin, apifunction)(**args)
                #TODO: this should be extended something like this:
                # a function can return None (further processing) or
                # (result, statuscode), where statuscode is a constant:
                # - NO_FURTHER_PROCESSING (return result)
                # - FURTHER_PROCESSING_THIS_RESULT (returns result, after
                #   invocing all other plugins)
                # - FURTHER_PROCESSING (invoce all other plugins, return
                #   the result from the last plugin,
                #   which returned something
                #TODO: there may be conflicting statuscodes, so we need
                #      priorities in statuscodes and maybe
                #      detection of such problems on registerCallback

                # and this is the very simple form, just for now:
                if result:
                    # stop further execution on first plugin which
                    # returns something
                    return result
            except Exception, e:
                self.logerror(self.logger, plugin.name, e)
