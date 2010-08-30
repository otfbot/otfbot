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
# (c) 2006 by Alexander Schier
#

"""
    Provide some aid to make a decision
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import random
import re


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        _=self.bot.get_gettext()
        self.answers = [
        _("Signs point to yes"),
        _("Yes"),
        _("Without a doubt"),
        _("As I see it, yes"),
        _("Most likely"),
        _("You may rely on it"),
        _("Yes definitely"),
        _("It is decidedly so"),
        _("Outlook good"),
        _("It is certain"),
        _("My sources say no"),
        _("Very doubtful"),
        _("Don't count on it"),
        _("Outlook not so good"),
        _("My reply is no"),
        _("Reply hazy, try again"),
        _("Concentrate and ask again"),
        _("Better not tell you now"),
        _("Cannot predict now"),
        _("Ask again later")]

    @callback
    def msg(self, user, channel, msg):
        if self.bot.config.getBool("autoAnswer", False, "eightball", self.network, channel):
            if re.match("[a-z][^\.\?!:;]*\?", msg.lower()):
                self.bot.sendmsg(channel, random.choice(self.answers))

    @callback
    def command(self, user, channel, command, options):
        # only if the user asked something.
        if command.lower() in ["8ball", "eightball"] and options != "":
            self.bot.sendmsg(channel, random.choice(self.answers))
