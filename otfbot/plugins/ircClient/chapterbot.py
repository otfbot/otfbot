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
# (c) 2009 by Finn Wilke
#

"""
    Record a series of user generated events with time stamps
"""

from otfbot.lib import chatMod

import time
import os
from time import gmtime
from time import strftime
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.started = False
        self.start_time = 0
        self.end_time = 0
        self.datadir = datadir
        self.admins = bot.config.get("admins", "[]", "chapterbot")
        #TODO: blocking
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)

    def writelog(self, filename, data):
        #TODO: blocking
        file = open(filename, "w")
        for item in data:
            line = item[0] + " " + item[1] + "\n"
            file.write(line)
            file.close

    def validUser(self, user, channel, userlist=None):
        if userlist == None:
            userlist = self.admins
        for i in userlist:
            if i == user:
                return True
        return False

    @callback
    def command(self, user, channel, command, options):
        sender = user.split("!")[0]

        if command == "foo":
            self.bot.sendmsg(channel, self.admins)

        if command == "start":
            if not self.started and self.validUser(sender, channel):
                self.started = True
                self.start_time = time.time()
                self.chapters = []
                self.chaptercount = 0
                self.logpath = self.datadir + strftime("%Y-%m-%d", time.gmtime(self.start_time))
                #TODO: blocking
                if os.path.exists(self.logpath + ".log"):
                    i = 1
                    while os.path.exists(self.logpath + "." + str(i) + ".log"):
                        i += 1
                    self.logpath += "." + str(i)
                self.logpath += ".log"
                #self.bot.msg(channel, "datadir is:" + str(self.datadir))
                #self.bot.msg(channel, "logpath is:" + str(self.logpath))
                self.bot.sendmsg(channel, "Sitzung beginnt jetzt (time: " + strftime("%H:%M:%S", time.gmtime(self.start_time)) + ")")

        if command == "stop" and self.validUser(sender, channel):
            if self.started:
                self.started = False
                self.stop_time = time.time()
                self.session_length = self.stop_time - self.start_time
                self.bot.sendmsg(channel, "Sitzung wurde beendet um " + strftime("%H:%M:%S", time.gmtime(self.stop_time)) + ". - Dauer: " + strftime("%H:%M:%S", time.gmtime(self.session_length)))

        if command == "chapter":
            if self.started:
                chaptertime = time.time()
                self.chaptercount += 1
                description = options
                chapter = [strftime("%H:%M:%S.000", time.gmtime(chaptertime)), description]
                self.chapters.append(chapter)
                self.writelog(self.logpath, self.chapters)

        if command == "list":
            if self.chaptercount != 0:
                self.bot.sendmsg(sender, "Es gibt " + str(self.chaptercount) + " Kapitel:")
                i = 0
                for item in self.chapters:
                    i += 1
                    self.bot.sendmsg(sender, "Kapitel " + str(i) + " (" + str(item[0]) + "): \"" + str(item[1]) + "\"")
