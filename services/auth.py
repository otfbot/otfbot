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
from twisted.words.service import WordsRealm, InMemoryWordsRealm

from lib.User import IrcUser

import logging, yaml


class YamlWordsRealm(InMemoryWordsRealm):
    def __init__(self, name, file):
        super(YamlWordsRealm, self).__init__(name)
        self.file=file
        reactor.callInThread(self.load)
            
    def userFactory(self, name):
        return IrcUser(name+"!user@host")

    def addUser(self, user):
        print "adding user"
        super(YamlWordsRealm, self).addUser(user)
        reactor.callInThread(self.save)
   
    def addGroup(self, group):
        super(YamlWordsRealm, self).addGroup(user)
        reactor.callInThread(self.save)        

    def save(self):
        file=open(self.file, "w")
        file.write(yaml.dump_all([self.users,self.groups], default_flow_style=False))
        file.close()
        
    def load(self):
        try:
            f=open(self.file, "r")
            file_h=yaml.load_all(f)
            self.users=file_h.next()
            self.groups=file_h.next()
            f.close()
        except IOError:
            self.users={}
            self.groups={}

class botService(service.MultiService, portal.Portal):
    name="auth"
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        service.MultiService.__init__(self)
        # TODO: write a custom Realm        

    def startService(self):
        print "auth service started"
        self.config=self.root.getNamedServices()['config']
        portal.Portal.__init__(self, YamlWordsRealm("userdb",self.config.get("datadir","data")+"/userdb.yaml"))        
        # checker hinzufuegen
        pwdb = checkers.FilePasswordDB(self.config.get("datadir","data")+"/passwd.txt",cache=True)
        self.registerChecker(pwdb,*pwdb.credentialInterfaces)
        service.Service.startService(self)

    def getCheckers(self):
        return self.checkers
