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
# (c) 2010 by Finn Wilke
#

"""
    This module gets notified by tcpServer.svn whenever a subversion
    repository gets updated. It then posts the commit information
    to the channel specified in the config.
"""

import logging
from otfbot.lib import chatMod

HAS_PYSVN = True
try:
    import pysvn
except ImportError:
    HAS_PYSVN = False


class Plugin(chatMod.chatMod):
    """
        svn-push plugin

        Configuration:
        You need to set 'svn-push.networks' and 'svn-push.channels' if you
        don't want to have the svn messages in all of the channels your bot
        is in. Both configuration settings are of the "list" type
    """
    def __init__(self, bot):
        """
            Initialisation

            Configuration:
            You need to set 'main.svn-push.networks' and 'svn-push.channels'
            (for each network) if you don't want to have the svn messages
            in all of the channels your bot is in.
            Both configuration settings are of the "list" type
        """
        if not HAS_PYSVN:
            self.bot.depends("pysvn python module")
        self.bot = bot
        self.logger = logging.getLogger("server")
        self.ircClient = self.bot.root.getServiceNamed("ircClient")

        networks = self.bot.config.get("svn-push.networks",
                                       self.ircClient.namedServices.keys(),
                                       "main")
        if not self.bot.network in networks:
            raise self.bot.WontStart("apparently it is not needed here...")

        channels = self.bot.config.get("channels",
                            self.bot.config.getChannels(self.bot.network),
                            "svn-push",
                            network=self.bot.network)
        self.channels = []
        for channel in channels:
            if channel in self.bot.config.getChannels(self.bot.network):
                self.channels.append(channel)
            else:
                self.logger.error("Channel '" + channel +
                                  "' does not exist in network " +
                                  self.bot.network +
                                  ". Please check your config file.")
        self.svnclient = pysvn.Client()
        self.buildResults = ['green', 'yellow', 'red']

        # mIRC (and other clients) variables
        self.mirc_bold = chr(2)
        self.mirc_green = chr(3) + "3"
        self.mirc_no_color = chr(15)

    def getRev(self, url, commit):
        """ Gets revision information from the svn repo"""
        revision = pysvn.Revision(pysvn.opt_revision_kind.number, commit)
        return self.svnclient.log(url, revision, limit=1)[0]

    def commit(self, url, commit):
        """
            Called from the tcpServer plugin when a new commit has been made

            @param url: The url of the repository
            @type url: string
            @param commit: The commit revision
            @type commit: int
        """
        log = self.getRev(url, commit)
        for channel in self.channels:
            self.bot.sendmsg(channel,
                             "New commit by " +
                             self.mirc_green + log['author'] +
                             self.mirc_no_color + " (" +
                             self.mirc_bold +
                             "r" + str(log['revision'].number) +
                             self.mirc_bold + "): " +
                             log['message'])

    def buildResult(self, url, commit, result):
        """
            Called from the tcpServer plugin when a build result
            needs to be posted

            @param url: The url of the repository
            @type url: string
            @param commit: The commit revision
            @type commit: int
            @param result: The result of the build process.
                           See self.buildResults
            @type result: string
        """
        if result in self.buildResults:
            if result == "green":
                resultmsg = "All green"
            if result == "yellow":
                resultmsg = "Yellow!"
            if result == "red":
                resultmsg = "Red!"
            log = self.getRev(url, commit)
            for channel in self.channels:
                self.bot.sendmsg(channel,
                                 self.mirc_bold +
                                 "r" + str(log['revision'].number) +
                                 self.mirc_bold + " build result: " +
                                 resultmsg)
