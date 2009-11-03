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

from lib import chatMod
import urllib2, re

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.config=bot.root.getServiceNamed("config")

    def command(self, user, channel, command, options):
        if not self.config:
            self.bot.sendmsg(channel, "I have no config and want to cry.")
            return
        if command == "flyspray" or command=="fs":
            bugid=0
            try:
                bugid=int(options)
            except ValueError:
                self.bot.sendmsg(channel, "Bug ID must be an integer")
                return
            url=self.config.get("url", "", "flyspray", self.bot.network, channel)
            if url:
                handle=urllib2.urlopen(url+"index.php?do=details&task_id=%d"%bugid)
                if handle.geturl()==url:
                    self.bot.sendmsg(channel, "Invalid Bug ID")
                    return
                elif handle.getcode()!=200:
                    self.bot.sendmsg(channel, "Unknown Error")
                    return
                title=re.match(".*<title>([^<]*)</title>.*", handle.read(), re.S+re.I)
                if title:
                    title=title.group(1)
                    self.bot.sendmsg(channel, title)
                else:
                    self.bot.sendmsg(channel, "Error parsing the flyspray page")

