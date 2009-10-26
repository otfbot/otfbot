#!/usr/bin/twistd -noy
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
import twisted

from services import config as configService

#logging
import logging, logging.handlers
from twisted.python import log
import logging, sys

#svnrevision=int("$Revision$".split(" ")[1]) #TODO: this is only updated, when otfbot.py is updated
svnrevision=0 # TODO: Move to git

# TODO: Move to git
#try:
#    # Try to determine the current version dynamically
#    import pysvn, os.path
#    wcpath=os.path.dirname(os.path.abspath(__file__))
#    client = pysvn.Client()
#    entry = client.info(wcpath)
#    svnrevision=entry.revision.number
#except:
#    pass

class Options(usage.Options):
        optParameters = [["config","c","otfbot.yaml","Location of configfile"]]

#config = Options()
#try:
#    config.parseOptions() # When given no argument, parses sys.argv[1:]
#except usage.UsageError, errortext:
#    print '%s: %s' % (sys.argv[0], errortext)
#    print '%s: Try --help for usage details.' % (sys.argv[0])
#    sys.exit(1)

configfilename="otfbot.yaml"

application=service.Application("otfbot")
application.getServiceNamed=service.IServiceCollection(application).getServiceNamed
application.version = "SVN revision "+str(svnrevision)

configS=configService.loadConfig(configfilename, "plugins/*/*.yaml")
if not configS:
    print "please run helpers/generateconfig.py"
    sys.exit(1)
configS.setServiceParent(application)

################################################################################
## Begin of logging setup

logging.getLogger('').setLevel(logging.DEBUG)
root=logging.getLogger('')

formatPattern = configS.get("format", '%(asctime)s %(name)-10s %(module)-14s %(funcName)-20s %(levelname)-8s %(message)s', "logging")
formatter = logging.Formatter(formatPattern)

logfile = configS.get("file", False, "logging")
if logfile:
    filelogger = logging.handlers.RotatingFileHandler(logfile,'a',1048576,5)
    filelogger.setFormatter(formatter)
    root.addHandler(filelogger)
errfile = configS.get("errfile", False, "logging")
if errfile:        
    errorlogger = logging.handlers.RotatingFileHandler(errfile,'a',1048576,5)
    errorlogger.setFormatter(formatter)
    errorlogger.setLevel(logging.ERROR)
    root.addHandler(errorlogger)
memorylogger = logging.handlers.MemoryHandler(1000)
memorylogger.setFormatter(formatter)
root.addHandler(memorylogger)
stdout = configS.get("logToConsole", True, "logging")
if stdout:
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

plo = log.PythonLoggingObserver()
if twisted.version.minor >= 2:
    log.startLoggingWithObserver(plo.emit, stdout)
else:
    plo.start()

corelogger = logging.getLogger('core')

## end of logging setup
################################################################################

corelogger.info("  ___ _____ _____ ____        _   ")
corelogger.info(" / _ \_   _|  ___| __ )  ___ | |_ ")
corelogger.info("| | | || | | |_  |  _ \ / _ \| __|")
corelogger.info("| |_| || | |  _| | |_) | (_) | |_ ")
corelogger.info(" \___/ |_| |_|   |____/ \___/ \__|")
corelogger.info("    bleeding edge from SVN rev %3i" % svnrevision)

service_names=configS.get("services", [], "main")
service_classes=[]
service_instances=[]
for service_name in service_names:
    corelogger.info("starting Service %s" % service_name)
    service_classes.append(__import__("services."+service_name, fromlist=['botService']))
    service_instances.append(service_classes[-1].botService(application, application))
    service_instances[-1].setServiceParent(application)
