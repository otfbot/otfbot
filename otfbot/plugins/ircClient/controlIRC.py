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
# (c) 2007 - 2010 by Robert Weidlich
#

"""
    Access the control service via IRC to control the Bot.
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):
    """
        Control the Bot as a identified user. Either query the Bot and enter
        the control mode by typing C{control} or use commands in a channel.

        An identified user can also invite the Bot to a channel.

        As unidentified user it is possible to issue a reload of a plugins
        state by typing a command like C{!reload <plugin>}.
    """

    def __init__(self, bot):
        self.bot = bot
        self.control = {}

    @callback
    def query(self, user, channel, msg):
        nick = user.getNick()
        if user in self.control and msg == "endcontrol":
            del self.control[user]
        if msg == "control" and self.bot.auth(user) > 0:
            self.control[user] = self.bot.root.getServiceNamed("control")
            welcome = "Entered configuration modus. type 'endcontrol' to exit"
            self.bot.sendmsg(nick, welcome)
        elif user in self.control:
            output = self.control[user].handle_command(msg)
            if output == None:
                output = "None"
            self.bot.sendmsg(nick, output)

    @callback
    def command(self, user, channel, command, options):
        if self.bot.auth(user) > 0:
            cmd = []
            cmd.append(command)
            control = self.bot.root.getServiceNamed("control")
            if options and options != "":
                cmd.append(options)
            r = control.handle_command(" ".join(cmd))
            if r is None:
                cmd.insert(0, self.bot.parent.parent.name)
                cmd.insert(0, self.network)
                r = control.handle_command(" ".join(cmd))
            if r is not None:
                self.bot.sendmsg(channel, r)
        if command == "reload" and len(options) > 0:
            try:
                self.bot.plugins['ircClient.' + options].reload()
                self.bot.sendmsg(channel, "Reloaded " + options)
            except KeyError:
                emsg = "Could not reload %s: No such Plugin" % options.strip()
                self.bot.sendmsg(channel, emsg)

    @callback
    def invitedTo(self, channel, inviter):
        self.logger.info("I was invited to " + channel + " by " + inviter)
        if self.bot.auth(inviter) > 0:
            self.logger.info("Accepting invitation.")
            self.bot.join(channel)
