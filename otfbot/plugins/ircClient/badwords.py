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
# (c) 2005 - 2010 by Alexander Schier
#

"""
    Kick user from a channel based on a list of bad words
"""

from otfbot.lib import chatMod
from otfbot.lib import functions
from otfbot.lib.pluginSupport.decorators import callback

import re


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    def start(self):
        self.badwordsFile = self.bot.config.getPath("file", datadir, "badwords.txt", "badwords")
        self.register_ctl_command(self.reload)
        self.reload()

    def reload(self):
        """
            (Re-)load the file with the bad words
        """
        self.badwords = functions.loadList(self.badwordsFile)

    @callback
    def msg(self, user, channel, msg):
        nick = user.getNick()
        for word in self.badwords:
            if channel in self.bot.channels:
                if word != "" and re.search(word, msg, re.I):
                    self.logger.info("kicked %s for badword %s" % (nick, word))
                    self.bot.kick(channel, nick, "Bad word: " + word)
