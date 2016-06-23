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
import urllib2

from twisted.internet.defer import inlineCallbacks, returnValue
import twisted.web.client
twisted.web.client._HTTP11ClientFactory.noisy = False

import treq
from lxml import etree

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


weathercodes = {
    0: u"Tornado", 1: u"Tropensturm", 2: u"Hurrikan", 3: u"ernsthafte Gewitter",
    4: u"Gewitter", 5: u"Regen und Schnee", 6: u"Regen und Graupelschauer",
    7: u"Schnee und Graupelschauer", 8: u"gefriender Nieselregen",
    9: u"Nieselregen", 10: u"gefrierender Regen", 11: u"Schauer", 12: u"Schauer",
    13: u"Schneegest\xf6ber", 14: u"leichte Schneeschauer", 15: u"Schneesturm",
    16: u"Schnee", 17: u"Hagel", 18: u"Graupelschauer", 19: u"starker Nebel",
    20: u"Nebel", 21: u"schwacher Nebel", 22: u"Qualmig", 23: u"St\xfcrmisch",
    24: u"Windig", 25: u"Kalt", 26: u"Bew\xf6lkt",
    27: u"\xfcberwiegend bew\xf6lkt", 28: u"\xfcberwiegend bew\xf6lkt",
    29: u"Teils bew\xf6lkt", 30: u"Teils bew\xf6lkt", 31: u"Klar", 32: u"Sonnig",
    33: u"Heiter", 34: u"Heiter", 35: u"Regen und Hagel", 36: u"Heiss",
    37: u"vereinzelte Gewitter", 38: u"verstreute Gewitter",
    39: u"verstreute Gewitter", 40: u"vereinzelte Schauer",
    41: u"starker Schneefall", 42: u"vereinzelt Schnee und Regen",
    43: u"starker Schneefall", 44: u"teils Bew\xf6lkt", 45: u"Gewitter",
    46: u"Schneeschauer", 47: u"vereinzelte Gewitter", 3200: u"Unbekannt"}


def get_direction(deg):
    dirs = [u"N", u"NNO", u"NO", u"NOO", u"O", u"SOO", u"SO", u"SSO",
            u"S", u"SSW", u"SW", u"SWW", u"W", u"NWW", u"NW", u"NNW", u"N"]
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

        template = u"Wetter f\xfcr {location[city]} ({location[country]}/{location[region]}): {conditionstr}, "
        template += u"{condition[temp]}\xb0{units[temperature]} "
        template += u"gef\xfchlt {wind[chill]}\xb0{units[temperature]}, "
        template += u"Wind: {wind[speed]}{units[speed]} aus {winddirection}, "
        template += u"Luftfeuchte: {atmosphere[humidity]}%"

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
            self.bot.sendmsg(channel, u"Wait a minute ...")
            return

        self.time = time.time()
        if command == "wetter":
            if not len(options) and nick in self.lastweather:
                options = self.lastweather[nick]
            elif len(options):
                self.lastweather[nick] = options
            self.get_weather_wrapper(options, channel)

