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

"""OTFBot"""

import os, sys, atexit
from twisted.internet import reactor, ssl
sys.path.insert(1,"lib") # Path for auxilary libs of otfbot
import functions, config
from botfactory import BotFactory
import cmdlineparser

#logging
import logging
import logging.handlers
from twisted.python import log
import log as otfbotlog

def main():
	# some constants for paths, might be read from configfile in future
	path_cfg="etc/otfbot.yaml"
	path_mods="modules"

	###############################################################################
	# Parse commandline options
	(options, args) = cmdlineparser.parse()
	###############################################################################
	# config
	theconfig=None
	if options.configfile != None:
		configfile=options.configfile
	else:
		configfile=path_cfg
	modulesconfigdir=path_mods #TODO: configuration-option(?)
	theconfig=config.loadConfig(configfile, modulesconfigdir)
	new_config=False
	if not theconfig: #file could not be loaded, i.e at first start
		theconfig=config.config()
		theconfig.set('enabled', 'false', 'main', 'samplenetwork')
		theconfig.set('server', 'localhost', 'main', 'samplenetwork')
		theconfig.set('enabled', 'false', 'main', 'samplenetwork', '#example')
		theconfig.set('nickname', 'OtfBot', 'main')
		theconfig.set('encoding', 'UTF-8', 'main')
		#theconfig.set('pidfile','otfbot.pid','main')
			
		new_config=True

	###############################################################################
	# some settings
	path_log=theconfig.getConfig("logfile", "otfbot.log", "main")
	path_errorlog=theconfig.getConfig("errorlog", "error.log", "main")
	path_pid=theconfig.getConfig("pidfile", "otfbot.pid", "main")
	path_data=theconfig.getConfig("datadir", "data", "main")
	###############################################################################
	# Setup Logging

	# logging to logfile
	filelogger = logging.handlers.RotatingFileHandler(path_log,'a',1048576,5)
	errorlogger = logging.handlers.RotatingFileHandler(path_errorlog,'a',1048576,5)
	errorlogger.setLevel(logging.ERROR)
	#filelogger = logging.FileHandler(path_log,'a')
	logging.getLogger('').setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
	filelogger.setFormatter(formatter)
	errorlogger.setFormatter(formatter)
	logging.getLogger('').addHandler(filelogger)
	logging.getLogger('').addHandler(errorlogger)
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
	# Load modules
	classes=[]
	# Path for bot-modules
	sys.path.insert(1,path_mods)
	for file in os.listdir(path_mods):
		if len(file)>=3 and file[-3:]==".py":
			classes.append(__import__(file[:-3]))
			#classes[-1].datadir = "modules/"+classes[-1].__name__+"-data"
			classes[-1].datadir = path_data+"/"+classes[-1].__name__
			corelogger.debug("Loading module "+classes[-1].__name__)
	###############################################################################

	createClassList(theconfig, classes) #auto create new classlist, if the classlist is removed by the user or on new config
	theconfig.writeConfig(configfile) #mostly needed for new configs

	if new_config:
		#no logger here: the user needs to read this on console, not in logfile
		print "Default Settings loaded."
		print "Edit "+configfile+" to configure the bot."
		sys.exit(0)


	# writing PID-File
	pidfile=path_pid
	f=open(pidfile,'w')
	f.write(str(os.getpid())+"\n")
	f.close()
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

	ipc=InstanceCommunication(theconfig, classes)

	###############################################################################
	# registering the exithook function
	reactor.addSystemEventTrigger('before','shutdown',disconnect, ipc, corelogger)
	reactor.addSystemEventTrigger('during','shutdown',exithook, theconfig, pidfile, configfile, corelogger)


	for network in theconfig.getNetworks():
		ipc.connectNetwork(network)
	reactor.run()

###############################################################################

def exithook(theconfig, pidfile, configfile, corelogger):
	""" This function is called, when the program terminates. """
	# remove Pidfile
	os.remove(pidfile)
	theconfig.writeConfig(configfile)
	corelogger.info("Bot shutted down")
	corelogger.info("-------------------------")


def createClassList(theconfig, classes):
	if theconfig.hasConfig("modsEnabled", "main")[0]==False: #TODO: how to handle if only classes have module-lists?
		theconfig.set("modsEnabled", [i.__name__ for i in classes], "main")



def disconnect(ipc, corelogger):
	corelogger.info("Disconnecting from all networks")
	for i in ipc.getall():
		corelogger.info("Disconnecting from "+i)
		ipc.get(i).disconnect()
	reactor.doIteration(0)


class InstanceCommunication:
	def __init__(self, theconfig, classes):
		self.ins={}
		self.theconfig=theconfig
		self.logger=logging.getLogger("ipc")
		self.classes=classes
	def add(self,name,inst):
		self.ins[name]=inst
	def rm(self,name):
		del(self.ins[name])
	def get(self,name):
		return self.ins[name]
	def __getitem__(self, name):
		return self.ins[name]
	def show(self):
		corelogger.info(str(self.ins))
	def getall(self):
		return self.ins
	def connectNetwork(self, network):
		if(self.theconfig.getBoolConfig('enabled', 'unset', 'main', network)):
			self.logger.info("Trying to connect to "+network)
			f = BotFactory(network, self, self.theconfig, self.classes)
			servername=self.theconfig.getConfig("server", "localhost", "main", network)
			if (self.theconfig.getBoolConfig('ssl','False','main',network)):
				s = ssl.ClientContextFactory()
				reactor.connectSSL(servername, int(self.theconfig.getConfig('port','6697','main',network)), f,s)
			else:
				reactor.connectTCP(servername, int(self.theconfig.getConfig('port','6667','main',network)), f)
if __name__=="__main__":
	main()
