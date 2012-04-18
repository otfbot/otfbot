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
# (c) 2009 by Bjorn Edstrom
# (c) 2012 by spasswurst
#

"""
    Support for blowfish cryption on irc
"""

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback_with_priority

import struct
from Crypto.Cipher import Blowfish

class Plugin(chatMod.chatMod):
    B64 = "./0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.root.getServiceNamed("config")

    @callback_with_priority(100)
    def topicUpdated(self, user, channel, newTopic):
        key = self.getBlowkey(channel)
        if not key:
            return
        topicdecrypted = self.blowfishDecrypt(newTopic, key)
        if topicdecrypted:
            result = self.bot.FURTHER_PROCESSING_THIS_ARGS, { "newTopic" : topicdecrypted}
            return result

    @callback_with_priority(100)
    def msg(self, user, channel, msg):
        key = self.getBlowkey(channel)
        if not key:
            return
        nick = user.getNick()
        if nick.lower() != self.bot.nickname.lower(): # incoming msg?
            msg = self.blowfishDecrypt(msg, key)
            if msg:
                char = msg[0]
                if char == self.config.get("commandChar", "!", "main"):
                    tmp = msg[1:].split(" ", 1)
                    command = tmp[0]
                    if len(tmp) == 2:
                        options = tmp[1]
                    else:
                        options = ""
                    self.bot._synced_apirunner("command", {"user": user, "channel": channel,
                                                       "command": command, "options": options})
                    return self.bot.NO_FURTHER_PROCESSING
                result = self.bot.FURTHER_PROCESSING_THIS_ARGS, { "msg" : msg}
                return result

    @callback_with_priority(100)
    def sendLine(self, line):
        s = line
        if s[0] != ':' and s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
            command = args.pop(0)
            if command != "PRIVMSG":
                return

            channel = args.pop(0)
            msg = args.pop(0)
            key = self.getBlowkey(channel)
            if not key:
                return
            msg = self.blowfishCrypt(msg, key)
            line = 'PRIVMSG %s :%s' % (channel, msg)
            result = self.bot.FURTHER_PROCESSING_THIS_RESULT, { "line" : line}
            return result

    def getBlowkey(self, channel):
        if channel[0] in '#+!&':
            channel = channel.lower()
            key = self.config.get("blowkey", "", "main", self.bot.network, channel, set_default=False)
            return key

    def blowcrypt_b64decode(self, s):
        """A non-standard base64-decode."""
        res = ''
        while s:
            left, right = 0, 0
            for i, p in enumerate(s[0:6]):
                right |= self.B64.index(p) << (i * 6)
            for i, p in enumerate(s[6:12]):
                left |= self.B64.index(p) << (i * 6)
            res += struct.pack('>LL', left, right)
            s = s[12:]
        return res

    def blowcrypt_b64encode(self, s):
        """A non-standard base64-encode."""
        res = ''
        while s:
            left, right = struct.unpack('>LL', s[:8])
            for i in xrange(6):
                res += self.B64[right & 0x3f]
                right >>= 6
            for i in xrange(6):
                res += self.B64[left & 0x3f]
                left >>= 6
            s = s[8:]
        return res

    def padto(self, msg, length):
        """Pads 'msg' with zeroes until it's length is divisible by 'length'.
        If the length of msg is already a multiple of 'length', does nothing."""
        L = len(msg)
        if L % length:
            msg += '\x00' * (length - L % length)
        assert len(msg) % length == 0
        return msg

    def blowfishDecrypt(self, message, key):
        if not (message.startswith('+OK ') or message.startswith('mcps ')):
            return
        _, rest = message.split(' ', 1)

        try:
            padded = self.padto(rest, 12)
            raw = self.blowcrypt_b64decode(padded)
            bf = Blowfish.new(key)
            decrypted = bf.decrypt(raw)
            decrypted = decrypted.strip('\x00')
            return decrypted
        except ValueError:
            return

    def blowfishCrypt(self, message, key):
        try:
            padded = self.padto(message, 8)
            bf = Blowfish.new(key)
            crypted = bf.encrypt(padded)
            crypted = '+OK ' + self.blowcrypt_b64encode(crypted)
            return crypted
        except ValueError:
            return
