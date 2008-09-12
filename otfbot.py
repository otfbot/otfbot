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

import os, sys
from twisted.internet import reactor, ssl
sys.path.insert(1,"lib") # Path for auxilary libs of otfbot
import functions, cmdlineparser
import config as otfbotconfig
from botfactory import BotFactory

#logging
import logging, logging.handlers
import log as otfbotlog

class otfbot:
	def __init__(self):
		# some constants for paths, might be read from configfile in future
		self.path_cfg="otfbot.yaml"
		self.path_mods="modules"
	def detach(self):
		try:
			import subprocess
			subprocess.Popen(["python",sys.argv[0],"-f"])
			sys.exit(0)
		except ImportError:
			pass
	def loadConfig(self, configfile=None):
		self.config=None
		if configfile != None:
			self.configfile=configfile
		else:
			self.configfile=self.path_cfg
		modulesconfigdir=self.path_mods #TODO: configuration-option(?)
		self.config=otfbotconfig.loadConfig(self.configfile, modulesconfigdir)
		self.new_config=False
		if not self.config: #file could not be loaded, i.e at first start
			self.config=otfbotconfig.config(self.configfile)
			self.config.set('enabled', False, 'main', 'samplenetwork')
			self.config.set('server', 'localhost', 'main', 'samplenetwork')
			self.config.set('enabled', False, 'main', 'samplenetwork', '#example')
			self.config.set('nickname', 'OtfBot', 'main')
			self.config.set('encoding', 'UTF-8', 'main')
			#self.config.set('pidfile','otfbot.pid','main')
				
			self.new_config=True
	def setupLogging(self, debuglevel=0):
		# logging to logfile
		self.filelogger = logging.handlers.RotatingFileHandler(self.path_log,'a',1048576,5)
		self.memorylogger = logging.handlers.MemoryHandler(1000)
		self.errorlogger = logging.handlers.RotatingFileHandler(self.path_errorlog,'a',1048576,5)
		self.errorlogger.setLevel(logging.ERROR)
		logging.getLogger('').setLevel(logging.DEBUG)
		self.formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
		self.filelogger.setFormatter(self.formatter)
		self.errorlogger.setFormatter(self.formatter)
		self.memorylogger.setFormatter(self.formatter)
		logging.getLogger('').addHandler(self.filelogger)
		logging.getLogger('').addHandler(self.errorlogger)
		logging.getLogger('').addHandler(self.memorylogger)

		if debuglevel > 0:
			# logging to stdout
			console = logging.StreamHandler()
			logging.getLogger('').setLevel(debuglevel)
			console.setFormatter(self.formatter)
			logging.getLogger('').addHandler(console)
		self.corelogger = logging.getLogger('core')
		self.corelogger.info("  ___ _____ _____ ____        _   ")
		self.corelogger.info(" / _ \_   _|  ___| __ )  ___ | |_ ")
		self.corelogger.info("| | | || | | |_  |  _ \ / _ \| __|")
		self.corelogger.info("| |_| || | |  _| | |_) | (_) | |_ ")
		self.corelogger.info(" \___/ |_| |_|   |____/ \___/ \__|")
		self.corelogger.info("")
		self.svnrevision="$Revision$".split(" ")[1] #TODO: this is only updated, when otfbot.py is updated
		self.corelogger.info("Starting OtfBot - Version svn "+self.svnrevision)
		# get messages from twisted as well
		plo=otfbotlog.PythonLoggingObserver()
		plo.start()
	def loadPaths(self):
		self.path_log=self.config.getConfig("logfile", "otfbot.log", "main", set_default=False)
		self.path_errorlog=self.config.getConfig("errorlog", "error.log", "main", set_default=False)
		self.path_pid=self.config.getConfig("pidfile", "otfbot.pid", "main", set_default=False)
		self.path_data=self.config.getConfig("datadir", "data", "main", set_default=False)
	def loadModuleClasses(self):
		sys.path.insert(1, self.path_mods)
		files = sorted(os.listdir(self.path_mods))
		for file in files:
			if len(file)>=3 and file[-3:]==".py":
				#TODO: this in bot.startMod(s)?
				self.classes.append(__import__(file[:-3]))
				self.classes[-1].datadir = self.path_data+"/"+self.classes[-1].__name__
				self.corelogger.debug("Loading module "+self.classes[-1].__name__)
	def checkUser(self, options):
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
	def writePidfile(self):
		# writing PID-File
		self.pidfile=self.path_pid
		f=open(self.pidfile,'w')
		f.write(str(os.getpid())+"\n")
		f.close()
	def main(self):

		###############################################################################
		# Parse commandline options
		(options, args) = cmdlineparser.parse()

		# Detaching from console
		if options.foreground == False and not options.debug > 0:
			self.detach()

		self.checkUser(options)
		# config
		self.loadConfig(options.configfile)

		# some settings
		self.loadPaths()

		# Setup Logging
		self.setupLogging(options.debug)

		# Load modules
		self.classes=[]
		# Path for bot-modules
		self.loadModuleClasses()

		self.createClassList(self.classes) #auto create new classlist, if the classlist is removed by the user or on new config
		self.config.writeConfig() #mostly needed for new configs

		if self.new_config:
			#no logger here: the user needs to read this on console, not in logfile
			print "Default Settings loaded."
			print "Edit "+self.configfile+" to configure the bot."
			sys.exit(0)

		self.ipc=InstanceCommunication(self)

		self.writePidfile()

		# registering the exithook function
		reactor.addSystemEventTrigger('before','shutdown',self.disconnect)
		reactor.addSystemEventTrigger('during','shutdown',self.exithook)

		for network in self.config.getNetworks():
			self.ipc.connectNetwork(network)
		reactor.run()

	def exithook(self):
		""" This function is called, when the program terminates. """
		# remove Pidfile
		os.remove(self.pidfile)
		self.config.writeConfig()
		self.corelogger.info("Bot shutted down")
		self.corelogger.info("-------------------------")


	def createClassList(self, classes):
		if self.config.hasConfig("modsEnabled", "main")[0]==False: #TODO: how to handle if only classes have module-lists?
			self.config.set("modsEnabled", [i.__name__ for i in classes], "main")

	def disconnect(self):
		self.corelogger.info("Disconnecting from all networks")
		for i in self.ipc.getall():
			self.corelogger.info("Disconnecting from "+i)
			self.ipc.get(i).disconnect()
		reactor.doIteration(0)


class InstanceCommunication:
	def __init__(self, otfbot):
		self.ins={}
		self.config=otfbot.config
		self.logger=logging.getLogger("ipc")
		self.classes=otfbot.classes
		self.otfbot=otfbot
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
		if(self.config.getBoolConfig('enabled', 'unset', 'main', network)):
			self.logger.info("Trying to connect to "+network)
			f = BotFactory(network, self)
			servername=self.config.getConfig("server", "localhost", "main", network)
			if (self.config.getBoolConfig('ssl','False','main',network)):
				s = ssl.ClientContextFactory()
				reactor.connectSSL(servername, int(self.config.getConfig('port','6697','main',network)), f,s)
			else:
				reactor.connectTCP(servername, int(self.config.getConfig('port','6667','main',network)), f)
if __name__=="__main__":
	bot=otfbot()
	bot.main()
