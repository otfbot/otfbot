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
from twisted.internet import protocol, reactor, defer
from twisted.cred import portal, checkers, credentials, error
from twisted.words.service import WordsRealm, InMemoryWordsRealm

from zope.interface import implements

from otfbot.lib.user import BotUser

import logging, yaml, hashlib


class YamlWordsRealm(InMemoryWordsRealm):
    implements(checkers.ICredentialsChecker)   
    credentialInterfaces = (
        credentials.IUsernamePassword,
    )
    
    def __init__(self, name, file):
        super(YamlWordsRealm, self).__init__(name)
        self.file=file
        reactor.callInThread(self.load)
            
    def userFactory(self, name):
        return BotUser(name)

    def addUser(self, user):
        super(YamlWordsRealm, self).addUser(user)
        reactor.callInThread(self.save)
   
    def addGroup(self, group):
        super(YamlWordsRealm, self).addGroup(user)
        reactor.callInThread(self.save)        

    def requestAvatarId(self, creds):
        u = self.getUser(unicode(creds.username))
        u.addErrback(error.UnauthorizedLogin)
        u.addCallback(self._checkpw, creds)
        return u

    def requestAvatar(self, avatarId, mind, *interfaces):
        if isinstance(avatarId, str):
            avatarId = avatarId.decode(self._encoding)

        def gotAvatar(avatar):
            #if avatar.realm is not None:
            #    raise ewords.AlreadyLoggedIn()
            for iface in interfaces:
                facet = iface(avatar, None)
                if facet is not None:
                    avatar.loggedIn(self, mind)
                    mind.name = avatarId
                    mind.realm = self
                    mind.avatar = avatar
                    return iface, facet, self.logoutFactory(avatar, facet)
            raise NotImplementedError(self, interfaces)

        return self.getUser(avatarId).addCallback(gotAvatar)

    def _checkpw(self, user, creds):
        up = credentials.IUsernamePassword(creds)
        if user.checkPasswd(up.password):
            return defer.succeed(user.name)
        else:
            return defer.fail(error.UnauthorizedLogin())

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
        self.checkers={}
        # TODO: write a custom Realm        

    def startService(self):
        print "auth service started"
        self.config=self.root.getServiceNamed('config')
        self.realm = YamlWordsRealm("userdb",self.config.get("datadir","data")+"/userdb.yaml")
        portal.Portal.__init__(self, self.realm)
        # checker hinzufuegen
        #pwdb = checkers.FilePasswordDB(self.config.get("datadir","data")+"/passwd.txt",cache=True)
        #self.registerChecker(pwdb,*pwdb.credentialInterfaces)
        self.registerChecker(self.realm,*self.realm.credentialInterfaces)
        service.Service.startService(self)

    def getCheckers(self):
        return self.checkers

