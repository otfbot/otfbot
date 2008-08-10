#!/usr/bin/python
#
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
# (c) 2005, 2006 by Alexander Schier
#

import sys, os, logging

class config:
	#private
	def getoptions(self, optionlist):
		ret={}
		for option in optionlist:
			try:
				ret[option.name]=option.value
			except AttributeError:
				self.logger.error("Config Error: Option name or value missing")
		return ret
		
	def getsuboptions(self, list):
		ret={}
		for item in list:
			options=[]
			try:
				options=item.option
			except AttributeError:
				pass
			tmp=self.getoptions(options)
			try:
				ret[item.name]=tmp
			except AttributeError:
				self.logger.error("Config Error: network/channel has no name")
		return ret

	def sorted(self, list):
		"""returns the sorted list"""
		list.sort()
		return list

	#public
	def __init__(self, filename=None):
		"""Initialize the config class and load a config"""
		self.logger=logging.getLogger("config")
		self.generic_options={}
		self.network_options={}
		self.filename=filename

		#still the default value?
		self.generic_options_default={}
		if not filename:
			return
		
		import yaml
		try:
			configs=yaml.load_all(open(filename, "r"))
			self.generic_options=configs.next()
			self.network_options=configs.next()
			for option in self.generic_options.keys():
				self.generic_options_default[option]=False
		except IOError:
			pass #does not exist
	
	def get(self, option, default, module=None, network=None, channel=None):
			"""
			get an option and set the default value, if the option is unset.

			>>> c=config()
			>>> c.get("option", "default")
			'default'
			>>> c.get("option", "unset?")
			'default'
			"""
			if module:
				option=module+"."+option

			try:
				return self.network_options[network][channel][option]
			except KeyError:
				pass
			try:
				return self.network_options[network][option];
			except KeyError:
				pass
			try:
				return self.generic_options[option];
			except KeyError:
				pass
			#set default in config, and return it
			if network and channel:
				if not network in self.network_options.keys():
					self.network_options[network]={}
				if not channel in self.network_options[network].keys():
					self.network_options[network][channel]={}
				self.network_options[network][channel][option]=default
			elif network:
				if not network in self.network_options.keys():
					self.network_options[network]={}
				self.network_options[network][option]=default
			else:
				if option=="config.writeDefaultValues" or (self.has("config.writeDefaultValues") and self.get("config.writeDefaultValues", "False") in ["true", "True", "on", "On", "1"]): #write this config option as defaultvalue, even if the default is not to write default values.
					self.set(option, default, still_default=False) #this will write the default value to the config
				else:
					self.set(option, default, still_default=True) #this will avoid a config with a lot of (maybe changed in later releases) default options.
			return default

	def has(self, option, module=None):
		"""
		test, in which networks/channels a option is set. 
		Returns a tuple: (general_bool, network_list, (network, channel) list)

		>>> c=config()
		>>> c.has("testkey")
		(False, [], [])
		>>> c.set("testkey", "testvalue")
		>>> c.has("testkey")
		(True, [], [])
		>>> c.set("testkey", "othervalue", network="samplenetwork")
		>>> c.has("testkey")
		(True, ['samplenetwork'], [])
		"""
		general=False
		networks=[]
		channels=[]
		if module:
			option=module+"."+option

		for item in self.generic_options.keys():
			if item==option:
				general=True
		for network in self.network_options.keys():
			if option in self.network_options[network].keys():
				networks.append(network)

		for network in self.network_options.keys():
			for channel in self.network_options[network].keys():
				if type(channel)==type({}):
					if option in self.network_options[network][channel].keys():
						channels.append((network, channel))
		return (general, networks, channels)

	
	def set(self, option, value, module=None, network=None, channel=None, still_default=False):
		if module:
				option=module+"."+option

		if network and channel:
			if not network in self.network_options.keys():
				self.network_options[network]={}
			if not channel in self.network_options[network].keys():
				self.network_options[network][channel]={}
			self.network_options[network][channel][option]=value
		elif network:
			if not network in self.network_options.keys():
				self.network_options[network]={}
			self.network_options[network][option]=value
		else:
			self.generic_options[option]=value
			self.generic_options_default[option]=still_default

	def delete(self, option, module=None, network=None, channel=None):
		"""
		>>> c=config()
		>>> c.set("key", "value")
		>>> c.get("key", "unset")
		'value'
		>>> c.delete("key")
		>>> c.get("key", "unset")
		'unset'
		"""
		if module:
			option=module+"."+option
		if network and channel:
			try:
				del self.network_options[network][channel][option]
			except IndexError:
				pass #does not exist anyway
		elif network:
			try:
				#this can be used to delete a channel definition
				del self.network_options[network][option]
			except IndexError:
				pass #does not exist anyway
		else:
			del self.generic_options[option]

	def getNetworks(self):
		ret=[]
		for network in self.network_options.keys():
			ret.append(network)
		return ret
	def getChannels(self, network):
		#TODO: Return only channels, which are active
		if network in self.network_options.keys():
			try:
				options=self.network_options[network].keys()
				ret=[]
				for option in options:
					if type(self.network_options[network][option])==type({}):
						ret.append(option)
				return ret
			except AttributeError:
				return []

	def exportyaml(self):
		try:
			import yaml
		except ImportError:
			return ""
		return yaml.dump_all([self.generic_options,self.network_options], default_flow_style=False)
################################################################################
	#some highlevel functions
	def setConfig(self, option, value, module=None, network=None, channel=None):
		self.set(option, value, module, network, channel)
		self.writeConfig(self.filename)
			
	def delConfig(self, option, module=None, network=None, channel=None):
		delete(option, module, network, channel)
	def hasConfig(self, option, module=None):
		return self.has(option, module)
	def getConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		return self.get(option, defaultvalue, module, network, channel)
	def getPathConfig(self, option, datadir, defaultvalue="", module=None, network=None, channel=None):
		value=self.get(option, defaultvalue, module, network, channel)
		if value[0]=="/":
			return value
		else:
			return datadir+"/"+value
	def getBoolConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
		"""
		>>> c=config()
		>>> c.set("key", "1")
		>>> c.set("key2", "on")
		>>> c.set("key3", "True")
		>>> c.getBoolConfig("key") and c.getBoolConfig("key2") and c.getBoolConfig("key3")
		True
		>>> c.set("key", "False")
		>>> c.set("key2", "any string which is not in [True, true, on, On, 1]")
		>>> c.getBoolConfig("key") or c.getBoolConfig("key2")
		False
		"""
		return self.get(option, defaultvalue, module, network, channel) in ["True","true","On","on","1"]
	
	def writeConfig(self, configfile):
		file=open(configfile, "w")
		file.write(self.exportyaml())
		file.close()
def loadConfig(myconfigfile, modulesconfigdir):
	if os.path.exists(myconfigfile):
		myconfig=config(myconfigfile)
		for file in os.listdir(modulesconfigdir):
			if len(file)>=4 and file[-4:]==".yaml":
				tmp=config(modulesconfigdir+"/"+file)
				for option in tmp.generic_options.keys():
					if not myconfig.has(option):
						myconfig.set(tmp.get(option, ""), still_default=True)
	
		return myconfig
	else:
		return None
	
if __name__ == '__main__':
	import doctest
	doctest.testmod()
