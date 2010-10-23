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
# (c) 2007 by Alexander Schier
#

"""
    Track the karma of user supplied terms
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import pickle
import os


def sortedbyvalue(dict):
    """Helper function to return a [(value, key)] list from a dict"""
    items = [(k, v) for (v, k) in dict.items()]
    items.reverse()
    return items


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.karmas = {} #channel ->  (what -> karma-struct)
        self.karmapaths = {} #path -> (what -> channel) (pointer!)
        self.verbose = self.bot.config.getBool("karma.verbose", True)
        self.freestyle = self.bot.config.getBool("karma.freestyle", True)

    def loadKarma(self, channel):
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        karmapath = self.bot.config.getPath("file", datadir, "karma.dat", "karma", self.bot.network, channel)
        if not karmapath in self.karmapaths.keys():
            if os.path.exists(karmapath):
                #TODO: blocking
                karmafile = open(karmapath, "r")
                self.karmas[channel] = pickle.load(karmafile)
                self.karmapaths[karmapath] = channel
                karmafile.close()
            else:
                self.karmas[channel] = {} #what -> karma-struct
        else:
            # pointer(!) to shared karma
            self.karmas[channel] = self.karmas[self.karmapaths[karmapath]]

    def saveKarma(self, channel):
        #Attention: we write the files from karmapaths(which are unique), not
        #           from the channels array!
        #TODO: blocking
        karmapath = self.bot.config.getPath("file", datadir, "karma.dat", "karma", self.bot.network, channel)
        karmafile = open(karmapath, "w")
        pickle.dump(self.karmas[channel], karmafile)
        karmafile.close()

    @callback
    def joined(self, channel):
        self.loadKarma(channel)

    @callback
    def left(self, channel):
        self.saveKarma(channel)

    @callback
    def command(self, user, channel, command, options):
        up = False
        what = None
        reason = None

        #return on why/who karma up/down
        num_reasons = 5
        num_user = 5

        tmp = options.split("#", 1)
        options = tmp[0].strip()
        if len(tmp) == 2:
            reason = tmp[1]

        if command == "karma":
            if options == "":
                rmsg = "Nutzen: !karma name++ oder !karma name--"
                self.bot.sendmsg(channel, rmsg)
                return
            else:
                if options[-2:] == "++":
                    up = True
                    what = options[:-2]
                elif options[-2:] == "--":
                    up = False
                    what = options[:-2]
                else:
                    self.tell_karma(options, channel)
                    return
            self.do_karma(channel, what, up, reason, user)
            if self.verbose:
                self.tell_karma(what, channel)
        elif command == "why-karmaup" or command == "wku":
            options.strip()
            reasons = ""
            if options in self.karma.keys():
                num = min(num_reasons, len(self.karma[options][3]))
                while num > 0:
                    num -= 1
                    reasons += " .. " + self.karma[options][3][-num]
                reasons = reasons[4:]
                self.bot.sendmsg(channel, reasons)
        elif command == "why-karmadown" or command == "wkd":
            options.strip()
            reasons = ""
            if options in self.karma.keys():
                num = min(num_reasons, len(self.karma[options][4]))
                while num > 0:
                    num -= 1
                    reasons += " .. " + self.karma[options][4][-num]
                reasons = reasons[4:]
                self.bot.sendmsg(channel, reasons)
        elif command == "who-karmaup":
            options.strip()
            people = ""
            if options in self.karma.keys():
                items = sortedbyvalue(self.karma[options][1])
                num = min(num_user, len(items))
                while num > 0:
                    num -= 1
                    people += " .. " + items[-num][1] + "=" + str(items[-num][0])
                people = people[4:]
                self.bot.sendmsg(channel, people)
        elif command == "who-karmadown":
            options.strip()
            people = ""
            if options in self.karma.keys():
                items = sortedbyvalue(self.karma[options][2])
                num = min(num_user, len(items))
                while num > 0:
                    num -= 1
                    people += " .. " + items[-num][1] + "=" + str(items[-num][0])
                people = people[4:]
                self.bot.sendmsg(channel, people)
        elif self.freestyle:
            if options[-2:] == "++":
                up = True
                what = command + " " + options[:-2]
            elif options[-2:] == "--":
                up = False
                what = command + " " + options[:-2]
            elif command[-2:] == "++":
                up = True
                what = command[:-2]
            elif command[-2:] == "--":
                up = False
                what = command[:-2]
            if what:
                self.do_karma(channel, what, up, reason, user)
                if self.verbose:
                    self.tell_karma(what, channel)

    def tell_karma(self, what, channel):
        self.bot.sendmsg(channel, "Karma: " + what + ": " + str(self.get_karma(channel, what)))

    def get_karma(self, channel, what):
        if not what in self.karmas[channel].keys():
            self.karmas[channel][what] = [0, {}, {}, [], []] #same as below!
        return self.karmas[channel][what][0]

    def do_karma(self, channel, what, up, reason, user):
        user = user.getNick()
        karma = self.karmas[channel]
        if not what in karma.keys():
            # score, who-up, who-down, why-up, why-down
            karma[what] = [0, {}, {}, [], []]
        if up:
            karma[what][0] = int(karma[what][0]) + 1
            if not user in karma[what][1].keys():
                karma[what][1][user] = 1
            else:
                karma[what][1][user] += 1
            if reason:
                karma[what][3].append(str(reason))
        else:
            karma[what][0] = int(karma[what][0]) - 1
            if not user in karma[what][2].keys():
                karma[what][2][user] = 1
            else:
                karma[what][2][user] += 1
            if reason:
                karma[what][4].append(str(reason))

    def stop(self):
        for karmapath in self.karmapaths.keys():
            self.saveKarma(self.karmapaths[karmapath])

    def start(self):
        for c in self.bot.channels:
            self.joined(c)
