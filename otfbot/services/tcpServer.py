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
    Provides a tcp server interface and makes it availiable through a unix
    socket and a tcp listener
"""

from twisted.internet import protocol
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.tcp import Server
from twisted.protocols.basic import LineOnlyReceiver
from twisted.application import internet, service

import logging

from otfbot.lib.pluginSupport import pluginSupport


class botService(service.MultiService):
    name = "tcpServer"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.logger = logging.getLogger("server")
        self.logger.info("Starting listener[s]")
        self.config = self.root.getServiceNamed('config')
        service.MultiService.__init__(self)

    def startService(self):
        """
            Starts the service. It supports a unix socket and a tcp networking
            port. Configure it by setting tcpServer.modes in the config file:
            socket, tcp

            unix socket: You can set the path where the socket file is
            created by setting tcpServer.socket.path to a filesystem path
            writable by the bot user

            tcp networking: You can set the port of the port of the connection
            with tcpServer.tcp.port and the interface with
            tcpServer.tcp.interface. Default is that the port is only
            accessible from localhost.
        """
        modes = self.config.get("modes", ["socket"], "main.tcpServer")
        self.factory = tcpServerFactory(self.root, self)
        if "socket" in modes:
            path = self.config.get("socket.path",
                                   "otfbot.sock",
                                   "main.tcpServer")
            server = internet.UNIXServer(address=path, factory=self.factory)
            self.addService(server)
        if "tcp" in modes:
            port = int(self.config.get("tcp.port", "7001", "main.tcpServer"))
            interface = self.config.get("tcp.interface",
                                        "127.0.0.1",
                                        "main.tcpServer")
            server = internet.TCPServer(port=port,
                                        factory=self.factory,
                                        interface=interface)
            self.addService(server)
        if "tcp" in modes or "socket" in modes:
            try:
                service.MultiService.startService(self)
            except Exception, e:
                self.logger.error(e)


class Server(LineOnlyReceiver, pluginSupport):
    """
        This is a very simple LineOnlyReceiver.
        It only supports the callback lineReceived.
    """
    pluginSupportName = "tcpServer"
    pluginSupportPath = "otfbot/plugins/tcpServer"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.logger = logging.getLogger("server")
        self.logger.info("Starting new server")
        pluginSupport.__init__(self, root, parent)
        self.startPlugins()
        self.logger.debug("All Plugins started")

    def lineReceived(self, line):
        """ This is called when a line is received """
        self.logger.debug("Received line " + line)
        if line.lower() == "quit":
            return self.transport.loseConnection()
        self._apirunner("lineReceived", {'line': line})

    def connectionLost(self, reason):
        self.logger.debug("connection lost")
        self.parent.instances.remove(self)


class tcpServerFactory(protocol.ServerFactory):
    """
        Factory for the tcpServer
    """

    def __init__(self, root, parent):
        self.logger = logging.getLogger("server")
        self.root = root
        self.parent = parent
        self.config = root.getServiceNamed('config')
        self.instances = []
        self.protocol = Server

    def buildProtocol(self, addr):
        self.instances.append(self.protocol(self.root, self))
        return self.instances[-1]

    def stopFactory(self):
        pass
