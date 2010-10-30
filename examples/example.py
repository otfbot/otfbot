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
# # (c) 2009 - 2010 by Robert Weidlich
#

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

""" an example for a plugin for the ircClient """


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    @callback
    def joined(self, channel):
        self.logger.debug('Callback joined called with channel=' +
            repr(channel) + '.')

    @callback
    def command(self, user, channel, command, options):
        self.logger.debug('Callback command called with user=' + repr(user) +
            ' channel=' + repr(channel) + ' command=' + repr(command) +
            ' options=' + repr(options) + '.')
        self.bot.sendmsg(channel, "Command " +
            repr(command) + " with args " + repr(options))

    @callback
    def query(self, user, channel, msg):
        self.logger.debug('Callback query called with user=' + repr(user) +
            ' channel=' + repr(channel) + ' msg=' + repr(msg) + '.')

    @callback
    def msg(self, user, channel, msg):
        self.logger.debug('Callback msg called with user=' + repr(user)
            + ' channel=' + repr(channel) + ' msg=' + repr(msg) + '.')

    def connectionMade(self):
        self.logger.debug('Callback connectionMade called with.')

    @callback
    def connectionLost(self, reason):
        self.logger.debug('Callback connectionLost called with reason='
            + repr(reason) + '.')

    @callback
    def signedOn(self):
        self.logger.debug('Callback signedOn called with.')

    @callback
    def left(self, channel):
        self.logger.debug('Callback left called with channel='
            + repr(channel) + '.')

    @callback
    def noticed(self, user, channel, msg):
        self.logger.debug('Callback noticed called with user=' + repr(user)
            + ' channel=' + repr(channel) + ' msg=' + repr(msg) + '.')

    @callback
    def action(self, user, channel, msg):
        self.logger.debug('Callback action called with user=' + repr(user) +
            ' channel=' + repr(channel) + ' msg=' + repr(msg) + '.')

    @callback
    def modeChanged(self, user, channel, set, modes, args):
        self.logger.debug('Callback modeChanged called with user=' + repr(user)
            + ' channel=' + repr(channel) + ' set=' + repr(set) + ' modes='
            + repr(modes) + ' args=' + repr(args) + '.')

    @callback
    def kickedFrom(self, channel, kicker, message):
        self.logger.debug('Callback kickedFrom called with channel=' +
            repr(channel) + ' kicker=' + repr(kicker) + ' message=' +
            repr(message) + '.')

    @callback
    def userKicked(self, kickee, channel, kicker, message):
        self.logger.debug('Callback userKicked called with kickee='
            + repr(kickee) + ' channel=' + repr(channel) + ' kicker='
            + repr(kicker) + ' message=' + repr(message) + '.')

    @callback
    def userJoined(self, user, channel):
        self.logger.debug('Callback userJoined called with user='
            + repr(user) + ' channel=' + repr(channel) + '.')

    @callback
    def userJoinedMask(self, user, channel):
        self.logger.debug('Callback userJoinedMask called with user='
            + repr(user) + ' channel=' + repr(channel) + '.')

    @callback
    def userLeft(self, user, channel):
        self.logger.debug('Callback userLeft called with user=' + repr(user)
            + ' channel=' + repr(channel) + '.')

    @callback
    def userQuit(self, user, quitMessage):
        self.logger.debug('Callback userQuit called with user=' + repr(user)
            + ' quitMessage=' + repr(quitMessage) + '.')

    @callback
    def yourHost(self, info):
        self.logger.debug('Callback yourHost called with info=' +
            repr(info) + '.')

    @callback
    def userRenamed(self, oldname, newname):
        self.logger.debug('Callback userRenamed called with oldname='
            + repr(oldname) + ' newname=' + repr(newname) + '.')

    @callback
    def topicUpdated(self, user, channel, newTopic):
        self.logger.debug('Callback topicUpdated called with user='
            + repr(user) + ' channel=' + repr(channel)
            + ' newTopic=' + repr(newTopic) + '.')

    @callback
    def irc_unknown(self, prefix, command, params):
        self.logger.debug('Callback irc_unknown called with prefix='
            + repr(prefix) + ' command=' + repr(command) + ' params='
            + repr(params) + '.')

    @callback
    def stop(self):
        self.logger.debug('Callback stop called.')

    @callback
    def reload(self):
        self.logger.debug('Callback reload called.')

    @callback
    def start(self):
        self.logger.debug('Callback start called.')

    @callback
    def sendLine(self, line):
        self.logger.debug('Callback sendLine called with line='
            + repr(line) + '.')

    @callback
    def lineReceived(self, line):
        self.logger.debug('Callback lineReceived called with line='
            + repr(line) + '.')

    @callback
    def ctcpQuery(self, user, channel, messages):
        self.logger.debug('Callback ctcpQuery called with user=' + repr(user)
            + ' channel=' + repr(channel) + ' messages='
            + repr(messages) + '.')
