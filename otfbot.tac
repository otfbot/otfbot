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

from services import config as configService

#logging
import logging, logging.handlers
from twisted.python import log
import logging, sys


#class pythonToTwistedLoggingHandler(logging.Handler):
#    def emit(self, record):
#        log.msg(record.getMessage())

logfile="otfbot.log"
errfile="otfbot.err"
stdout=True

formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')

filelogger = logging.handlers.RotatingFileHandler(logfile,'a',1048576,5)
filelogger.setFormatter(formatter)        
errorlogger = logging.handlers.RotatingFileHandler(errfile,'a',1048576,5)
errorlogger.setFormatter(formatter)
memorylogger = logging.handlers.MemoryHandler(1000)
memorylogger.setFormatter(formatter)
if stdout:
    console = logging.StreamHandler()
    console.setFormatter(formatter)

logging.getLogger('').setLevel(logging.DEBUG)
errorlogger.setLevel(logging.ERROR)

root=logging.getLogger('')
root.addHandler(filelogger)
root.addHandler(errorlogger)
root.addHandler(memorylogger)
if stdout:
    root.addHandler(console)

plo = log.PythonLoggingObserver()
plo.start()

corelogger = logging.getLogger('core')
corelogger.info("  ___ _____ _____ ____        _   ")
corelogger.info(" / _ \_   _|  ___| __ )  ___ | |_ ")
corelogger.info("| | | || | | |_  |  _ \ / _ \| __|")
corelogger.info("| |_| || | |  _| | |_) | (_) | |_ ")
corelogger.info(" \___/ |_| |_|   |____/ \___/ \__|")
corelogger.info("")
svnrevision="$Revision$".split(" ")[1] #TODO: this is only updated, when otfbot.py is updated

class Options(usage.Options):
        optParameters = [["config","c","otfbot.yaml","Location of configfile"]]

#config = Options()
#try:
#    config.parseOptions() # When given no argument, parses sys.argv[1:]
#except usage.UsageError, errortext:
#    print '%s: %s' % (sys.argv[0], errortext)
#    print '%s: Try --help for usage details.' % (sys.argv[0])
#    sys.exit(1)
#class myApp(service.Application):

configfilename="otfbot.yaml"

application=service.Application("otfbot")
application.getServices=lambda: service.IServiceCollection(application).services
application.getNamedServices=lambda: service.IServiceCollection(application).namedServices
def getNamedService(name):
    try:
        return application.getNamedServices()[name]
    except KeyError:
        return None
application.getNamedService=getNamedService

configS=configService.loadConfig(configfilename, "plugins/*/*.yaml")
if not configS:
    print "please run helpers/generateconfig.py"
    sys.exit(1)
configS.setServiceParent(application)

service_names=configS.get("services", [], "main")
service_classes=[]
service_instances=[]
for service_name in service_names:
    log.msg("starting Service %s" % service_name)
    service_classes.append(__import__("services."+service_name, fromlist=['botService']))
    service_instances.append(service_classes[-1].botService(application, application))
    service_instances[-1].setServiceParent(application)
