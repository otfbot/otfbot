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

MODE_CHARS = {
    ' ': 0,
    'v': 1,
    'h': 2,
    'o': 4,
    'a': 8,
    'q': 16
}
MODE_SIGNS={
    0: ' ',
    1: '+',
    2: 'h',
    4: '@',
    8: '!',
    16: '&'
}
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
        self.channels = set()
        self.modes = {} #dict channel -> modes

    def getBotuser(self):
        return self.avatar

    def setBotuser(self, avatar):
        self.avatar = avatar

    def hasBotuser(self):
        return self.avatar != None

    def setNick(self, nick):
        self.nick = nick

    def setChannels(self, channels):
        """ set the channels list to the set given as parameter
            @ivar channels: the channellist
        """
        self.channels = set([channel.lower() for channel in channels])
        for channel in channels:
            self.modes[channel]=0

    def getChannels(self):
        """ get the channels list """
        return self.channels

    def addChannel(self, channel):
        """ add a channel to the list of channels of the user
            @ivar channel: the channel to add
        """
        assert type(channel) == str
        self.channels.add(channel.lower())
        self.modes[channel]=0

    def hasChannel(self, channel):
        return channel.lower() in self.channels

    def removeChannel(self, channel):
        """ remove a channel from the list of channels
            @ivar channel: the channel to remove
        """
        channel=channel.lower()
        assert(channel in self.channels)
        self.channels.remove(channel)
        self.modes.remove(channel)

    def setMode(self, channel, modechar):
        """ set the usermode specified by the char modchar on channel
            @ivar channel: the channel where the mode is set
            @ivar modechar: the char corrosponding to the mode (i.e. "o")
        """
        channel=channel.lower()
        assert(channel in self.channels)
        assert(modechar in MODE_CHARS)
        assert(channel in self.modes)
        self.modes[channel]=self.modes[channel] | MODE_CHARS[modechar]

    def removeMode(self, channel, modechar):
        """ remove the usermode specified by the char modchar on channel
            @ivar channel: the channel where the mode is removed
            @ivar modechar: the char corrosponding to the mode (i.e. "o")
        """
        channel=channel.lower()
        assert(channel in self.channels)
        assert(modechar in MODE_CHARS)
        self.modes[channel]=self.modes ^ MODE_CHARS[modechar]

    def getModeSign(self, channel):
        channel=channel.lower()
        assert(channel in self.channels)
        ret_sign=""
        for sign in MODE_SIGNS:
            if self.modes[channel] & sign: #signs are ASCENDING in importance
                ret_sign=MODE_SIGNS[sign]
        return ret_sign


    def getHostMask(self):
        return self.nick + "!" + self.user + "@" + self.host

    def __repr__(self):
        return "<IrcUser %s (%s)>" % (self.getHostMask(), self.name)
