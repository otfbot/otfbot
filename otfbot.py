#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
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
# (c) 2005, 2006 by Alexander Schier
# (c) 2006 by Robert Weidlich
# 

"""Chat Bot"""

# standard Python libs
import os, random, string, re, sys, atexit, time
# libs from Python twisted
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, error, ssl

# Path for auxilary libs of otfbot
sys.path.insert(1,"lib")
# modules from otfbot
import functions, config
from botfactory import BotFactory
from bot import Bot

# some constants for paths, might be read from configfile in future
path_log="otfbot.log"
path_pid="otfbot.pid"
path_cfg="etc/otfbot.yaml"
path_mods="modules"
path_data="data"

# Path for bot-modules
sys.path.insert(1,path_mods)

###############################################################################
# Parse commandline options
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--config",dest="configfile",metavar="FILE",help="Location of configfile",type="string")
parser.add_option("-d","--debug",dest="debug",metavar="LEVEL",help="Show debug messages of level LEVEL (10, 20, 30, 40 or 50). Implies -f.", type="int", default=0)
parser.add_option("-f","--nodetach",dest="foreground",help="Do not fork into background.",action="store_true", default=False)

parser.add_option("-u","--user",dest="userid",help="if run as root, the bot needs a userid to chuid to.",type="int", default=0)
parser.add_option("-g","--group",dest="groupid",help="if run as root, the bot needs a groupid to chgid to.",type="int", default=0)

(options,args)=parser.parse_args()
if options.debug and options.debug not in (10,20,30,40,50):
	parser.error("Unknown value for --debug")
###############################################################################
#check for root rights
if os.getuid()==0:
	if options.userid and options.userid!=0 and options.groupid and options.groupid!=0:
		from twisted.python.util import switchUID
		#os.chroot(".") #DOES NOT WORK. pwd.getpwuid fails in switchUID, when chrooted.
		switchUID(options.userid, options.groupid)
	else:
		print "Otfbot should not be run as root."
		print "please use -u and -g to specify a userid/groupid"
		sys.exit(1)
###############################################################################
# Detaching from console
if options.foreground == False and not options.debug > 0:
	try:
		import subprocess
		subprocess.Popen(["python",sys.argv[0],"-f"])
		sys.exit(0)
	except ImportError:
		pass
###############################################################################
# Setup Logging
import logging
import logging.handlers
from twisted.python import log
import log as otfbotlog
# Basic settings for logging
# logging to logfile
filelogger = logging.handlers.RotatingFileHandler(path_log,'a',1048576,5)
#filelogger = logging.FileHandler(path_log,'a')
logging.getLogger('').setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
filelogger.setFormatter(formatter)
logging.getLogger('').addHandler(filelogger)
#corelogger.addHandler(filelogger)

if options.debug > 0:
	# logging to stdout
	console = logging.StreamHandler()
	logging.getLogger('').setLevel(options.debug)
	formatter = logging.Formatter('%(asctime)s %(name)-10s %(module)-18s %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)
	#corelogger.addHandler(console)
corelogger = logging.getLogger('core')
corelogger.info("  ___ _____ _____ ____        _   ")
corelogger.info(" / _ \_   _|  ___| __ )  ___ | |_ ")
corelogger.info("| | | || | | |_  |  _ \ / _ \| __|")
corelogger.info("| |_| || | |  _| | |_) | (_) | |_ ")
corelogger.info(" \___/ |_| |_|   |____/ \___/ \__|")
corelogger.info("")
svnrevision="$Revision$".split(" ")[1]
corelogger.info("Starting OtfBot - Version svn "+svnrevision)
# get messages from twisted as well
plo=otfbotlog.PythonLoggingObserver()
plo.start()


###############################################################################

def exithook():
	""" This function is called, when the program terminates. """
	# remove Pidfile
	os.remove(pidfile)
	theconfig.writeConfig(configfile)
	corelogger.info("Bot shutted down")
	corelogger.info("-------------------------")

# Load modules
classes=[]
for file in os.listdir(path_mods):
	if len(file)>=3 and file[-3:]==".py":
		classes.append(__import__(file[:-3]))
		#classes[-1].datadir = "modules/"+classes[-1].__name__+"-data"
		classes[-1].datadir = path_data+"/"+classes[-1].__name__
		corelogger.debug("Loading module "+classes[-1].__name__)

###############################################################################
# some config functions
theconfig=None

try:
	configfile=parser.configfile
except AttributeError:
	configfile=path_cfg
modulesconfigdir=path_mods #TODO: configuration-option(?)
theconfig=config.loadConfig(configfile, modulesconfigdir)

def createClassList():
	print theconfig.hasConfig("modsEnabled", "main")[0]
	if theconfig.hasConfig("modsEnabled", "main")[0]==False: #TODO: how to handle if only classes have module-lists?
		print [i.__name__ for i in classes]
		theconfig.set("modsEnabled", [i.__name__ for i in classes], "main")

if not theconfig: #file could not be loaded, i.e at first start
	theconfig=config.config()
	theconfig.set('enabled', 'false', 'main', 'samplenetwork')
	theconfig.set('server', 'localhost', 'main', 'samplenetwork')
	theconfig.set('enabled', 'false', 'main', 'samplenetwork', '#example')
	theconfig.set('nickname', 'OtfBot', 'main')
	theconfig.set('encoding', 'UTF-8', 'main')
	theconfig.set('pidfile','otfbot.pid','main')
		
	createClassList() #because of the system.exit we need this here, too
	theconfig.writeConfig(configfile)
	#no logger here: the user needs to read this on console, not in logfile
	print "Default Settings loaded."
	print "Edit "+configfile+" to configure the bot."
	sys.exit(0)

createClassList() #auto create new classlist, if the classlist is removed by the user

# writing PID-File
pidfile=theconfig.getConfig('pidfile',path_pid,'main')
f=open(pidfile,'w')
f.write(str(os.getpid())+"\n")
f.close()


def disconnect():
	corelogger.info("Disconnecting from all networks")
	for i in ipc.getall():
		corelogger.info("Disconnecting from "+i)
		ipc.get(i).disconnect()
	reactor.doIteration(0)

# registering the exithook function
reactor.addSystemEventTrigger('before','shutdown',disconnect)
reactor.addSystemEventTrigger('during','shutdown',exithook)


class InstanceCommunication:
	def __init__(self):
		self.ins={}
		self.logger=logging.getLogger("ipc")
	def add(self,name,inst):
		self.ins[name]=inst
	def rm(self,name):
		del(self.ins[name])
	def get(self,name):
		return self.ins[name]
	def show(self):
		corelogger.info(str(self.ins))
	def getall(self):
		return self.ins
	def connectNetwork(self,network):
		self.logger.info("Trying to connect to "+network)
		if(theconfig.getBoolConfig('enabled', 'unset', 'main', network)):
			f = BotFactory(network, self, theconfig, classes)
			servername=theconfig.getConfig("server", "localhost", "main", network)
			if (theconfig.getBoolConfig('ssl','False','main',network)):
				s = ssl.ClientContextFactory()
				reactor.connectSSL(servername, int(theconfig.getConfig('port','6697','main',network)), f,s)
			else:
				reactor.connectTCP(servername, int(theconfig.getConfig('port','6667','main',network)), f)
		
ipc=InstanceCommunication()

for network in theconfig.getNetworks():
	ipc.connectNetwork(network)
reactor.run()
