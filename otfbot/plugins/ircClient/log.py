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
# (c) 2005, 2006 by Alexander Schier
# (c) 2006 by Robert Weidlich
#

"""
    Log channel conversations to files.
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback
from otfbot.lib.color import filtercolors

import time
import string
import locale
import os
from string import Template


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.channels = {}
        self.files = {}
        self.path = {}

        #this has no usable defaultconfig string, because datadir is only known at runtime
        self.datadir = bot.config.getPath("logdir", datadir, ".", "log")
        default = "$n-$c/$y-$m-$d.log"
        self.logpath = self.datadir + "/" + bot.config.get("path", default, "log")
        self.doLogPrivate = self.bot.config.getBool("logPrivate", True, "log")
        #TODO: blocking
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)
        #try:
        #    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
        #except:
        #    locale.setlocale(locale.LC_ALL, "")
        # saves the hour, to detect daychanges
        self.day = self.ts("%d")
        #for c in self.bot.channels:
        #    self.setNetwork()
        #    self.joined(c)
        self.setNetwork()

    def timemap(self):
        return {'y': self.ts("%Y"), 'm': self.ts("%m"), 'd': self.ts("%d")}

    def ts(self, format="%H:%M"):
        """timestamp"""
        return time.strftime(format, time.localtime(time.time()))

    def secsUntilDayChange(self):
        """calculate the Seconds to midnight"""
        tmp = time.localtime(time.time())
        wait = (24 - tmp[3] - 1) * 60 * 60
        wait += (60 - tmp[4] - 1) * 60
        wait += 60 - tmp[5]
        return wait

    def dayChange(self):
        self.day = self.ts("%d")
        self.closeLogs()
        for channel in self.channels:
            self.openLog(channel)
            #self.log(channel, "--- Day changed "+self.ts("%a %b %d %Y"))

    def log(self, channel, string, timestamp=True):
        if self.day != self.ts("%d"):
            self.dayChange()
        if channel in self.channels:
            logmsg = filtercolors(string) + "\n"
            if timestamp:
                logmsg = self.ts() + " " + logmsg
            #TODO: blocking
            self.files[channel].write(logmsg.encode("UTF-8"))
            self.files[channel].flush()

    def logPrivate(self, user, mystring):
        if self.doLogPrivate:
            mystring = filtercolors(mystring)
            dic = self.timemap()
            dic['c'] = string.lower(user)
            filename = Template(self.logpath).safe_substitute(dic)
            #TODO: blocking
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            file = open(filename, "a")
            file.write(self.ts() + " " + mystring.encode("UTF-8") + "\n")
            file.close()

    def openLog(self, channel):
        self.channels[string.lower(channel)] = 1
        #self.files[string.lower(channel)]=open(string.lower(channel)+".log", "a")
        self.path[channel] = Template(self.logpath).safe_substitute({'c': channel.replace("/", "_").replace(":", "")}) #replace to handle psyc:// channels
        file = Template(self.path[channel]).safe_substitute(self.timemap())
        #TODO: blocking
        if not os.path.exists(os.path.dirname(file)):
            os.makedirs(os.path.dirname(file))
        self.files[string.lower(channel)] = open(file, "a")
        self.log(channel, "--- Log opened " + self.ts("%a %b %d %H:%M:%S %Y"), False)

    @callback
    def joined(self, channel):
        self.openLog(channel)
        self.log(channel, "-!- " + self.bot.nickname + " [" + self.bot.hostmask.split("!")[1] + "] has joined " + channel)

    @callback
    def left(self, channel):
        self.log(channel, "-!- " + self.bot.nickname + "[" + self.bot.hostmask.split("!")[1] + "] has left " + channel)
        del self.channels[string.lower(channel)]
        self.files[string.lower(channel)].close()

    @callback
    def msg(self, user, channel, msg):
        user = user.getNick()
        modesign = " " #self.bot.users[channel][user]['modchar']
        if string.lower(channel) == string.lower(self.bot.nickname):
            self.logPrivate(user, "<" + modesign + user + "> " + msg)
        elif len(channel) > 0 and channel[0] == "#":
            #modesign=self.bot.users[channel][user]['modchar']
            self.log(channel, "<" + modesign + user + "> " + msg)

    @callback
    def query(self, user, channel, msg):
        user = user.getNick()
        if user == self.bot.nickname:
            self.logPrivate(channel, "<" + user + "> " + msg)
        else:
            self.logPrivate(user, "<" + user + "> " + msg)

    @callback
    def noticed(self, user, channel, msg):
        if user != "":
            #self.logger.info(str(user+" : "+channel+" : "+msg))
            self.logPrivate(user.getNick(), "< " + user.getNick() + "> " + msg)

    @callback
    def action(self, user, channel, msg):
        #self.logger.debug(user+channel+msg)
        user = user.getNick()
        self.log(channel, " * " + user + " " + msg)

    @callback
    def modeChanged(self, user, channel, set, modes, args):
        user = user.getNick()
        sign = "+"
        if not set:
            sign = "-"
        self.log(channel, "-!- mode/" + channel + " [" + sign + modes + " " + string.join(args, " ") + "] by " + user)

    @callback
    def userKicked(self, kickee, channel, kicker, message):
        self.log(channel, "-!- " + kickee + " was kicked from " + channel + " by " + kicker + " [" + message + "]")

    @callback
    def userJoined(self, user, channel):
        self.log(channel, "-!- " + user.getNick() + " [" + user.getHostMask().split("!")[1] + "] has joined " + channel)

    @callback
    def userLeft(self, user, channel):
        self.log(channel, "-!- " + user.getNick() + " [" + user.getHostMask().split("!")[1] + "] has left " + channel)

    @callback
    def userQuit(self, user, quitMessage):
        #user is known with current hostmask
        if user in self.bot.user_list:
            user=self.bot.user_list[user]
        #hostmask changed (vHost function of some IRCDs)
        #or nicktracking did not work as expected
        #but even lower(nick) should be unique per network
        else:
            user=self.bot.getUserByNick(user.getNick())

        if user:
            for channel in user.getChannels():
                self.log(channel, "-!- " + user.nick + " [" + user.user + "@" + user.host + "] has quit [" + quitMessage + "]")

    @callback
    def topicUpdated(self, user, channel, newTopic):
        #TODO: first invoced on join. This should not be logged
        self.log(channel, "-!- " + user + " changed the topic of " + channel + " to: " + newTopic)

    @callback
    def userRenamed(self, oldname, newname):
        for user in self.bot.user_list.values():
            if user.nick.lower() == oldname.lower():
                for channel in user.getChannels():
                    self.log(channel, "-!- " + oldname + " is now known as " + newname)

    @callback
    def stop(self):
        self.closeLogs()

    def closeLogs(self):
        for channel in self.channels:
            self.log(channel, "--- Log closed " + self.ts("%a %b %d %H:%M:%S %Y"), False)
            self.files[channel].close()

    @callback
    def connectionMade(self):
        self.setNetwork()

    def setNetwork(self):
        if len(self.bot.network.split(".")) < 3:
            net = self.bot.network
        else:
            net = self.bot.network.split(".")[-2]
        self.logpath = Template(self.logpath).safe_substitute({'n': net})
