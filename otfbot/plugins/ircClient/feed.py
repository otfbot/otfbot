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
# (c) 2005 - 2010 by Alexander Schier
#

"""
Post Headlines and Links from a Newsfeed
"""

from twisted.internet import reactor

from otfbot.lib import chatMod, urlutils
from otfbot.lib.pluginSupport.decorators import callback

import time


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.end = False

        self.feedparser = self.bot.depends_on_module("feedparser")
        self.bot.depends_on_service("scheduler")

        self.feedHeadlines = {} #map url -> [(url, headline), ...]
        self.readUrls = {} #map channel->[url, url, ...]
        self.feedLastLoaded = {} #map url->timestamp
        self.callIDs = {} #map url -> callLater ID

    def addSource(self, url, channel, minWait, maxWait, factor, postMax):
        """ add a feed
            @param url: the url of the feed
            @param minWait: minimal time between updates
            @param maxWait: maximum time between updates
            @param factor: the factor to increase update delay
            if no new news were found
            @param postMax: maximum new items to post on update
        """
        if(minWait > maxWait):
            wmsg = "%s minWait is bigger than maxWait. Skipping feed." % url
            self.logger.warning(wmsg)
            return
        if factor == 0:
            self.logger.warning(url + " has a waitFactor of 0."+
                " Skipping feed.")
            return
        self.callIDs[url] = self.bot.root.getServiceNamed('scheduler').\
            callLater(minWait * 60, self.postNewsLoop, channel, url,
            minWait, minWait, maxWait, factor, postMax)

        self.readUrls[channel] = []
        self.feedLastLoaded[url] = 0
        self.feedHeadlines[url] = []

        self.logger.debug(url + " (update every " + str(minWait) + " - " +\
            str(maxWait) + " minutes), waitFactor " + str(factor) + ".")

    def loadSource(self, num, channel):
        feedUrl = self.bot.config.get("feed" + str(num) + ".url", "",\
            "feed", self.bot.network, channel)

        feedMinWait = float(self.bot.config.get("feed" + str(num) +\
            ".minWait", "5.0", "feed", self.bot.network, channel))
        feedMaxWait = float(self.bot.config.get("feed" + str(num) +\
            ".maxWait", "60.0", "feed", self.bot.network, channel))
        feedWaitFactor = float(self.bot.config.get("feed" + str(num) +\
            ".waitFactor", "1.5", "feed", self.bot.network, channel))
        feedPostMax = int(self.bot.config.get("feed" + str(num) +\
            ".postMax", "3", "feed", self.bot.network, channel))

        self.addSource(feedUrl, channel, feedMinWait, feedMaxWait,\
            feedWaitFactor, feedPostMax)

    @callback
    def joined(self, channel):
        numFeeds = int(self.bot.config.get("numFeeds", 0, "feed",\
            self.bot.network, channel))
        if numFeeds > 0:
            self.logger.debug("Found " + str(numFeeds) + " Feed-Urls:")
            for i in xrange(1, numFeeds + 1):
                self.loadSource(i, channel)

    def getWaitTime(self, curWait, minWait, maxWait, factor, hadNew):
        """ calculate the new wait time
            @type curWait: float
            @param curWait: current wait time
            @type minWait: float
            @param minWait: minimum wait time
            @type maxWait: float
            @param curWait: maximum wait time
            @type maxWait: float
            @param factor: factor (>=1) to increase the delay if no news
            were found
            @type hadNew: bool
            @param hadNew: set to true, if new news were loaded
        """
        newWait = 1.0
        if hadNew:
            if curWait != minWait:
                self.logger.debug("new wait-time: " + str(minWait) +\
                    " (minimum)")
            newWait = minWait
        else:
            newWait = curWait * factor
            if newWait > maxWait:
                newWait = maxWait
                self.logger.debug("new wait-time: " + str(newWait) +\
                    " (maximum)")
            else:
                self.logger.debug("new wait-time: " + str(newWait))
        return newWait

    def loadNews(self, url):
        self.feedLastLoaded[url] = int(time.time()) #to be removed, too?
        self.logger.debug("loading new Headlines")
        urlutils.download(url).addCallback(self.parseNews, url)

    def parseNews(self, feedcontent, url):
        def parseNewsThread(self, feedcontent, url):
            parsed = self.feedparser.parse(feedcontent)
            self.feedHeadlines[url] = []
            for entry in parsed['entries']:
                self.feedHeadlines[url].append((entry['link'], entry['title']))
        reactor.callInThread(parseNewsThread, self, feedcontent, url)

    def postNews(self, channel, url, feedPostMax):
        had_new = False #new urls? needed for wait-time modification
        numPostUrls = feedPostMax
        channels = self.bot.channels
        for (url, headline) in self.feedHeadlines[url]:
            if channel in channels:
                if not url in self.readUrls[channel]:
                    if numPostUrls > 0:
                        numPostUrls -= 1
                        self.bot.sendmsg(channel, (url +\
                            " - " + headline))
                        #TODO: config option to choose?
                        #with this line, all urls will be posted, but the
                        #queue may get longer and longer
                        #self.readUrls[channel].append(url) 
                    #with this line, we will throw away all new urls,
                    #which are more than feedPostMax (less indented)
                    self.readUrls[channel].append(url)
                    had_new = True
        self.logger.debug("posted " + str(feedPostMax - numPostUrls) +\
            " new URLs")
        return had_new

    def postNewsLoop(self, channel, url, curWait=5.0, minWait=1.0,\
        maxWait=60.0, factor=1.5, feedPostMax=3):
        """load News if needed and Post them to a channel"""
        if self.end:
            return

        #avoid loading, if it was loaded by another channel-loop
        #at the wait-time
        if time.time() - self.feedLastLoaded[url] > curWait:
            self.loadNews(url)
        had_new = self.postNews(channel, url, feedPostMax)

        newWait = self.getWaitTime(curWait, minWait, maxWait, factor,\
            had_new)
        self.callIDs[url] = self.bot.root.getServiceNamed('scheduler')\
            .callLater(newWait * 60, self.postNewsLoop, channel, url,\
            newWait, minWait, maxWait, factor, feedPostMax) #recursion

    @callback
    def connectionLost(self, reason):
        self.stop()

    def stop(self):
        self.end = 1

    @callback
    def command(self, user, channel, command, options):
        if self.bot.auth(user) >= 10:
            if command == "refresh":
                if options != "":
                    num = int(options)
                    if num != 0:
                        feedUrl = self.bot.config.get("feed" + str(num) +\
                            ".url", "", "feed", self.bot.network, channel)
                        self.callIDs[feedUrl].cancel()
                        self.loadNews(feedUrl)
                        self.postNews(channel, feedUrl,\
                            int(self.bot.config.get("feed" + str(num) +\
                            ".postMax", "3", "feed", self.bot.network,\
                            channel)))
                        self.loadSource(num, channel)
            elif command == "addfeed":
                options = options.split(" ")
                num = int(self.bot.config.get("numFeeds", 0, "feed",\
                    self.bot.network, channel)) + 1
                if len(options) == 5:
                    self.bot.config.set("feed" + str(num) + ".waitFactor",\
                        options[4], "feed", self.bot.network, channel)
                if len(options) >= 4:
                    self.bot.config.set("feed" + str(num) + ".maxWait",\
                        options[3], "feed", self.bot.network, channel)
                if len(options) >= 3:
                    self.bot.config.set("feed" + str(num) + ".minWait",\
                        options[2], "feed", self.bot.network, channel)
                if len(options) >= 2:
                    self.bot.config.set("feed" + str(num) + ".postMax",\
                        options[1], "feed", self.bot.network, channel)
                if len(options) >= 1 and len(options[0]):
                    self.bot.config.set("feed" + str(num) + ".url",\
                        options[0], "feed", self.bot.network, channel)
                else:
                    self.bot.sendmsg(channel, "Error: Syntax "+
                        u"!addfeed url postMax minWait maxWait factor")
                    return
                self.bot.config.set("numFeeds", num, "feed",\
                    self.bot.network, channel)
                self.loadSource(num, channel)
