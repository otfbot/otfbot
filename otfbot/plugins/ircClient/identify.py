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
# (c) 2005 - 2007 by Alexander Schier
# (c) 2006 - 2010 by Robert Weidlich
#

"""
Identify the Bot to a nickserv, if the botnick is registered
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.sent_identification = False

    @callback
    def signedOn(self):
        self.identify()

    def identify(self):
        password = self.bot.config.get("nickservPassword", None, 
            "identify", self.bot.network)
        if password:
            self.logger.info("identifying to nickserv")
            self.bot.sendmsg("nickserv", u"identify " + password)
            self.sent_identification = True
        if self.bot.config.getBool("setBotFlag", True, "identify", self.bot.network):
            self.logger.info("setting usermode +b")
            self.bot.mode(self.bot.nickname, 1, "B")

    @callback
    def noticed(self, user, channel, msg):
        user = user.getNick()
        if (user.lower() == "nickserv" and self.sent_identification):
            self.logger.debug(user + ": " + msg)

    @callback
    def connectionLost(self, reason):
        self.sent_identification = False
