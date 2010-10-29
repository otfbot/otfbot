#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# (c) 2005-2008 by Alexander Schier
# (c) 2008 by Robert Weidlich
#

""" configuration service """

import sys
import os
import logging
import glob

from twisted.application import internet, service
from twisted.internet.defer import Deferred

import yaml
from copy import deepcopy


class configService(service.Service):
    name = "config"

    def __init__(self, filename=None, is_subconfig=False):
        """Initialize the config class and load a config"""
        self.logger = logging.getLogger("config")
        self.generic_options = {}
        self.network_options = {}
        self.filename = filename
        self.name = "config"

        #still the default value?
        self.generic_options_default = {}
        if not filename:
            return

        try:
            configs = yaml.load_all(open(filename, "r"))
            self.generic_options = configs.next()
            if not is_subconfig:
                self.network_options = configs.next()
                if not self.network_options:
                    self.network_options = {}
            for option in self.generic_options.keys():
                self.generic_options_default[option] = False
        except IOError:
            pass #does not exist

    def _create_preceding(self, network, channel=None):
        """
        create preceding dictionary entries for network/channel options

        >>> c=configService()
        >>> c.network_options
        {}
        >>> c._create_preceding("samplenetwork", "#samplechannel")
        >>> c.network_options
        {'samplenetwork': {'#samplechannel': {}}}
        >>> c._create_preceding("othernetwork")
        >>> c.network_options
        {'othernetwork': {}, 'samplenetwork': {'#samplechannel': {}}}
        """
        if network:
            if network not in self.network_options:
                # empty network option/channel-list
                self.network_options[network] = {}
            if channel:
                if channel not in self.network_options[network]:
                    # emtpy option-list for the given channel
                    self.network_options[network][channel] = {}

    def get(self, option, default, module=None, network=None,
                                        channel=None, set_default=True):
        """
        get an option and set the default value, if the option is unset.

        >>> c=configService()
        >>> c.get("option", "default")
        'default'
        >>> c.get("option", "unset?")
        'default'

        @param set_default: if True, the default will be set in the
                            config, if its used. If False, the default
                            will be returned, but the config will not
                            be changed.
        """
        if module:
            option = module + "." + option
        #do NOT create channel config for queries!
        #see rfc2811 section 2.1, these four are the only valid channel signs
        if channel and not channel[0] in '#+!&':
            channel=None

        #This part tries to get the config value for an option only
        if network in self.network_options:
            if channel in self.network_options[network]:
                if option in self.network_options[network][channel]:
                    #1) choice: channel specific
                    return deepcopy(self.network_options[network][channel][option])
            if option in self.network_options[network]:
                #2) choice: network specific
                return deepcopy(self.network_options[network][option])
        if option in self.generic_options:
            #3) choice: general key
            return deepcopy(self.generic_options[option])

        # if we did not return above, we need to check if the
        # default should be written to config and return the default

        if network:
            if channel:
                self._create_preceding(network, channel)
                # set the default
                self.network_options[network][channel][option] = default
            else:
                self._create_preceding(network)
                # set the default
                self.network_options[network][option] = default
        else:
            # config.writeDefaultValues is a global setting,
            # which decides if the get default-values are written to config,
            # if they are in no defaultconfig-snippets present
            # set_default is a local setting, which decides the same,
            # so modules can decide, if they want to write the default
            # value to the config. If the global setting is false, its
            # never written to config.

            # write this config.writeDefaultValues option as default value,
            # even if the default is not to write default values.
            if option == "config.writeDefaultValues" or (
                    self.has("config.writeDefaultValues") and
                    self.getBool("config.writeDefaultValues", False) and
                    set_default):
                # this will write the default value to the config
                self.set(option, default, still_default=False)
            else:
                # this will avoid a config with a lot of default options.
                self.set(option, default, still_default=True)
        return default

    def has(self, option, module=None):
        """
        Test, in which networks/channels a option is set.
        Returns a tuple: (general_bool, network_list, (network, channel) list)

        >>> c=configService()
        >>> c.has("testkey")
        (False, [], [])
        >>> c.set("testkey", "testvalue")
        >>> c.has("testkey")
        (True, [], [])
        >>> c.set("testkey", "othervalue", network="samplenetwork")
        >>> c.has("testkey")
        (True, ['samplenetwork'], [])
        """
        general = False
        networks = []
        channels = []
        if module:
            option = module + "." + option

        for item in self.generic_options.keys():
            if item == option:
                general = True
        for network in self.network_options.keys():
            if option in self.network_options[network].keys():
                networks.append(network)

        for network in self.network_options.keys():
            for channel in self.network_options[network].keys():
                if type(self.network_options[network][channel]) == dict:
                    if option in self.network_options[network][channel].keys():
                        channels.append((network, channel))
        return (general, networks, channels)

    def set(self, option, value, module=None, network=None,
                                            channel=None, still_default=False):
        if module:
                option = module + "." + option
        #do NOT create channel config for queries!
        #see rfc2811 section 2.1, these four are the only valid channel signs
        if channel and not channel[0] in '#+!&':
            channel=None

        if network:
            if channel:
                self._create_preceding(network, channel)
                self.network_options[network][channel][option] = value
            else:
                self._create_preceding(network)
                self.network_options[network][option] = value
        else:
            self.generic_options[option] = value
            self.generic_options_default[option] = still_default

        self.writeConfig()

    def delete(self, option, module=None, network=None, channel=None):
        """
        >>> c=configService()
        >>> c.set("key", "value")
        >>> c.get("key", "unset")
        'value'
        >>> c.delete("key")
        >>> c.get("key", "unset")
        'unset'
        """
        if module:
            option = module + "." + option
        if network:
            if channel:
                try:
                    del self.network_options[network][channel][option]
                except IndexError:
                    pass #does not exist anyway
            else:
                try:
                    #this can be used to delete a channel definition
                    del self.network_options[network][option]
                except IndexError:
                    pass #does not exist anyway
        else:
            try:
                del self.generic_options[option]
            except IndexError:
                pass #does not exist anyway

    def getNetworks(self):
        ret = []
        for network in self.network_options.keys():
            ret.append(network)
        return ret

    def getChannels(self, network):
        if network in self.network_options.keys():
            try:
                options = self.network_options[network].keys()
                ret = []
                for option in options:
                    if type(self.network_options[network][option]) == dict:
                        ret.append(option)
                return ret
            except AttributeError:
                return []

    ##########################################################################
    #some highlevel functions
    ##########################################################################

    def setConfig(self, opt, value, module=None, network=None, channel=None):
        self.logger.debug("deprecated call to setConfig for opt %s" % opt)
        self.set(opt, value, module, network, channel)

    def delConfig(self, opt, module=None, network=None, channel=None):
        self.logger.debug("deprecated call to delConfig for opt %s" % opt)
        delete(opt, module, network, channel)

    def hasConfig(self, option, module=None):
        self.logger.debug("deprecated call to hasConfig for opt %s" % option)
        return self.has(option, module)

    def getConfig(self, option, defaultvalue="", module=None,
                                network=None, channel=None, set_default=True):
        self.logger.debug("deprecated call to getConfig for opt %s" % option)
        return self.get(option, defaultvalue, module,
                                network, channel, set_default)

    def getPath(self, option, datadir, defaultvalue="",
                                    module=None, network=None, channel=None):
        value = self.get(option, defaultvalue, module, network, channel)
        if value[0] == "/":
            return value
        else:
            return datadir + "/" + value

    def getBool(self, option, defaultvalue="", module=None,
                                                network=None, channel=None):
        """
        >>> c=configService()
        >>> c.set("key", "1")
        >>> c.set("key2", "on")
        >>> c.set("key3", "True")
        >>> c.getBool("key") and c.getBool("key2") and c.getBool("key3")
        True
        >>> c.set("key", "False")
        >>> c.set("key2", "any string which is not in [True, true, on, On, 1]")
        >>> c.getBool("key") or c.getBool("key2")
        False
        """
        return self.get(option, defaultvalue, module,
                network, channel) in ["True", "true", "On", "on", "1", True, 1]

    def writeConfig(self):
        if not self.filename:
            return False
        file = open(self.filename, "w")
        #still_default options
        generic_options=deepcopy(self.generic_options)
        if not self.getBool("writeDefaultValues", False, "config"):
            for option in self.generic_options_default.keys():
                if option in generic_options \
                and self.generic_options_default[option]:
                    del(generic_options[option])
        file.write(yaml.dump_all([generic_options, self.network_options], 
                                 default_flow_style=False))
        file.close()
        return True
    def startService(self):
        service.Service.startService(self)

    def stopService(self):
        self.writeConfig()
        service.Service.stopService(self)

def loadConfig(myconfigfile, modulesconfigdirglob):
    if os.path.exists(myconfigfile):
        myconfig = configService(myconfigfile)
        #something like plugins/*/*.yaml
        for file in glob.glob(modulesconfigdirglob):
            tmp = configService(file, is_subconfig=True)
            for option in tmp.generic_options.keys():
                if not myconfig.has(option)[0]:
                    myconfig.set(option, tmp.get(option, ""), still_default=True)
            del(tmp)
        return myconfig
    else:
        return None

if __name__ == '__main__':
    import doctest, unittest
    doctest.testmod()
    
    class configTest(unittest.TestCase):
        def setUp(self):
            os.mkdir("test_configsnippets")
            os.mkdir("test_configsnippets2") #empty
            file = open("test_configsnippets/foomod.yaml", "w")
            file.write("""fooMod.setting1: 'blub'
fooMod.setting2: true
fooMod.setting3: false""")
            file.close()
            c = configService("testconfig.yaml")
            #c.setConfig("writeDefaultValues", True, "config")
            c.writeConfig()
            self.config = loadConfig("testconfig.yaml", "test_configsnippets/*.yaml")
        def tearDown(self):
            os.remove("test_configsnippets/foomod.yaml")
            os.rmdir("test_configsnippets")
            os.rmdir("test_configsnippets2")
            os.remove("testconfig.yaml")
        def testDefaults(self):
            blub = self.config.get("setting1", "unset", "fooMod")
            self.assertTrue(blub == "blub", "fooMod.setting1 is '%s' instead of 'blub'" % blub)
            blub2 = self.config.get("setting4", "new_setting", "fooMod")
            self.assertTrue(blub2 == "new_setting", "blub2 is '%s' instead of 'new_setting'" % blub2)

            self.config.writeConfig()
            config2 = loadConfig("testconfig.yaml", "test_configsnippets2/*.yaml")
            self.assertTrue(config2.hasConfig("setting1", "fooMod")[0] == False)
            self.assertTrue(config2.hasConfig("setting4", "fooMod")[0] == False)
        def testWriteDefaults(self):
            self.config.set("writeDefaultValues", True, "config")

            blub = self.config.get("setting1", "unset", "fooMod")
            self.assertTrue(blub == "blub", "fooMod.setting1 is '%s' instead of 'blub'" % blub)
            blub2 = self.config.get("setting4", "new_setting", "fooMod")
            self.assertTrue(blub2 == "new_setting", "blub2 is '%s' instead of 'new_setting'" % blub2)

            self.config.writeConfig()
            config2 = loadConfig("testconfig.yaml", "test_configsnippets2/*.yaml")
            self.assertTrue(config2.hasConfig("setting1", "fooMod")[0] == True)
            self.assertTrue(config2.hasConfig("setting4", "fooMod")[0] == True)
    unittest.main()

