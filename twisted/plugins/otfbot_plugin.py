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
# (c) 2005 - 2010 by Alexander Schier
# (c) 2006 - 2010 by Robert Weidlich
# 

from twisted.application import internet, service
from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python import log, usage
import twisted

from zope.interface import implements

import logging, logging.handlers, sys

from otfbot.lib import version
from otfbot.services import config as configService

class Options(usage.Options):
    optParameters = [["config","c","otfbot.yaml","Location of configfile"]]

class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "otfbot"
    description = "OtfBot - The friendly Bot"
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in myproject.
        """

        application = service.MultiService()
        application.version=version._version
        
        configS=configService.loadConfig(options['config'], "plugins/*/*.yaml")
        if not configS:
            print "please run twistd gen-otfbot-config"
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
        if twisted.version.minor > 2:
            log.startLoggingWithObserver(plo.emit)
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
        _v="version %s" % application.version.short()
        corelogger.info(" "*(34-len(_v))+_v)

        service_names=configS.get("services", [], "main")
        service_classes=[]
        service_instances=[]
        for service_name in service_names:
            #corelogger.info("starting Service %s" % service_name)
            service_classes.append(__import__("otfbot.services."+service_name, fromlist=['botService']))
            service_instances.append(service_classes[-1].botService(application, application))
            service_instances[-1].setServiceParent(application)

        return application

serviceMaker = MyServiceMaker()