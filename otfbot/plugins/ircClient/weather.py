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
# (c) 2007 by Robert Weidlich

import xml.sax
import xml.sax.handler
import urllib
import string
import re
import time
import os.path

from twisted.internet import defer
import yaml

from otfbot.lib import chatMod, functions, urlutils
from otfbot.lib.pluginSupport.decorators import callback


class CityCodeParser(xml.sax.handler.ContentHandler):
    """Parses the answer of the CityCode Search"""

    def __init__(self):
        self.content = []

        self.inSearch = 0
        self.inLoc = 0

        self.currentLoc = -1
        self.currentLocText = ""

    def startElement(self, name, attributes):
        if name == "search":
            self.inSearch = 1
        if name == "loc":
            self.inLoc = 1
            self.currentLoc += 1
            self.content.append({'code': attributes.getValue('id')})

    def characters(self, data):
        if self.inSearch:
            if self.inLoc:
                self.currentLocText += data

    def endElement(self, name):
        if name == "search":
            self.inSearch = 0
        if name == "loc":
            self.content[self.currentLoc]['text'] = self.currentLocText
            self.currentLocText = ""
            self.inLoc = 0


class YahooWeatherParser(xml.sax.handler.ContentHandler):
    """Parses the actual weatherdata into a dict"""
    _attrs = ["yweather:location", "yweather:units",
              "yweather:wind", "yweather:atmosphere",
              "yweather:astronomy", "yweather:condition",
              "geo:lat", "geo:long"]

    def __init__(self):
        self.content = {}

        self.inChannel = 0
        self.inItem = 0
        self.Item = ""
        self.inSub = 0
        self.Sub = ""

        self.currentText = ""

    def startElement(self, name, attributes):
        if name == "channel":
            self.inChannel = 1
        if name == "item":
            self.inItem = 1
        if name in ["title", "description", "lastBuildDate", "ttl"]:
            if not name == self.inItem:
                self.inSub = 1
                self.Sub = name
        if name in self._attrs:
            vals = {}
            for attr in attributes.getNames():
                vals[attr] = attributes.getValue(attr)
            self.content[name.split(":")[1]] = vals

    def characters(self, data):
        if self.inChannel:
            if self.inItem:
                pass
            if self.inSub:
                self.currentText += data

    def endElement(self, name):
        if name == "channel":
            self.inChannel = 0
        if name == "item":
            self.inItem = 0
        if name == self.Sub:
            self.inSub = 0
            self.content[self.Sub] = self.currentText
            self.currentText = ""
            self.inSub = 0


def get_location_code(location):
    """ Fetch Location code """
    loc_enc = urllib.quote_plus(location.encode("UTF-8"))
    url = "http://xoap.weather.com/search/search?where=%s" % loc_enc
    return urlutils.download(url).addCallback(parse_location_code)


def parse_location_code(content):
    """ Parse Location code response """
    try:
        handler = CityCodeParser()
        xml.sax.parseString(content, handler)
        return defer.succeed(handler.content)
    except xml.sax._exceptions.SAXParseException:
        print "CityCodeParser: Parse Exception"
        return defer.succeed([{}])


def get_weather(location):
    """wrapperfunction for YahooWeatherParser"""
    return get_location_code(location).addCallback(fetch_weather)


def fetch_weather(codes):
    """
        Get the weather from Yahoo! Weather.
    """
    if len(codes) < 1:
        return defer.succeed([])
    url = "http://xml.weather.yahoo.com/forecastrss/%s_c.xml" \
                % str(codes[0]['code'])
    return urlutils.download(url).addCallback(parse_weather)


def parse_weather(weather):
    try:
        handler = YahooWeatherParser()
        xml.sax.parseString(weather, handler)
        return defer.succeed(handler.content)
    except xml.sax._exceptions.SAXParseException:
        print "YahooWeatherParser: Parse Exception"
        return defer.succeed([])


### otfBot-Modulecode ####
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


def getDirection(deg):
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

    def __init__(self, bot):
        self.bot = bot
        self.time = time.time()
        self.commands = ["wetter"]
        self.lastweather = {}

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
            get_weather(options).addCallback(self.send_answer, channel).addErrback(defer.logError)

    def send_answer(self, c, channel):
        if len(c) < 1 or 'location' not in c:
            self.bot.sendmsg(channel, u"Keinen passenden Ort gefunden")
        else:
            answ = "Wetter f\xfcr " + str(c['location']['city'])
            if len(c['location']['country']) > 0:
                answ += " (" + str(c['location']['country']) + ")"
            answ += ": " + str(weathercodes[int(c['condition']['code'])])
            answ += ", " + str(c['condition']['temp']) + "\xb0"
            answ += str(c['units']['temperature'])
            answ += " gef\xfchlt " + str(c['wind']['chill']) + "\xb0"
            answ += str(c['units']['temperature']) + ", Wind: "
            answ += str(c['wind']['speed']) + str(c['units']['speed'])
            answ += " aus " + str(getDirection(int(c['wind']['direction'])))
            answ += ", Luftfeuchte: " + str(c['atmosphere']['humidity']) + "%"
            if not type(answ)==unicode:
                answ=unicode(answ, "iso-8859-1")
            self.bot.sendmsg(channel, answ)
