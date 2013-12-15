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
# # (c) 2013 by Robert Weidlich
#

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

""" an example for a plugin for the ircClient """


class Monitor(object):

    def __init__(self, plugin, nick):
        self.plugin = plugin
        self.nick = nick
        self.start()

    def start(self):
        pass

    def irc_unknown(self, prefix, command, params):
        pass

    def stop(self):
        pass


class WatchMonitor(Monitor):

    def start(self):
        self.plugin.bot.sendLine("WATCH +%s" % self.nick)

    def irc_unknown(self, prefix, command, params):
        if command == "601": # offline
            self.plugin.check_nick_change(params[1])
        elif command == "602": # stopped watching
            pass
        elif command == "604": # is online
            pass

    def stop(self):
        self.plugin.bot.sendLine("WATCH -%s" % self.nick)

class MonitorMonitor(Monitor):

    def start(self):
        self.plugin.bot.sendLine("MONITOR + %s" % self.nick)

    def irc_unknown(self, prefix, command, params):
        if command == "731": # offline
            self.plugin.check_nick_change(params[1])
        elif command == "730": # is online
            pass

    def stop(self):
        self.plugin.bot.sendLine("MONITOR - %s" % self.nick)

class Plugin(chatMod.chatMod):

    # are we currently watching a name we want to get?
    keepnick = False

    # the nick we want to get
    confignick = "OtfBot"

    monitor = None

    connected = False

    def __init__(self, bot):
        self.bot = bot

    def check_nick_change(self, nick):
        if nick == self.confignick and self.keepnick:
            self.logger.debug("Desired nick free, changing my nick")
            self.keepnick = False
            self.bot.setNick(self.confignick)
            self.monitor.stop()

    def start_nickkeeping(self): 
        self.keepnick = True
        self.logger.info('Signed On as %s, expected %s. Trying to get expected nick.' % (self.bot.nickname, self.confignick))
        if self.connected:
            self.start_monitoring()

    def start_monitoring(self):
        if self.keepnick:
            if "MONITOR" in self.bot.serversupports:
                self.monitor = MonitorMonitor(self, self.confignick)
            elif "WATCH" in self.bot.serversupports:
                self.monitor = WatchMonitor(self, self.confignick)

    @callback
    def signedOn(self):
        self.confignick = self.bot.config.get("nickname", "OtfBot", 'main', self.network)
        if self.bot.nickname != self.confignick:
            self.start_nickkeeping()

    @callback
    def connected(self):
        self.connected = True
        self.start_monitoring()

    @callback
    def userKicked(self, kickee, channel, kicker, message):
        self.check_nick_change(kickee)

    @callback
    def userQuit(self, user, quitMessage):
        self.check_nick_change(user.nick)

    @callback
    def userRenamed(self, oldname, newname):
        self.check_nick_change(oldname)

    @callback
    def nickChanged(self, nick):
        if nick != self.confignick:
            self.start_nickkeeping()

    @callback
    def irc_unknown(self, prefix, command, params):
        if self.keepnick and self.monitor:
            self.monitor.irc_unknown(prefix, command, params)
