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
# (c) 2015 by Robert Weidlich
#

from otfbot.lib.pluginSupport import plugin
from otfbot.lib.pluginSupport.decorators import callback

import logging


class Plugin(plugin.Plugin):

    def __init__(self, wps):
        self.wps = wps
        self.logger = logging.getLogger("count")

    @callback
    def GET(self, path, headers, request):
        res = ""
        if path == '/users':
            ircClient = self.wps.root.getServiceNamed("ircClient")
            ns = ircClient.namedServices
            for n in list(ns.keys()):
                if not ns[n] or not ns[n].protocol:
                    self.logger.warning("Error, %s is not connected." % n)
                    continue
                # cud=ns[n].protocol.getChannelUserDict()
                for c in ns[n].protocol.channels:
                    ops = 0
                    hops = 0
                    voices = 0
                    # for user in cud[c].keys():
                    #     if cud[c][user] & ns[n].protocol.rev_modchars['o']:
                    #         ops+=1
                    #     elif cud[c][user] & ns[n].protocol.rev_modchars['h']:
                    #         hops+=1
                    #     elif cud[c][user] & ns[n].protocol.rev_modchars['v']:
                    #         voices+=1
                    # wfile.write("%s.%s: %s\n"%(n, c, len(cud[c])))
                    output = "%s.%s: %s\n" % (
                        n, c, len(ns[n].protocol.getUsers(c)))
                    res += output
                    # wfile.write("%s.%s.total: %s\n"%(n, c, len(cud[c])))
                    # wfile.write("%s.%s.ops: %s\n"%(n, c, ops))
                    # wfile.write("%s.%s.hops: %s\n"%(n, c, hops))
                    # wfile.write("%s.%s.voices: %s\n"%(n, c, voices))
            return (self.wps.NO_FURTHER_PROCESSING, res)
        if path == '/lines':
            for network in self.wps.root.getServiceNamed("ircClient").services:
                if network and network.protocol:  # no NoneType Exception on disconnected network
                    for channel in network.protocol.channels:
                        res += "%s.%s: %s\n" % (network.name, channel, network.protocol.plugins[
                                                'ircClient.statistics'].getLinesPerMinute(channel))
            return (self.wps.NO_FURTHER_PROCESSING, res)
        if path == '/active_users':
            # TODO: duplicate code, refactor me!
            for network in self.wps.root.getServiceNamed("ircClient").services:
                if network and network.protocol:  # no NoneType Exception on disconnected network
                    for channel in network.protocol.channels:
                        res += "%s.%s: %s\n" % (network.name, channel, network.protocol.plugins[
                                                'ircClient.statistics'].getActiveUsersCount(channel))
            return (self.wps.NO_FURTHER_PROCESSING, res)
# app.getServiceNamed("ircClient").services[0].protocol.plugins['plugins.ircClient.ki']
