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
    Calculate the discordian Date
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

import random
import datetime
import calendar


#http://rosettacode.org/wiki/Discordian_date
DISCORDIAN_SEASONS = ["Chaos", "Discord", "Confusion", "Bureaucracy",
    "The Aftermath"]
DISCORDIAN_WEEKDAYS=["Sweetmorn", "Boomtime", "Pungenday", "Prickle-Prickle",
    "Setting Orange"]
 
def ddate(year, month, day, _):
    today = datetime.date(year, month, day)
    is_leap_year = calendar.isleap(year)
    if is_leap_year and month == 2 and day == 29:
        return "St. Tib's Day, YOLD " + (year + 1166)
 
    day_of_year = today.timetuple().tm_yday - 1
 
    weekday=day_of_year % 5
    if is_leap_year and day_of_year >= 60:
        day_of_year -= 1 # Compensate for St. Tib's Day
 
    season, dday = divmod(day_of_year, 73)
    return _("Today is %s, the %d day of %s in the YOLD %d") \
        % (DISCORDIAN_WEEKDAYS[weekday], dday + 1, \
        DISCORDIAN_SEASONS[season], year + 1166)


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot

    @callback
    def command(self, user, channel, command, options):
        _=self.bot.get_gettext(channel)
        if command == "ddate":
            dt = datetime.datetime.now()
            self.bot.sendmsg(channel, ddate(dt.year, dt.month, dt.day, _))
