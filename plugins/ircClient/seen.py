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
# (c) 2009 by Thomas Wiegart
#
import sys
import shelve,time,os
from lib import chatMod

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot = bot
        try:
            os.mkdir(datadir)
        except OSError:
            pass
        self.userdata = {}#shelve.open(datadir + "/users.slv")
        
    def joined(self,channel):
        try:
            self.userdata[channel]
        except KeyError:
            self.userdata[channel] = {}
    
    def msg(self, user, channel, msg):
        self.logger.info(channel)
        if channel[0] == "#":
            self.logger.info("DATEN!")
            self.logger.info(user)
            self.logger.info(user.split("!")[0].lower())
            self.userdata[channel][user.split("!")[0].lower()] = {'msg':msg, 'time':time.time()}
    
    def command(self, user, channel, command, options):
        if command == "seen":
            time = self.userdata[channel][options.lower()]['time']
            msg = self.userdata[channel][options.lower()]['msg']
            if self.userdata[channel].has_key(options):
                self.bot.sendmsg(channel,"user " + options + " was last seen on " + str(time) + " saying " + msg + ".")
            else:
                self.bot.sendmsg(channel,"user " + options + " is unknown")

    def stop(self):
        self.userdata.close()
