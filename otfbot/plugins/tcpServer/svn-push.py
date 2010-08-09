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
    Listens on the LineRecieved events from tcpServer and talks to the
    ircClient plugin "svn-push" to notify it of new commits
"""

from otfbot.lib.pluginSupport.decorators import callback
from otfbot.lib import chatMod
import logging


class Plugin(chatMod.chatMod):
    """
        svn-push tcpServer plugin

        You can find all settings for this module in the
        ircClient.svn-push documentation
    """
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("server")
        self.bot.depends_on_service("ircClient",
                description="This plugin needs the ircClient service to run")
        self.bot.depends_on_plugin("svn-push",
                description="This plugin needs ircClient.svn-push to work",
                service="ircClient")
        self.ircClient = bot.root.namedServices['ircClient']
        self.networks = []
        # check if networks have been configured, otherwise take all networks
        networks = self.bot.config.get("svn-push.networks",
                                      self.ircClient.namedServices.keys(),
                                      "main")
        for network in networks:
            try:
                self.networks.append(
                    self.ircClient.namedServices[network])
            except KeyError:
                self.logger.error("Network " +
                                  str(network) +
                                  " does not exist. Please check \
                                    your config file")

        self.plugins = []
        for network in self.networks:
            try:
                self.plugins.append(network.protocol.plugins['ircClient.svn-push'])
            except KeyError:
                self.logger.error("Network " +
                                  network +
                                  " does not have the svn-push plugin. \
                                    Please check your config file")

        if not self.plugins:
            raise self.bot.WontStart("it doesn't have any ircClient.svn-push \
                                      plugins connected to it")

    @callback
    def lineReceived(self, line):
        """
            Called when a line is received. Check if the commands are for this
            plugin and call ircClient.svn-push when this is the case
        """
        plugin = line.split(" ", 1)
        if plugin[0].lower() == "svn":
            command = line.split(" ", 4)
            if len(command) == 4 and command[1].lower() == "commit":
                repo = command[2] # URL of the repository
                try:
                    commit = int(command[3]) # Revision number of the commit
                except ValueError:
                    self.logger.warn("Revision number not integer!")
                self.logger.info("New commit on " + repo +
                                 " with the revision " + str(commit))
                for plugin in self.plugins:
                    plugin.commit(repo, commit)

            command = line.split(" ", 4)
            if len(command) == 5 and command[1].lower() == "buildresult":
                # result of automatic compilation (buildbot etc)
                # the last argument can be multiple words
                repo = command[2]
                try:
                    commit = int(command[3])
                except ValueError:
                    self.logger.warn("Revision number not integer!")
                    return 1
                # build result of the compilation.
                # The ircClient plugin cares about input validation here
                result = command[4]

                self.logger.info("New buildresult on " + repo + " r" +
                                 str(commit) + ": " + result)
                for plugin in self.plugins:
                    plugin.buildResult(repo, commit, result)
