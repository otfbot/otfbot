# This file is part of OtfBot.
#
# OtfBot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OtfBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OtfBot; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
# (c) 2009 Robert Weidlich
#

from twisted.application import internet, service
from twisted.internet import protocol, reactor, error
from twisted.cred import portal, checkers
from twisted.words.service import InMemoryWordsRealm
from lib.bot import Bot
import logging

class botService(service.MultiService, portal.Portal):
    name="auth"
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        service.MultiService.__init__(self)
        # TODO: write a custom Realm
        portal.Portal.__init__(self, InMemoryWordsRealm("blub"))
    def startService(self):
        self.config=self.root.getNamedServices()['config']
        # checker hinzufuegen
        pwdb = checkers.FilePasswordDB(self.config.get("datadir","data")+"/passwd.txt",cache=True)
        self.registerChecker(pwdb,*pwdb.credentialInterfaces)
        service.Service.startService(self)
    def getCheckers(self):
        return self.checkers;