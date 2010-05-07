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
# (c) 2008 - 2010 by Alexander Schier
# (c) 2009 - 2010 by Robert Weidlich
#

""" Objects to represent users
"""

from twisted.words import service

import hashlib


class BotUser(service.User):
    """ represents a user of the bot

        @ivar password: Authentification data
        @ivar ircuser: references to IrcUser instances
    """
    password = ""
    ircuser = {}

    def __init__(self, name):
        self.name = name

    def setPasswd(self, passwd):
        self.password = self._hashpw(passwd)

    def checkPasswd(self, passwd):
        return self._hashpw(passwd) == self.password

    def _hashpw(self, pw):
        s = hashlib.sha1(pw)
        return s.hexdigest()

    def __repr__(self):
        return "<BotUser %s>" % self.name


class IrcUser(object):
    """ Represents the connection of a L{BotUser} via IRC

        @ivar network: reference to the network over which
                        the user is connected
        @ivar name:    verbose name of this connection
        @ivar nick:    IRC nick
        @ivar user:    user part of the hostmask
        @ivar host:    host part of the hostmask
        @ivar avatar:  reference to the corresponding L{BotUser}
                       instance
        @ivar realname: content of the realname property of the user
    """

    def __init__(self, nick, user, host, realname, network):
        self.network = network
        self.name = "anonymous"
        self.nick = nick
        self.user = user
        self.host = host
        self.avatar = None
        self.realname = realname

    def getBotuser(self):
        return self.avatar

    def hasBotuser(self):
        return self.avatar != None

    def getHostMask(self):
        return self.nick + "!" + self.user + "@" + self.host

    def __repr__(self):
        return "<IrcUser %s (%s)>" % (self.getHostMask(), self.name)
