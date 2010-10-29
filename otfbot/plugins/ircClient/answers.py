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
    Send answers from file based on regexes
"""

import string
import re

from otfbot.lib import chatMod
from otfbot.lib import functions
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    def start(self):
        self.answersFile = self.bot.config.getPath("file", datadir, "answers.txt", "answer")
        self.encoding = self.bot.config.get("fileencoding", "iso-8859-15", "answer")
        self.reload()

    @callback
    def action(self, user, channel, msg):
        return self.msg(user, channel, msg)

    @callback
    def msg(self, user, channel, msg):
        user = user.getNick()
        if channel in self.bot.channels: #Do not respond to server messages
            answer = self.respond(user, msg)
            if answer != "":
                self.bot.sendmsg(channel, answer, self.encoding)

    def reload(self):
        """
            load the answers from the configured file
        """
        self.answers = functions.loadProperties(self.answersFile)

    def respond(self, user, msg):
        """
            assemble a response

            @param user: name of the user which issued the message
            @param msg: the message which needs a response
        """
        answer = ""
        for key in self.answers.keys():
            if re.search(key, msg, re.I):
                answer = self.answers[key]
                answer = re.sub("USER", user, answer)
                answer = re.sub("MESSAGE", msg, answer)
        if len(answer) > 0 and answer[-1] == "\n":
            return answer[0:-1]
        else:
            return answer
