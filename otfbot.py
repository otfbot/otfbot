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

from twisted.application import service
from twisted.python import usage

from globalModules.ircClientService import ircClientService
from configService import configService

#logging
import logging, logging.handlers
import log as otfbotlog
from twisted.python import log
import logging, sys


class pythonToTwistedLoggingHandler(logging.Handler):
	def emit(self, record):
		log.msg(record.getMessage())

# Setup Logging
#path_log="otfbot.log"
#path_errorlog="otfbot.err"
# logging to logfile
#debuglevel=0
#filelogger = logging.handlers.RotatingFileHandler(path_log,'a',1048576,5)
#memorylogger = logging.handlers.MemoryHandler(1000)
#errorlogger = logging.handlers.RotatingFileHandler(path_errorlog,'a',1048576,5)
#errorlogger.setLevel(logging.ERROR)
logging.getLogger('').setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
#filelogger.setFormatter(formatter)
#errorlogger.setFormatter(formatter)
#memorylogger.setFormatter(formatter)
#logging.getLogger('').addHandler(filelogger)
#logging.getLogger('').addHandler(errorlogger)
#logging.getLogger('').addHandler(memorylogger)
logging.getLogger('').addHandler(pythonToTwistedLoggingHandler())

#if debuglevel > 0:
	# logging to stdout
#console = logging.StreamHandler()
#logging.getLogger('').setLevel(debuglevel)
#console.setFormatter(formatter)
#logging.getLogger('').addHandler(console)
#corelogger = logging.getLogger('core')
#corelogger.info("  ___ _____ _____ ____        _   ")
#corelogger.info(" / _ \_   _|  ___| __ )  ___ | |_ ")
#corelogger.info("| | | || | | |_  |  _ \ / _ \| __|")
#corelogger.info("| |_| || | |  _| | |_) | (_) | |_ ")
#corelogger.info(" \___/ |_| |_|   |____/ \___/ \__|")
#corelogger.info("")
#svnrevision="$Revision$".split(" ")[1] #TODO: this is only updated, when otfbot.py is updated
# get messages from twisted as well
#plo=otfbotlog.PythonLoggingObserver()
#plo.start()

class Options(usage.Options):
	    optParameters = [["config","c","otfbot.yaml","Location of configfile"]]

#config = Options()
#try:
#    config.parseOptions() # When given no argument, parses sys.argv[1:]
#except usage.UsageError, errortext:
#    print '%s: %s' % (sys.argv[0], errortext)
#    print '%s: Try --help for usage details.' % (sys.argv[0])
#    sys.exit(1)

sys.path.insert(1,"globalModules/ircServerModules")
config={}
config['config']="otfbot.yaml"

application=service.Application("otfbot")
configService(config['config']).setServiceParent(application)
irc=ircClientService()
irc.setServiceParent(application)

from twisted.conch import manhole_tap
manholeService=manhole_tap.makeService({'telnetPort':'7777','sshPort':None,'passwd':'/home/robert/frickelei/otfbot/Otfbot/passwd', 'namespace':{'app':irc}})
manholeService.setName("manhole")
manholeService.setServiceParent(application)