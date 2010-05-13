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
# (c) 2009 by Alexander Schier
#

"""
    Collect live statistics of channel usage
"""

from otfbot.lib import chatMod
from otfbot.lib import functions

import time


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.linesperminute = {}
        self.new_lines = {}
        self.timestamp = {}

    def msg(self, user, channel, msg):
        self.calcLPM(channel)
        self.new_lines[channel][-1] += 1

    def calcLPM(self, channel):
        new_timestamp = int(time.time())
        if not channel in self.timestamp:
            self.timestamp[channel] = new_timestamp
        if not channel in self.new_lines:
            self.new_lines[channel] = [0, 0, 0, 0, 0]
        if new_timestamp - self.timestamp[channel] >= 60:
            no_lines = reduce(lambda x, y: x + y, self.new_lines[channel][:-1])
            timediff = new_timestamp - self.timestamp[channel]
            self.linesperminute[channel] = no_lines * 60 / 4.0 / timediff
            self.new_lines[channel] = self.new_lines[channel][1:]
            self.new_lines[channel].append(0)
            self.timestamp[channel] = new_timestamp

    def getLinesPerMinute(self, channel):
        self.calcLPM(channel)
        if not channel in self.linesperminute:
            self.linesperminute[channel] = 0
        return self.linesperminute[channel]
