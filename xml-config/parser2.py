#!/usr/bin/python
import handyxml



class config:
	def __init__(self, filename):
		"""Initialize the config class and load a xml config"""
		self.generic_options={}
		self.network_options={}
		self.channel_options={}
		
		self.doc=handyxml.xml(filename)
		#generic options
		options={}
		try:
			options=self.doc.option
		except AttributeError:
			pass
		self.generic_options=self.getoptions(options)
	
		#network specific
		networks=[]
		try:
			networks=self.doc.network
		except AttributeError:
			pass
		self.network_options=self.getsuboptions(networks);
	
		#channel specific (format = channel_options[network][channel])
		for network in networks:
			channels=[]
			try:
				channels=network.channel
			except AttributeError:
				pass
			try:
				self.channel_options[network.name]=self.getsuboptions(channels)
			except AttributeError:
				print "Config Error: network has no name"
	
	def getoptions(self, optionlist):
		ret={}
		for option in optionlist:
			try:
				ret[option.name]=option.value
			except AttributeError:
				print "Config Error: Option name or value missing"
		return ret
		
	def getsuboptions(self, list):
		ret={}
		for item in list:
			try:
				options=item.option
			except AttributeError:
				pass
			tmp=self.getoptions(options)
			try:
				ret[item.name]=tmp
			except AttributeError:
				print "Config Error: network/channel has no name"
		return ret
	
	def get(self, option, default, network=None, channel=None):
			try:
				return self.channel_options[network][channel][option]
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
				if not network in self.channel_options.keys():
					self.channel_options[network]={}
				if not channel in self.channel_options[network].keys():
					self.channel_options[network][channel]={}
				self.channel_options[network][channel][option]=default
			elif network:
				if not network in self.network_options.keys():
					self.network_options[network]={}
				self.network_options[network][option]=default
			else:
				self.generic_options[option]=default
			return default
	
	def set(self, option, value, network=None, channel=None):
		if network and channel:
			if not network in self.channel_options.keys():
				self.channel_options[network]={}
			if not channel in self.channel_options[network].keys():
				self.channel_options[network][channel]={}
			self.channel_options[network][channel][option]=value
		elif network:
			if not network in self.network_options.keys():
				self.network_options[network]={}
			self.network_options[network][option]=value
		else:
			self.generic_options[option]=value
				

	def getxml(self):
		ret="<?xml version=\"1.0\"?>\n"
		ret+="<chatbot>\n"
		indent="	";
		#generic options
		for option in self.generic_options.keys():
			ret+=indent+"<option name=\""+option+"\" value=\""+self.generic_options[option]+"\" />\n"
		#network specific
		channel_networks=self.channel_options.keys() #get the networks, for which we have channel settings
		for network in self.network_options.keys():
			ret+=indent+"<network name=\""+network+"\">\n"
			for option in self.network_options[network].keys():
				ret+=indent*2+"<option name=\""+option+"\" value=\""+self.network_options[network][option]+"\" />\n"
			if network in channel_networks:
				for channel in self.channel_options[network].keys():
					ret+=indent*2+"<channel name=\""+channel+"\">\n"
					for option in self.channel_options[network][channel].keys():
						ret+=indent*3+"<option name=\""+option+"\" value=\""+self.channel_options[network][channel][option]+"\" />\n"
					ret+=indent*2+"</channel>\n"
			ret+=indent+"</network>\n"
		
		ret+="</chatbot>\n"
		return ret

def test_get():
	print "Test:"
	print "Which channel?"
	channel=raw_input();
	print "Which Network?"
	network=raw_input()
	print "Which Setting?"
	setting=raw_input()
	print "Default String?"
	default=raw_input()
	print "Result:"
	print ""
	print get(setting, default, network, channel)


myconfig=config("config2.xml")
print myconfig.getxml()
#print generic_options
#print getxml();
#test_get()