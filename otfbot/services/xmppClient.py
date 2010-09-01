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

from twisted.application import service
from wokkel.xmppim import MessageProtocol, AvailablePresence
from twisted.words.protocols.jabber import jid
from wokkel.client import XMPPClient

import logging

from otfbot.lib.pluginSupport import pluginSupport





class botService(service.MultiService):
    name = "xmppClient"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.logger = logging.getLogger("xmppClient")
        self.config = self.root.getServiceNamed('config')
        service.MultiService.__init__(self)
        try:
            myjid=self.config.get("jid", "", "main.xmppClient")
            password=self.config.get("password", "", "main.xmppClient")
            if not (myjid and password):
                self.logger.warn("please set main.xmppClient.jid "+\
                    "and main.xmppClient.password")
                return
            self.client = XMPPClient(jid.internJID(myjid+"/otfbot"), password)
            self.client.logTraffic = False
            self.protocol=Bot(root, self)
            self.protocol.setHandlerParent(self.client)
            self.client.setServiceParent(self)
        except Exception, e:
            self.logger.error(e)

    def startService(self):
        try:
            service.MultiService.startService(self)
        except Exception, e:
            self.logger.error(e)

class Bot(MessageProtocol, pluginSupport):
    pluginSupportName="xmppClient"
    pluginSupportPath="otfbot/plugins/xmppClient"
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        self.logger=parent.logger
        pluginSupport.__init__(self, root, parent)
        MessageProtocol.__init__(self)
        self.startPlugins()

    def connectionMade(self):
        self.logger.debug("Connected!")
        # send initial presence
        self.send(AvailablePresence())
        self._apirunner("connectionMade", {})

    def connectionLost(self, reason):
        self.logger.debug("Disconnected")
        self._apirunner("connectionLost", {'reason': reason})

    def onMessage(self, msg):
        self._apirunner("onMessage", {'msg': msg})

