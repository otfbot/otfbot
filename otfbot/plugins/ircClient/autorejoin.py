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
# (c) 2008 - 2010 by Thomas Wiegart
#

"""
Rejoin, if kicked. (note: this is often a bad idea!)
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    @callback
    def kickedFrom(self, channel, kicker, message):
        if int(self.bot.config.get("enabled", False, "autorejoin", self.bot.network, channel)):
            self.bot.join(channel)
