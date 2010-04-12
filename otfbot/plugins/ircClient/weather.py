# This file is part of OtfBot.
# -*- coding: utf-8 -*-
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
# (c) 2010 by Thomas Wiegart
#

from otfbot.lib import chatMod
HAS_PYWAPI = True
try:
    import pywapi
except ImportError:
    HAS_PYWAPI = False

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot = bot
        if not HAS_PYWAPI:
            self.bot.depends("pywapi - http://code.google.com/p/python-weather-api/")
    
    def command(self, user, channel, command, options):
        if command in ["wetter", "weather"]:
            try:
                wetter = pywapi.get_weather_from_google(options)
                feuchtigkeit = wetter['current_conditions']['humidity']
                temperatur = wetter['current_conditions']['temp_c'] + " Grad C"
                wind = wetter['current_conditions']['wind_condition']
                beschreibung = wetter['current_conditions']['condition']
                self.bot.sendmsg(channel,"Wetter fuer " + options + ": " + beschreibung.encode("utf8") + " bei " + temperatur.encode("utf8") + ". " + wind.encode("utf8") + ", " + feuchtigkeit.encode("utf8"),"UTF-8")
            except KeyError:
                self.bot.sendmsg(channel,"Unbekannter Ort oder PLZ: " + options)
