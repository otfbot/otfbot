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

import urllib2, re
from lib import chatMod

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot

    def command(self, user, channel, command, options):
        if command == "sprichwort":
            url=urllib2.urlopen("http://www.sprichwortrekombinator.de")
        elif command == "proverb":
            url=urllib2.urlopen("http://proverb.gener.at/or/")
        else:
            return
        data=url.read()
        url.close()
        sprichwort=re.search("<div class=\"spwort\">([^<]*)<\/div>", data, re.S).group(1)
        self.bot.sendmsg(channel, sprichwort)
