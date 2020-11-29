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
# (c) 2010, 2011 by Alexander Schier
#

"""
    get information from an icecast-server
"""

from otfbot.lib import chatMod, urlutils
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.mountpoint = ""

    @callback
    def command(self, user, channel, command, options):
        statusurl = self.config.get("statusurl",
          "http://localhost:8000/status2.xsl",
          "icecast", self.bot.network, channel)

        if options == "":
            mountpoint = self.config.get("defaultMountpoint", "/radio.ogg", "icecast", \
              self.bot.network, channel)
        else:
            mountpoint = options

        if command == "np" or command == "listeners":
            urlutils.download(statusurl).addCallback(self.downloadFinished, \
              command, channel, mountpoint)
        elif command in ("mountpoints", "mounts"):
            urlutils.download(statusurl).addCallback(self.downloadFinished, \
              "mounts", channel, "")

    def downloadFinished(self, data, command, channel, mountpoint):
        self.logger.debug("downloadFinished %s %s" % (channel, mountpoint))
        try:
            _ = self.bot.get_gettext(channel)
            #remove header info
            lines = data.replace("</pre>", "")\
            .replace("<pre>", "").split("\n")

            #np, listeners need a mountpoint
            if command in ("np", "listeners"):
                found = False
                for line in lines:
                    parts = line.split(",")
                    if len(parts) < 6:  # doctype or header line
                        continue
                    if mountpoint in parts[0]:
                        found = True
                        if command == "np":
                            self.bot.sendmsg(channel,
                              _("np: %s (%s listeners)") %
                              (parts[5], parts[3]))
                            break
                        elif command == "listeners":
                            self.bot.sendmsg(channel, \
                              _("%s listeners") % (parts[3]))
                            break
                if not found:
                    self.bot.sendmsg(channel,
                      _('mountpoint "%s" not found') % mountpoint)
            #list mountpoints
            elif command == "mounts":
                mounts = []
                for line in lines:
                    parts = line.split(",")
                    if len(parts) < 6:  # doctype or header line
                        continue
                    if not parts[0] in ("Global", "MountPoint"):
                        mounts.append(parts[0])
                self.bot.sendmsg(channel, " ".join(mounts))
        except Exception as e:
            self.logger.error(e)
