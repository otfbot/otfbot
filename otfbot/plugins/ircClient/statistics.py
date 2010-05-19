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
    Calculate some statistics, as peak usercount.
"""
import time
from otfbot.lib import chatMod

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.peak={}
        self.peak_date={}

    def joined(self, channel):
        if not channel in self.peak:
            self.peak[channel]=len(self.bot.users[channel])
        if not channel in self.peak_date:
            self.peak_date[channel]=time.strftime("%d.%m.%Y %H:%M")
        self._recalc_peak()

    def userJoined(self, user, channel):
        self._recalc_peak(channel)

    def _recalc_peak(self, channel):
        if self.peak[channel]<len(self.bot.users[channel]):
            self.peak[channel]=len(self.bot.users[channel])
            self.peak_date[channel]=time.strftime("%d.%m.%Y %H:%M")


    def command(self, user, channel, command, options):
        if command == "peak":
            self.bot.sendmsg(channel, "Maximale Nutzerzahl (%s) erreicht am %s"%(self.peak[channel], self.peak_date[channel]))
