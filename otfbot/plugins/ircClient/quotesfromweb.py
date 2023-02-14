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
# (c) 2008 by Thomas Wiegart
# (c) 2009 by Alexander Schier
#

"""
    Sends quotes and proverbs to the channel
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import urllib.request, urllib.error, urllib.parse
import re


class Plugin(chatMod.chatMod):
    """ quotesfromweb plugin """
    quoteurl = "http://www.all4quotes.com/quote/rss/quotes/"

    def __init__(self,bot):
        self.bot = bot
    
    @callback
    def command(self, user, channel, command, options):
        """
            Handels the commands !zitat, !sprichwort and !proverb and posts appropriate phrases in the channel
        """
        if command == "sprichwort" or command == "proverb":
            if command == "sprichwort":
                url=urllib.request.urlopen("http://www.sprichwortrekombinator.de")
            elif command == "proverb":
                url=urllib.request.urlopen("http://proverb.gener.at/or/")
            data=url.read().decode("utf-8", errors="replace")
            url.close()
            sprichwort=re.search("<div class=\"spwort\">([^<]*)<\/div>", data, re.S).group(1)
            self.bot.sendmsg(channel, sprichwort)
        elif command == "commitmsg":
            url=urllib.request.urlopen("http://whatthecommit.com/")
            data=url.read().decode("utf-8", errors="replace")
            url.close()
            msg = re.search("<p>(.*)", data).group(1)
            self.bot.sendmsg(channel, msg)
        else:
            return
