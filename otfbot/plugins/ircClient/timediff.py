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
#

"""
    provide time and compare CTCP times
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

from time import mktime, ctime, strptime, time, sleep

class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.queries={}
        self.compare={}

    @callback
    def command(self, user, channel, command, options):
        _=self.bot.get_gettext(channel)
        if command == "time":
            self.bot.sendmsg(channel, _("my time: %s")%ctime())
        elif command == "timediff":
            self.bot.ctcpMakeQuery(user.getNick(), [("TIME", None)])
            self.queries[user]=channel

    @callback
    def ctcpReply(self, user, channel, tag, data):
        if tag == "TIME":
            if user in self.queries:
                try:
                    _=self.bot.get_gettext(self.queries[user])
                    timediff = time() - mktime(strptime(data))
                    self.bot.sendmsg(self.queries[user],
                      _("my time: %s, your time: %s, %d seconds difference")\
                      %(ctime(), data, timediff))
                except ValueError:
                    pass
                del self.queries[user]
