#!/usr/bin/python
import handyxml

doc=handyxml.xml("config2.xml")

generic_options={}
network_options={}
channel_options={}

def getoptions(optionlist):
	ret={}
	for option in optionlist:
		try:
			ret[option.name]=option.value
		except AttributeError:
			print "Config Error: Option name or value missing"
	return ret
	
def getsuboptions(list):
	ret={}
	for item in list:
		try:
			options=item.option
		except AttributeError:
			pass
		tmp=getoptions(options)
		try:
			ret[item.name]=tmp
		except AttributeError:
			print "Config Error: network/channel has no name"
	return ret

def get(option, default, network=None, channel=None):
		try:
			return channel_options[network][channel][option]
		except KeyError:
			pass
		try:
			return network_options[network][option];
		except KeyError:
			pass
		try:
			return generic_options[option];
		except KeyError:
			pass
		if network and channel:
			if not network in channel_options.keys():
				channel_options[network]={}
			if not channel in channel_options[network].keys():
				channel_options[network][channel]={}
			channel_options[network][channel][option]=default
		elif network:
			network_options[network][option]=default
		else:
			generic_options[option]=default
		return default
			

#generic options
options=[]
try:
	options=doc.option
except AttributeError:
	pass
generic_options=getoptions(options)

#network specific
networks=[]
try:
	networks=doc.network
except AttributeError:
	pass
network_options=getsuboptions(networks);

#channel specific (format = channel_options[network][channel])
for network in networks:
	channels=[]
	try:
		channels=network.channel
	except AttributeError:
		pass
	try:
		channel_options[network.name]=getsuboptions(channels)
	except AttributeError:
		print "Config Error: network has no name"
		
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
