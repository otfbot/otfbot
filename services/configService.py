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
# (c) 2008 by Robert Weidlich
# 

from twisted.application import internet, service
from lib.botfactory import BotFactory
import lib.config as otfbotconfig

class configService(service.Service):
    def __init__(self, filename):
        self.filename=filename
        self.config=None
        self.name="config"

    def startService(self):
        service.Service.startService(self)
        self.config=otfbotconfig.loadConfig(self.filename, "data")
        self.delConfig=self.config.delConfig
        self.getConfig=self.config.getConfig
        self.hasConfig=self.config.hasConfig
        self.getPathConfig=self.config.getPathConfig
        self.setConfig=self.config.setConfig
        self.getBoolConfig=self.config.getBoolConfig        
        self.getNetworks=self.config.getNetworks
        self.getChannels=self.config.getChannels

    def stopService(self):
        self.config.writeConfig()
        service.Service.stopService(self)
