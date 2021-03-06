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
# (c) 2010 by Alexander Schier

"""
    Calculate some statistics, like peak usercount.
"""
import time
from otfbot.lib import chatMod
from otfbot.lib import functions
from otfbot.lib.pluginSupport.decorators import callback

class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot=bot
        self.peak={}
        self.peak_date={}
        self.timestamps = {}
        self.AVERAGE_MINUTES = 5.0

    @callback
    def msg(self, user, channel, msg):
        self.addTs(channel, user)

    @callback
    def msg(self, user, channel, msg):
        self.addTs(channel, user)

    def removeOldTimestamps(self, channel):
        new_timestamp = int(time.time())
        while len(self.timestamps[channel]) and new_timestamp -  self.timestamps[channel][0][0] > self.AVERAGE_MINUTES*60:
            self.timestamps[channel].pop(0)

    def addTs(self, channel, user):
        new_timestamp = int(time.time())
        if not channel in self.timestamps:
            self.timestamps[channel] = [(new_timestamp, user)]
        else:
            self.timestamps[channel].append((new_timestamp, user))
        self.removeOldTimestamps(channel)

    def getLinesPerMinute(self, channel):
        if not channel in self.timestamps:
            return 0
        self.removeOldTimestamps(channel)
        return len(self.timestamps[channel]) / self.AVERAGE_MINUTES

    def getActiveUsersCount(self, channel):
        if not channel in self.timestamps:
            return 0
        self.removeOldTimestamps(channel)
        return len(set(map(lambda x:x[1], self.timestamps[channel])))

    @callback
    def joined(self, channel):
        if not channel in self.peak:
            self.peak[channel]=len(self.bot.getUsers(channel))
        if not channel in self.peak_date:
            self.peak_date[channel]=time.strftime("%d.%m.%Y %H:%M")
        self._recalc_peak(channel)

    @callback
    def userJoined(self, user, channel):
        self._recalc_peak(channel)

    def _recalc_peak(self, channel):
        if not channel in self.peak:
            self.peak[channel]=len(self.bot.getUsers(channel))
        if self.peak[channel]<len(self.bot.getUsers(channel)):
            self.peak[channel]=len(self.bot.getUsers(channel))
            self.peak_date[channel]=time.strftime("%d.%m.%Y %H:%M")

    @callback
    def command(self, user, channel, command, options):
        if command == "peak":
            self.bot.sendmsg(channel, "Maximale Nutzerzahl (%s) erreicht am %s"%(self.peak[channel], self.peak_date[channel]))
        elif command == "lpm":
            self.bot.sendmsg(channel, "aktuelle Zeilen pro Minute: %s"%(self.getLinesPerMinute(channel)))
        elif command == "activeusers":
            self.bot.sendmsg(channel, "Aktive Nutzer: %s"%(self.getActiveUsersCount(channel)))
