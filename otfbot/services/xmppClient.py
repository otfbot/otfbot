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
# (c) 2010 by Alexander Schier
#

"""
    connect to a jabber account
"""

from twisted.application import service
from wokkel.xmppim import MessageProtocol, AvailablePresence,\
        PresenceClientProtocol, RosterClientProtocol
from twisted.words.protocols.jabber import jid
from wokkel.client import XMPPClient
from twisted.words.xish import domish

import logging
import gettext
import traceback

from otfbot.lib.pluginSupport import pluginSupport


class botService(service.MultiService):
    """
        xmpp botService
    """
    name = "xmppClient"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.logger = logging.getLogger("xmppClient")
        self.config = self.root.getServiceNamed('config')
        self.config.set("enabled", False, "main", network="xmpp")
        service.MultiService.__init__(self)
        self.protocol=None
        try:
            self.myjid=self.config.get("jid", "", "main.xmppClient")
            password=self.config.get("password", "", "main.xmppClient")
            if not (self.myjid and password):
                self.logger.warn("please set main.xmppClient.jid "+\
                    "and main.xmppClient.password")
                return
            self.client = XMPPClient(jid.internJID(self.myjid+"/otfbot"), password)
            self.client.logTraffic = False
            self.protocol=Bot(root, self)
            self.messageProtocol=myMessageProtocol(self.protocol)
            self.messageProtocol.setHandlerParent(self.client)
            self.presenceClientProtocol=myPresenceClientProtocol(self.protocol)
            self.presenceClientProtocol.setHandlerParent(self.client)
            self.rosterClientProtocol=myRosterClientProtocol(self.protocol)
            self.rosterClientProtocol.setHandlerParent(self.client)

            self.protocol.messageProtocol=self.messageProtocol
            self.protocol.rosterClientProtocol=self.rosterClientProtocol
            self.protocol.presenceClientProtocol=self.presenceClientProtocol

            self.client.setServiceParent(self)
        except Exception, e:
            self.logger.error(e)

    def startService(self):
        try:
            service.MultiService.startService(self)
        except Exception, e:
            self.logerror(self.logger, "xmppClient", e)

    def serviceOnline(self, servicename):
        if self.protocol:
            self.protocol.serviceOnline(servicename)
        else:
            self.logger.warn("I have no protocol and i want to cry")

class myMessageProtocol(MessageProtocol):
    def __init__(self, bot):
        self.bot=bot
        MessageProtocol.__init__(self)
    def onMessage(self, *args, **kwargs):
        try:
            self.bot.onMessage(*args, **kwargs)
        except Exception, e:
            self.bot.logerror(self.bot.logger, "messageProtocol", e)
    def connectionMade(self):
        try:
            self.bot.connectionMade()
        except Exception, e:
            self.bot.logerror(self.bot.logger, "messageProtocol", e)
    def connectionLost(self, reason):
        try:
            self.bot.connectionLost(reason)
        except Exception, e:
            self.bot.logerror(self.bot.logger, "messageProtocol", e)

class myRosterClientProtocol(RosterClientProtocol):
    def __init__(self, bot):
        self.bot=bot

    def onRosterSet(self, item):
        pass

class myPresenceClientProtocol(PresenceClientProtocol):
    def __init__(self, bot):
        self.bot=bot
        PresenceClientProtocol.__init__(self)

    def subscribeReceived(self, entity):
        try:
            self.subscribe(entity) #let them see our status
            self.subscribed(entity) #request their status
            self.presenceClientProtocol.update_presence() #send presence again
        except Exception, e:
            self.bot.logger.error(e)

    def unsubscribeReceived(self, entity):
        self.unsubscribe(entity) #deny our status, too

    def update_presence(self):
        self.send(AvailablePresence(statuses={
            'C': 'at your service',
            'de': 'stets zu Diensten'
        }))

class Bot(pluginSupport):
    """
        xmppClient Bot protocol
    """

    pluginSupportName="xmppClient"
    pluginSupportPath="otfbot/plugins/xmppClient"
    def __init__(self, root, parent):
        """
            initialize protocol

            @param root: reference to the application object
            @param parent: reference to the parent object
        """
        self.root=root
        self.parent=parent
        self.logger=parent.logger
        self.myjid=parent.myjid
        pluginSupport.__init__(self, root, parent)

        #ircClient compatiblity
        self.nickname=self.myjid
        self.network="xmpp"
        self.translations={}

        self.startPlugins()

    def startPlugins(self):
        pluginSupport.startPlugins(self)
        ircPlugins=self.config.get("xmppClientIRCPlugins", [], "main")
        for pluginName in ircPlugins:
            plugin=self.startPlugin(pluginName,\
                package="otfbot.plugins.ircClient")

    def connectionMade(self):
        """
            XMPP connection successfully established
        """
        self.logger.info("Connected!")
        self.presenceClientProtoco.update_presence()
        self._apirunner("connectionMade", {})

    def connectionLost(self, reason):
        """
            connection lost

            @param reason: string why the connection was lost
            @type reason: str
        """
        self.logger.info("Disconnected %s"%str(reason))
        self._apirunner("connectionLost", {'reason': reason})

    def serviceOnline(self, servicename):
        #self.logger.debug("%s went online" % servicename)
        self.startPlugins()

    def onMessage(self, msg):
        """
            XMPP message received

            @param msg: the message
        """
        self._apirunner("onMessage", {'msg': msg})
        body=unicode(msg.body)
        if msg.body and not body[:5] == "?OTR:":
            user=msg['from']
            channel=msg['to']
            try:
                self._apirunner("query", {'user': user,
                    'channel': channel, 'msg': body})
            except Exception, e:
                self.logerror(self.logger, "xmppClient", e)
            #like in IRCClient XXX: common library function?
            if body[0] == self.config.get("commandChar", "!", "main").encode("UTF-8"):
                tmp = body[1:].split(" ", 1)
                command = tmp[0]
                if len(tmp) == 2:
                    options = tmp[1]
                else:
                    options = ""

                #user = user, channel = user, because most commands are
                #answered in the channel, not to the user
                try:
                    self._apirunner("command", {"user": user, "channel": user,
                        "command": command, "options": options})
                except Exception, e:
                    self.logerror(self.logger, "xmppClient", e)

    #ircClient compatiblity
    def sendmsg(self, channel, msg, encoding="UTF-8", fallback="ISO-8859-1"):
        """
            sendmsg method simulating the ircClient.Bot.sendmsg method.
            so some ircClient plugins will work with xmppClient
        """
        try:
            if type(msg) != unicode:
                try:
                    msg=unicode(msg, encoding)
                except UnicodeDecodeError, e:
                    msg=unicode(msg, fallback)
            #self.logger.debug("To: %s"%channel)
            #self.logger.debug("From: %s"%(self.myjid+"/otfbot"))
            #self.logger.debug(msg)
            message=domish.Element((None, "message"))
            message['to'] = channel
            message['from'] = self.myjid+"/otfbot"
            message['type'] = 'chat'
            message.addElement('body', content=msg)
            self.mP.send(message)
            self._apirunner("privmsg", {'user': self.nickname, \
                'channel': channel, 'msg': msg})
            self._apirunner("query", {'user': self.nickname, \
                'channel': channel, 'msg': msg})
        except Exception, e:
            self.logerror(self.logger, "xmppClient", e)
            tb_list = traceback.format_stack(limit=6)
            for entry in tb_list:
                for line in entry.strip().split("\n"):
                    self.logger.error(line)

    def get_gettext(self, channel=None):
        """
            return a gettext function for the configured language

            @param channel: ignored, its just for compatibilty
                            with ircClient plugins
        """
        lang=self.config.get("language", None, "main", self.network)
        if not lang in self.translations and lang:
            if gettext.find("otfbot", "locale", languages=[lang]):
                self.translations[lang]=gettext.translation("otfbot", "locale", \
                    languages=[lang])
            else: #no language file found for requested language
                lang=None
        if lang:
            def _(input):
                return self.translations[lang].gettext(input)
        else:
            def _(input):
                return input
        return _
    def register_ctl_command(self, *args, **kwargs):
        """
            dummy for compatiblity with ircClient plugins
        """
        pass

