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
# (c) 2008 by Alexander Schier
#

from twisted.internet import reactor, protocol
from twisted.internet.tcp import Server
from twisted.words.protocols.irc import IRC
from twisted.words.protocols import irc
from twisted.words.service import IRCUser
from twisted.application import service, internet

import logging, traceback, sys, time, glob, traceback

from otfbot.lib import chatMod
from otfbot.lib.pluginSupport import pluginSupport

class MyTCPServer(internet.TCPServer):
    """
        TCPServer, which has self.root, self.parent and self.factory
    """
    def __init__(self, root, parent, *args, **kwargs):
        self.root=root
        self.parent=parent
        self.factory=kwargs['factory']
        internet.TCPServer.__init__(self, *args, **kwargs)

class botService(service.MultiService):
    """
        botService spawning MYTCPServer instances using Server as protocol
    """

    name="ircServer"

    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        self.instances=[]
        service.MultiService.__init__(self)

    def startService(self):
        try:
            self.config=self.root.getServiceNamed('config')
            port=int(self.config.get("port", "6667", "server"))
            interface=interface=self.config.get("interface", "127.0.0.1", "server")
            factory=ircServerFactory(self.root, self)
            serv=MyTCPServer(self.root, self, port=port, factory=factory, interface=interface)
            self.addService(serv)
            service.MultiService.startService(self)  
        except Exception, e:
            logger=logging.getLogger("server")
            logger.error(e)
            tb_list = traceback.format_tb(sys.exc_info()[2])[1:]
            for entry in tb_list:
                for line in entry.strip().split("\n"):
                    logger.error(line)


class Server(IRCUser, pluginSupport):
    """
        the server protocol, implemending pluginSupport and IRCUser
    """
    pluginSupportName="ircServer"
    pluginSupportPath="otfbot/plugins/ircServer"

    def __init__(self, root, parent):
        pluginSupport.__init__(self, root, parent)

        self.name="nickname"
        self.user="user"
        self.loggedon=False
        self.logger=logging.getLogger("server")
        self.classes=[]
        self.config=root.getServiceNamed('config')

        self.startPlugins()

    def handleCommand(self, command, prefix, params):
        """Determine the function to call for the given command and call
        it with the given arguments.
        """
        ###twisted handling###
        #method = getattr(self, "irc_%s" % command, None)
        #try:
        #    if method is not None:
        #        method(prefix, params)
        #    else:
        #        self.irc_unknown(prefix, command, params)
        #except:
        #    log.deferr()
        ###we use _apirunner instead###
        self._apirunner("irc_%s"%command, {'prefix': prefix, 'params': params})

    def connectionMade(self):
        self._apirunner("connectionMade")
        self.logger.info("connection made")
        self.connected=True

    def connectionLost(self, reason):
        self.connected=False
        self.parent.instances.remove(self)

    def getHostmask(self):
        return "%s!%s@%s"%(self.name, self.user, self.hostname)

    def sendmsg(self, user, channel, msg):
        if self.connected:
            self.privmsg(user, channel, msg)

    def action(self, user, channel, msg):
        if self.connected:
            self.sendLine(":%s PRIVMSG %s :ACTION %s"%(user, channel, msg))

    def stop(self):
        self._apirunner("stop")
        for mod in self.plugins.keys():
            del(self.plugins[mod])
        self.plugins={}


class ircServerFactory(protocol.ServerFactory):
    """
        Factory building Server instaces, used by twisted
    """

    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        self.config=root.getServiceNamed('config')

        self.protocol=Server

    def buildProtocol(self, addr):
        """ 
            builds the protocol and appends the instance to parent.intances

            @return: the instance
        """
        p=self.protocol(self.root, self.parent)
        self.parent.instances.append(p)
        return p
