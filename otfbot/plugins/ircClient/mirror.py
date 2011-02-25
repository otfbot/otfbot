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
# (c) 2008 by Alexander Schier
#

"""
    Mirror the activities of one channel into another
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback
from otfbot.lib import color


class Plugin(chatMod.chatMod):
    """
        Configuration:
        If you want to mirror channel #a to channel #b then you need to add
        mirror.mirrorto: network-#b
        to the channel configuration of #a  where 'network' is the irc network name.
    """

    def __init__(self, bot):
        self.bot = bot
        self.getbot = lambda network: bot.root.getServiceNamed('ircClient').getServiceNamed(network).protocol
        # the bot is red
        self.colors = ["navy", "green", "brown", "cyan", "teal", "blue", "light_grey", "grey", "pink", "purple"]

    def _sendToMirror(self, channel, message):
        """Send a message to the mirrorChannel of the channel"""
        if (self.network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            (target_network, target_channel) = self.bot.config.get("mirrorto", "unset", "mirror", self.network, channel).split("-", 1)
            ircClient = self.bot.root.getServiceNamed('ircClient')
            if target_network in ircClient.namedServices:
                networkService = ircClient.getServiceNamed(target_network)
                networkService.protocol.sendmsg(target_channel, message)

    @callback
    def msg(self, user, channel, msg):
        nick = user.getNick()
        if nick.lower() == self.bot.nickname.lower():
            nick = color.changecolor("red") + nick + color.resetcolors()
        else:
            nickcolor = self.colors[hash(nick) % len(self.colors)]
            nick = color.changecolor(nickcolor) + nick + color.resetcolors()
        self._sendToMirror(channel, "< %s> %s" % (nick, msg))

    @callback
    def action(self, user, channel, msg):
        self._sendToMirror(channel, "* %s %s " % (user.getNick(), msg))

    @callback
    def kickedFrom(self, channel, kicker, message):
        self._sendToMirror(channel, "%s was kicked from %s by %s [%s]" % (self.bot.nickname, channel, kicker, message))

    @callback
    def userKicked(self, kickee, channel, kicker, message):
        self._sendToMirror(channel, "%s was kicked from %s by %s [%s]" % (kickee, channel, kicker, message))

    @callback
    def userJoined(self, user, channel):
        self._sendToMirror(channel, "%s has joined %s" % (user.getNick(), channel))

    @callback
    def userLeft(self, user, channel):
        self._sendToMirror(channel, "%s has left %s" % (user.getNick(), channel))

    @callback
    def userQuit(self, user, quitMessage):
        for (network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            if self.network == network:
                self._sendToMirror(channel, "%s has quit [%s]" % (user.getNick(). quitMessage))

    @callback
    def userRenamed(self, oldname, newname):
        for (network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            if self.network == network:
                self._sendToMirror(channel, "%s is now known as %s" % (oldname, newname))

    @callback
    def modeChanged(self, user, channel, set, modes, args):
        sign = "+"
        if not set:
            sign = "-"
        self._sendToMirror(channel, "mode/" + channel + " [" + sign + modes + " " + " ".join(args) + "] by " + str(user))

    @callback
    def joined(self, channel):
        self._sendToMirror(channel, "joined %s" % channel)
