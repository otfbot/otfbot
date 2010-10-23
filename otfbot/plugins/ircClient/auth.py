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
# (c) 2006 - 2010 by Robert Weidlich
# (c) 2008 - 2010 by Thomas Wiegart
#

"""
    Authenticates a user to the Bot
"""

from twisted.cred.credentials import UsernamePassword
from twisted.words.iwords import IUser

from otfbot.lib import chatMod
from otfbot.lib.user import BotUser
from otfbot.lib.user import IrcUser
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(chatMod.chatMod):
    """
        Make a query to the bot to prove the users identity:

        Use C{msg <bot> identify <password>} if the user name in the bot is
        equal to the IRC-Nickname. Use C{msg <bot> identify <user> <password>}
        to explicitly specify a user.
    """

    def __init__(self, bot):
        self.bot = bot

    @callback
    def query(self, user, channel, msg):
        """
        Uses the auth-service to identify a user.
        If no username is given, the nickname is used.
        """
        _=self.bot.get_gettext()
        if user.getNick().lower() == self.bot.nickname.lower():
            return
        nick = user.getNick()
        if msg[0:9] == "identify ":
            portal = self.bot.root.getServiceNamed("auth")
            if not portal:
                self.bot.sendmsg(nick, _("Error: could not get portal"))
                return
            msgs = msg.split(" ")
            if len(msgs) == 2:
                cred = UsernamePassword(nick, msgs[1])
            elif len(msgs) == 3:
                cred = UsernamePassword(msgs[1], msgs[2])
            else:
                self.bot.sendmsg(nick, _("Usage: identify [user] pass"))
                return

            d = portal.login(cred, user, IUser)
            msg = _("Successfully logged in as %s")
            d.addCallback(lambda args: self.bot.sendmsg(nick, msg 
                % args[1].name))
            fail = _("Login failed: %s")
            d.addErrback(lambda failure: self.bot.sendmsg(nick, fail 
                % failure.getErrorMessage()))

    @callback
    def auth(self, user):
        """
        Returns the access-level of the given user.
        """
        if user.avatar is not None:
            return 10
        else:
            return 0
