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
cast a vote with !votecast question and collect answers
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.bot.depends_on_service("scheduler")
        self.votes={}

    @callback
    def command(self, user, channel, command, options):
        if command == "newvote":
            if not channel in self.votes:
                self.votes[channel]=[options, 0, 0, 0, []]
                self.bot.sendmsg(channel, 
                    "Abstimmung: %s (!vote ja/nein/egal)"%options)
                self.bot.root.getServiceNamed("scheduler").callLater(
                    60, self.voteend, channel)
            else:
                self.bot.sendmsg(channel, "Es laeuft bereits eine Abstimmung.")
        elif command == "vote":
            if not channel in self.votes:
                self.bot.sendmsg(channel, "Es laeuft gerade keine Abstimmung")
                return
            elif user in self.votes[channel][4]:
                self.bot.sendmsg(channel, 
                    "%s: Du hast schon abgestimmt!"%(user.getNick()))
            else:
                self.votes[channel][4].append(user)
                if options.lower() in ["yes", "ja"]:
                    self.votes[channel][1]+=1
                elif options.lower() in ["no", "nein"]:
                    self.votes[channel][2]+=1
                elif options.lower() in ["whatever", "egal"]:
                    self.votes[channel][3]+=1

    def voteend(self, channel):
        self.bot.sendmsg(channel, "Vote: %s"%self.votes[channel][0])
        self.bot.sendmsg(channel, "Ja: %s, Nein: %s, Egal: %s"%(self.votes[channel][1], self.votes[channel][2], self.votes[channel][3]))
        del(self.votes[channel])
