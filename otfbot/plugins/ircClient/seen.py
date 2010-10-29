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

import pickle, time, os
from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        try:
            os.mkdir(datadir)
        except OSError:
            pass
        try:
            f = file(datadir + "/users", "rb")
            self.userdata = pickle.load(f)
            f.close()
        except IOError:
            self.userdata = [{}]
        self.bot.root.getServiceNamed('scheduler').callPeriodic(60, self.save_data) #TODO: call this only on exit
        
    @callback
    def joined(self,channel):
        try:
            self.userdata[0][channel]
        except KeyError:
            self.userdata[0][channel] = {}
    
    @callback
    def msg(self, user, channel, msg):
        if channel[0] == "#":
            self.userdata[0][channel][user.getNick().lower()] = {'msg':msg, 
                'time':time.time()}
    
    @callback
    def command(self, user, channel, command, options):
        if command in ("seen", "seen-exact"):
            user=self.bot.getUserByNick(options)
            if user and user.hasChannel(channel):
                self.bot.sendmsg(channel, "%s is in the channel!"%options)
            elif options.lower() in self.userdata[0][channel]:
                zeit = self.userdata[0][channel][options.lower()]['time']
                msg = self.userdata[0][channel][options.lower()]['msg']
                if command == "seen-exact":
                    self.bot.sendmsg(channel,"user " + options + " was last "
                        "seen on " + 
                        str(time.strftime("%a, %d %b %Y %H:%M:%S",
                        time.localtime(zeit))) + " saying '" + msg + "'.")
                else:
                    delta=int(time.time() - zeit)
                    days = delta / (60 * 60 * 24)
                    delta = delta % (60 * 60 * 24)
                    hours = delta / (60 * 60)
                    delta = delta % (60 * 60)
                    minutes = delta / 60
                    seconds = delta % 60
                    if days > 0:
                        self.bot.sendmsg(channel,"user " + options + 
                            " was last seen %d days and %d hours ago, saying "
                            "\"%s\" "%(days, hours, msg))
                    elif hours > 0:
                        self.bot.sendmsg(channel,"user " + options + 
                            " was last seen %d hours and %d minutes ago, "
                            "saying \"%s\" "%(hours, minutes, msg))
                    elif minutes > 0:
                        self.bot.sendmsg(channel,"user " + options + 
                            " was last seen %d minutes and %d seconds ago, "
                            "saying \"%s\" "%(minutes, seconds, msg))
                    else:
                        self.bot.sendmsg(channel,"user " + options + 
                            " just left %d seconds ago, "
                            "saying \"%s\""%(seconds, msg))
            else:
                self.bot.sendmsg(channel,"user " + options + " is unknown")
    
    def stop(self):
        self.save_data()
    
    def save_data(self):
        f = file(datadir + "/users", "wb")
        pickle.dump(self.userdata, f)
        f.close()
