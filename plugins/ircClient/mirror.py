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

import random, re
from lib import chatMod

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.getbot=lambda network: bot.root.getServiceNamed('ircClient').getServiceNamed(network).protocol
        #x034 (red) is the bot
        self.colors=["\x032", "\x033", "\x035", "\x0311", "\x0310", "\x0312", "\x0315", "\x0314", "\x0316", "\x0313", "\x036"]

    def _sendToMirror(self, channel, message):
        if (self.network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            (target_network, target_channel)=self.bot.config.get("mirrorto", "unset", "mirror", self.network, channel).split("-", 1)
            ircClient=self.bot.root.getServiceNamed('ircClient')
            if ircClient.namedServices.has_key(target_network):
                networkService=ircClient.getServiceNamed(target_network)
                networkService.protocol.sendmsg(target_channel, message)


    def msg(self, user, channel, msg):
        nick=user.split("!")[0]
        if nick.lower()==self.bot.nickname.lower():
            nick="\x034%s\x0F"%nick
        else:
            color=self.colors[hash(nick)%len(self.colors)]
            nick="%s%s\x0F"%(color, nick)
        self._sendToMirror(channel, "< %s> %s"%(nick,msg))
    def action(self, user, channel, msg):
        self._sendToMirror(channel, "* %s %s "%(user.split("!")[0], msg))
    def kickedFrom(self, channel, kicker, message):
        self._sendToMirror(channel, "%s was kicked from %s by %s [%s]"%(self.bot.nickname, channel, kicker, message))
    def userKicked(self, kickee, channel, kicker, message):
        self._sendToMirror(channel, "%s was kicked from %s by %s [%s]"%(kickee, channel, kicker, message))
    def userJoined(self, user, channel):
        self._sendToMirror(channel, "%s has joined %s"%(user.split("!")[0], channel))
    def userLeft(self, user, channel):
        self._sendToMirror(channel, "%s has left %s"%(user.split("!")[0], channel))
    def userQuit(self, user, quitMessage):
        for (network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            if self.network == network:
                self._sendToMirror(channel, "%s has quit [%s]"%(user.split("!")[0], quitMessage))
    def userRenamed(self, oldname, newname):
        for (network, channel) in self.bot.config.has("mirrorto", "mirror")[2]:
            if self.network == network:
                self._sendToMirror(channel, "%s is now known as %s"%(oldname, newname))
    def modeChanged(self, user, channel, set, modes, args):
        sign="+"
        if not set:
            sign="-"
        self._sendToMirror(channel, "mode/"+channel+" ["+sign+modes+" "+" ".join(args)+"] by "+user.split("!")[0])
    def joined(self, channel):
        self._sendToMirror(channel, "joined %s"%channel)
