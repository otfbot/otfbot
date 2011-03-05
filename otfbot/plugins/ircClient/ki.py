# -*- coding: UTF-8 -*-
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
# (c) 2005, 2006 by Alexander Schier
#

"""
    Try to emulate a normal user by answering
"""

import string, re, random, time, os.path
import urllib, urllib2, socket

from otfbot.lib import chatMod, functions
from otfbot.lib.eliza import eliza
from otfbot.lib.pluginSupport.decorators import callback
from otfbot.lib.color import filtercolors

import yaml

MEGAHAL = 1
NIALL = 1
try:
    import mh_python
except ImportError:
    MEGAHAL = 0
try:
    from otfbot.lib import pyniall_sqlite
except ImportError:
    NIALL = 0

class Meta:
    service_depends = ['scheduler']

class responder:
    """a prototype of a artificial intelligence responder. 
    It does nothing at all, but it contains all the methods
    needed to extend it for a ai-responder"""
    def __init__(self):
        pass
    def learn(self, string):
        """learns a new string, without responding"""
        pass
    def reply(self, msg):
        """reply to a string, potentially learning it"""
        return ""
    def cleanup(self):
        """cleanup before shutdown, if needed"""
        pass

def ascii_string(msg):
    """
    make sure, the string uses only ascii chars
    (at the moment it removes any char but a-ZA-Z@. and space)

    Example:

    >>> ascii_string("Umlaute: äöüÜÖÄß!")
    'Umlaute aeoeueUeOeAess'
    """
    mapping = {
            "ö": "oe",
            "ä": "ae",
            "ü": "ue",
            "Ü": "Ue",
            "Ä": "Ae",
            "Ö": "Oe",
            "ß": "ss"}
    msg = filtercolors(msg)
    for key in mapping.keys():
        msg = re.sub(key, mapping[key], msg)
        try:
            msg = re.sub(key.decode("iso-8859-15").encode("utf-8"), mapping[key], msg)
        except UnicodeDecodeError:
            pass
        except UnicodeEncodeError:
            pass
        try:
            msg = re.sub(key.decode("utf-8").encode("iso-8859-15"), mapping[key], msg)
        except UnicodeDecodeError:
            pass
        except UnicodeEncodeError:
            pass
    return re.sub("[ ]+", " ", re.sub("[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890@.!?;:/%\$\-_ ]", " ", msg))

class udpResponder(responder):
    def __init__(self, bot):
        self.bot = bot
        self.host = self.bot.config.get("host", "", "ki", self.bot.network)
        self.remoteport = int(self.bot.config.get("remoteport", "", "ki", self.bot.network))
        self.localport = int(self.bot.config.get("localport", "", "ki", self.bot.network))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(10)
        self.socket.bind(("", self.localport))
    def learn(self, msg):
        self.socket.sendto(msg, (self.host, self.remoteport))
        self.socket.recvfrom(8 * 1024)
    def reply(self, msg):    
        self.socket.sendto(msg, (self.host, self.remoteport))
        return ascii_string(self.socket.recvfrom(8 * 1024)[0].strip())

class webResponder(responder):
    def __init__(self, bot):
        self.bot = bot
    def learn(self, msg):
        url = self.bot.config.get("url", "", "ki", self.bot.network)
        urllib2.urlopen(url + urllib.quote(msg)).read()
    def reply(self, msg):    
        url = self.bot.config.get("url", "", "ki", self.bot.network)
        return ascii_string(urllib2.urlopen(url + urllib.quote(msg)).read())

class niallResponder(responder):
    def __init__(self, bot, datadir):
        self.niall = pyniall_sqlite.pyNiall(datadir + "/%s.db" % bot.network)
    def learn(self, msg):
        msg = ascii_string(msg)
        if msg:
            self.niall.learn(msg)
    def reply(self, msg):
        msg = ascii_string(msg)
        reply = self.niall.reply(str(msg))
        if reply == None:
            reply = ""
        return reply
    def cleanup(self):
        self.niall.cleanup()

class elizaResponder(responder):
    def __init__(self, bot, datadir):
        self.eliza = eliza()
        if os.path.exists(datadir + "/eliza.yaml"):
            file = open(datadir + "/eliza.yaml")
            data = file.read()
            file.close()
            tmp = yaml.load(data)
            self.eliza.setReflections(tmp[0])
            self.eliza.setPatterns(tmp[1])
    def reply(self, msg):
        return self.eliza.reply(msg)

class megahalResponder(responder):
    """implements a responder based on the megahal ai-bot"""
    def __init__(self, bot):
        """starts the megahal program"""
        try:
            mh_python.setnobanner()
            mh_python.setdir(datadir)
        except:
            pass
        mh_python.initbrain()
        self.bot = bot
    def learn(self, msg):
        """learns msg without responding
        @type    msg:    string
        @param    msg:    the string to learn
        """
        mh_python.learn(msg.encode("iso-8859-15"))
    def reply(self, msg):
        """replies to msg, and learns it
        @param    msg: the string to reply to
        @type    msg: string
        @rtype: string
        @returns the answer of the megahal bot
        """
        string = msg.encode("iso-8859-15")
        return unicode(mh_python.doreply(string), "iso-8859-15")

    def cleanup(self):
        """clean megahal shutdown"""
        mh_python.cleanup()



class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot = bot
        self.exit=False

    def start(self):
        self.channels = []
        self.wordpairsFile = self.bot.config.getPath("wordpairsFile",
            datadir, "wordpairs.txt")
        self.wordpairs = functions.loadProperties(self.wordpairsFile, 
            self.bot.config.get("wordpairsEncoding", "UTF-8", "ki", 
            self.bot.network) )
        #TODO: use self.bot.user_list
        self.nicklist = [string.lower(self.bot.nickname)]

        module = self.bot.config.get("module", "megahal", "ki", 
            self.bot.network)
        self.logger.debug("ki: using module " + module + 
            ",megahal=" + str(MEGAHAL) + ",niall=" + str(NIALL))
        if module == "niall":
            if NIALL:
                self.responder = niallResponder(self.bot, datadir)
                self.logger.info("ki: using niall module")
            else:
                self.logger.warning("Cannot use niall. Module niall not availible.")
                if MEGAHAL:
                    self.logger.info("Using Megahal instead")
                    self.responder = megahalResponder(self.bot)
                else:
                    self.logger.info("Using no KI.")
                    self.responder = responder() #null responder
        elif module == "megahal":
            if MEGAHAL:
                self.responder = megahalResponder(self.bot)
            else:
                self.logger.warning("Cannot use megahal. Module mh_python not availible.")
                self.responder = responder() #null responder
                #Fallback
                if NIALL:
                    self.logger.warning("Trying niall instead.")
                    self.responder = niallResponder(self.bot, datadir)
        elif module == "web":
            self.responder = webResponder(self.bot)
        elif module == "udp":
            self.responder = udpResponder(self.bot)
        elif module == "eliza":
            self.responder = elizaResponder(self.bot, datadir)

    @callback
    def joined(self, channel):
        self.channels.append(channel)

    @callback
    def query(self, user, channel, msg):
        if msg[0] == "!":
            return
        if not self.bot.config.get("ignoreQuery", True, "ki", self.bot.network):
            ## ignoreQuery should be set to True if you're using auth.
            ## Else the ki also saves your username and password and maybe posts it in public!
            user = user.getNick()
            if user[0:len(self.bot.nickname.lower())] == self.bot.nickname.lower():
                return
            if user.lower() == self.bot.nickname.lower() or string.lower(user) in self.bot.config.get("ignore", [], "ki", self.bot.network):
                return
            reply = self.responder.reply(msg)
            if not reply:
                return
            number = random.randint(1, 1000)
            chance = int(self.bot.config.get("answerQueryPercent", 70, "ki", self.bot.network)) * 10
            delay = len(reply) * 0.3 * float(self.bot.config.get("wait", 2, "ki", self.bot.network)) #a normal user does not type that fast
            if number < chance:
                #self.bot.sendmsg(user, reply, "UTF-8")
                self.bot.root.getServiceNamed('scheduler').callLater(delay, self.bot.sendmsg, user, reply, "UTF-8")

    @callback
    def action(self, user, channel, msg):
        self.msg(user, channel, msg)
    
    @callback
    def msg(self, user, channel, msg):
        user = user.getNick().lower()
        if not user in self.nicklist:
            self.nicklist.append(user)
        if user in self.bot.config.get("ignore", [], "ki", self.bot.network, channel):
            return

        if user == self.bot.nickname.lower():
            return
        #if not channel in self.channels: 
        #    return
        if msg[0] == "!":
            return
            

        reply = ""

        #bot answers random messages
        number = random.randint(1, 1000)
        chance = int(float(self.bot.config.get("randomPercent", 0, "ki", self.bot.network, channel)) * 10)
        israndom = 0
        if number < chance:
            israndom = 1
        #bot answers if it hears its name
        ishighlighted = self.bot.nickname.lower() in string.lower(msg)
            

        #test, if it starts with user:
        for nick in self.nicklist:
            if string.lower(msg[0:len(nick)]) == nick:
                msg = msg[len(nick) + 1:] #cut of len of nick + one char (":", ",", " ", etc.)

        if len(msg) and msg[0] == " ": 
            msg = msg[1:]

        channel = string.lower(channel)
        if ishighlighted or israndom:
            reply = self.responder.reply(msg)
        else:
            self.responder.learn(msg)

        if reply:
            #reply=re.sub(" "+self.bot.nickname, " "+user, reply) #more secure to match only the name
            reply = re.sub(self.bot.nickname.lower(), user, str(reply), re.I) 
            for key in self.wordpairs.keys():
                reply = re.sub(key, self.wordpairs[key], reply, re.I)
            
            reply = re.sub("Http", "http", reply, re.I) #fix for nice urls

            if reply == string.upper(reply): #no UPPERCASE only Posts
                reply = string.lower(reply)
            delay = len(reply) * 0.3 * float(self.bot.config.get("wait", 2, "ki", self.bot.network, channel)) #a normal user does not type that fast
            number = random.randint(1, 1000)
            chance = int(self.bot.config.get("answerPercent", 50, "ki", self.bot.network, channel)) * 10
            if israndom:
                #self.bot.sendmsg(channel, reply, "UTF-8")
                self.bot.root.getServiceNamed('scheduler').callLater(delay, self.bot.sendmsg, channel, reply, "UTF-8")
            elif number < chance: #apply answerPercent only on answers
                #self.bot.sendmsg(channel, user+": "+reply, "UTF-8")
                self.bot.root.getServiceNamed('scheduler').callLater(delay, self.bot.sendmsg, channel, user + ": " + reply, "UTF-8")

    @callback
    def connectionLost(self, reason):
        if not self.exit:
            self.exit=True
            self.responder.cleanup()

    @callback
    def stop(self):
        if not self.exit:
            self.exit=True
            self.responder.cleanup()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
