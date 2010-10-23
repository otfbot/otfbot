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
# (c) 2006 by Alexander Schier
#

import time
from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback
from datetime import datetime

"""
    Remind the user after X minutes, displaying a message
"""

class Meta:
    service_depends = ['scheduler']

class Plugin(chatMod.chatMod):
    """ reminder plugin """
    def __init__(self, bot):
        self.bot=bot
        self.messages={}
        self.bot.depends_on_service('scheduler', \
            'without scheduler the reminder-plugin cannot work')
        self.scheduler = self.bot.root.getServiceNamed('scheduler')

    @callback
    def remind(self, user, channel, message):
        """
            called at every time where a reminder is set.
            will send all reminders at given time to the appropriate channels.
        """

        self.bot.sendmsg(channel, user+": Reminder: "+message)

    @callback
    def command(self, user, channel, command, options):
        """
            react on !remindme 

            add new reminders with !remindme (float) (string), i.e. !remindme 5.0 coffee is ready
        """
        _=self.bot.get_gettext(channel)
        user = user.getNick()

        if command == "remindmein":
            options = options.split(" ", 1)
            if not len(options) == 2:
                self.bot.sendmsg(channel, user+_(": ERROR: You need to specify a number of minutes and a reminder text!"))
                return
            try:
                wait=float(options[0])
            except ValueError:
                self.bot.sendmsg(channel, user+_(": ERROR: invalid number format \"%s\".") %options[0])
                return
            text = str(options[1])
            
            self.bot.sendmsg(channel, user+_(": I will remind you in %i minutes") % wait)
            self.scheduler.callLater(wait*60, self.remind, user, channel, text)

        if command == "remindmeat":
            options = options.split(" ", 2)
            if len(options) == 3 and len(options[0].split("-")) == 3 and len(options[1].split(":")) == 2:
                rdate = options[0].split("-")
                rtime = options[1].split(":")
                try:
                    dt = datetime(int(rdate[0]),int(rdate[1]),int(rdate[2]),int(rtime[0]),int(rtime[1]))
                except ValueError:
                     self.bot.sendmsg(channel, user+_(": Syntax: !remindmeat YYYY-MM-DD hh:mm <reminder text>"))
                     return
                text = str(options[2])
                if self.scheduler.callAtDatetime(dt, self.remind, user, channel, text) != False:
                    self.bot.sendmsg(channel, user+_(": I will remind you at %s %s") % (options[0],options[1]))
                else:
                    self.bot.sendmsg(channel, user+_(": ERROR: You specified a date in the past"))
            else:
                self.bot.sendmsg(channel, user+_(": Syntax: !remindmeat YYYY-MM-DD hh:mm <reminder text>"))
