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
# (c) 2005, 2006 by Alexander Schier
# (c) 2007, 2014 by Robert Weidlich

import time
import urllib.request, urllib.error, urllib.parse

from twisted.internet.defer import inlineCallbacks, returnValue
import twisted.web.client
twisted.web.client._HTTP11ClientFactory.noisy = False

import treq
from lxml import etree

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


weathercodes = {
    0: "Tornado", 1: "Tropensturm", 2: "Hurrikan", 3: "ernsthafte Gewitter",
    4: "Gewitter", 5: "Regen und Schnee", 6: "Regen und Graupelschauer",
    7: "Schnee und Graupelschauer", 8: "gefriender Nieselregen",
    9: "Nieselregen", 10: "gefrierender Regen", 11: "Schauer", 12: "Schauer",
    13: "Schneegest\xf6ber", 14: "leichte Schneeschauer", 15: "Schneesturm",
    16: "Schnee", 17: "Hagel", 18: "Graupelschauer", 19: "starker Nebel",
    20: "Nebel", 21: "schwacher Nebel", 22: "Qualmig", 23: "St\xfcrmisch",
    24: "Windig", 25: "Kalt", 26: "Bew\xf6lkt",
    27: "\xfcberwiegend bew\xf6lkt", 28: "\xfcberwiegend bew\xf6lkt",
    29: "Teils bew\xf6lkt", 30: "Teils bew\xf6lkt", 31: "Klar", 32: "Sonnig",
    33: "Heiter", 34: "Heiter", 35: "Regen und Hagel", 36: "Heiss",
    37: "vereinzelte Gewitter", 38: "verstreute Gewitter",
    39: "verstreute Gewitter", 40: "vereinzelte Schauer",
    41: "starker Schneefall", 42: "vereinzelt Schnee und Regen",
    43: "starker Schneefall", 44: "teils Bew\xf6lkt", 45: "Gewitter",
    46: "Schneeschauer", 47: "vereinzelte Gewitter", 3200: "Unbekannt"}


def get_direction(deg):
    dirs = ["N", "NNO", "NO", "NOO", "O", "SOO", "SO", "SSO",
            "S", "SSW", "SW", "SWW", "W", "NWW", "NW", "NNW", "N"]
    d = 11.25
    i = 0
    while d < 372:
        if deg < d:
            return dirs[i]
        i += 1
        d += 22.5


class Plugin(chatMod.chatMod):
    '''
       This plugin fetches the current weather from yahoo apis. For the places api
       you need to get an appid token from yahoo at 
       https://developer.apps.yahoo.com/wsregapp/
    '''

    def __init__(self, bot):
        self.bot = bot
        self.time = time.time()
        self.commands = ["wetter", ]
        self.lastweather = {}

    def weather_to_string(self, result):
        data = {}
        data.update(result)
        data.update(result["item"])
        data['conditionstr'] = weathercodes[int(data['condition']['code'])]
        data['winddirection'] = get_direction(
            int(data['wind']['direction']))

        template = "Wetter f\xfcr {location[city]} ({location[country]}/{location[region]}): {conditionstr}, "
        template += "{condition[temp]}\xb0{units[temperature]} "
        template += "gef\xfchlt {wind[chill]}\xb0{units[temperature]}, "
        template += "Wind: {wind[speed]}{units[speed]} aus {winddirection}, "
        template += "Luftfeuchte: {atmosphere[humidity]}%"

        return template.format(**data)

    @inlineCallbacks
    def get_weather_wrapper(self, string, channel):
        try:
            baseurl = "https://query.yahooapis.com/v1/public/yql?"
            yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='%s') and u='c'"

            params = {'q': yql_query % string, 'format': 'json'}
            result = yield treq.get(baseurl, params=params)
            content = yield result.json()

            if content["query"]["results"]:
                self.bot.sendmsg(
                    channel, self.weather_to_string(content["query"]["results"]["channel"]))
            else:
                self.bot.sendmsg(channel, "Keinen passenden Ort gefunden")
        except Exception as e:
            self.bot.sendmsg(
                channel, "Some error occured while fetching the weather.")
            self.logger.error(e)

    @callback
    def command(self, user, channel, command, options):
        nick = user.getNick()
        if channel in self.commands and 0 < (time.time() - self.time) < 5:
            self.bot.sendmsg(channel, "Wait a minute ...")
            return

        self.time = time.time()
        if command == "wetter":
            if not len(options) and nick in self.lastweather:
                options = self.lastweather[nick]
            elif len(options):
                self.lastweather[nick] = options
            self.get_weather_wrapper(options, channel)

