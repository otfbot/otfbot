#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# (c) 2011 by Robert Weidlich
#
# AmqpFactory and AmqpProtocol based on code from txamqp_helpers
#   (c) 2010 by Dan Siemon <dan at coverfire dot com>
#

"""
    Providing a client interface to IRC
"""
from twisted.application import internet, service
from twisted.internet import protocol, reactor, error, ssl
from twisted.words.protocols import irc
from twisted.internet.defer import inlineCallbacks, Deferred

import logging
import string
import time
from threading import Lock
import gettext
import traceback

from otfbot.lib.pluginSupport import pluginSupport
from otfbot.lib.user import IrcUser, MODE_CHARS, MODE_SIGNS

from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient

import txamqp
import simplejson

# TODO: support plugins, cleanup


class Meta:
    depends = ['ircClient', 'auth', 'control']


def my_callback(msg):

    print msg.content.body
    print type(msg.fields)
    print type(msg.method)
    print msg.fields[-1]
    print "Callback received: ", msg

class botService(service.MultiService):
    name = "amqp"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        service.MultiService.__init__(self)

    def handle_command(self, msg):
        routing_key = msg.fields[-1]
        try:
            content = simplejson.loads(msg.content.body)
            if "commands" in content:
                if not isinstance(content['commands'], (list, tuple)):
                    content['commands']=[content['commands'],]
                for c in content['commands']:
                    rv = self.controlservice.handle_command(c)
                    if rv:
                        self.logger.warning("Error while executing command %s: %s" % (c, rv))
            else:
                self.logger.warning("No command in amqp-message found")                    
        except simplejson.JSONDecodeError:
            self.logger.warning("Could not decode json data")
            return

    def startService(self):
        """
        start the service

        registers control-commands, connects to the configured networks
        and then calls MultiService.startService

        """
        self.logger = logging.getLogger(self.name)
        self.config = self.root.getServiceNamed('config')

        self.controlservice = self.root.getServiceNamed('control')
#        if not self.controlservice:
#            logger.warning("cannot register control-commands as " +
#                            "no control-service is available")
#        else:
#            self.register_ctl_command(self.connect)
#            self.register_ctl_command(self.disconnect)
#            self.register_ctl_command(lambda: self.namedServices.keys(),
#                                      name="list")

        self.connect()
        service.MultiService.startService(self)

    def connect(self):
        """
            connect to the network
            @ivar network: the name of the network to connect to as used in the config

            gets the servername and port from config, and then connects to the network.
        """

        __spec_file = "otfbot/services/amqp0-8.stripped.rabbitmq.xml"
        __vhost = self.config.get("vhost", "/", self.name)
        __user = self.config.get("user", "guest", self.name)
        __password = self.config.get("password", "guest", self.name)

        f = AmqpFactory(self.root, self.parent, __spec_file, __vhost, __user, __password)

        __ssl = self.config.getBool("ssl", False, self.name)

        __host = self.config.get("host", "localhost", self.name)
        __port = int(self.config.get("port", 5672, self.name))

        if __ssl:
            s = ssl.ClientContextFactory()
            serv = internet.SSLClient(host=__host, port=__port, factory=f,
                                           contextFactory=s)
            repr = "<AMQP Connection with SSL to %s:%s>"
            serv.__repr__ = lambda: repr % (__host, __port)
            serv.factory = f
        else:
            serv = internet.TCPClient(host=__host, port=__port, factory=f)
            serv.__repr__ = lambda: "<AMQP Connection to %s:%s>" % (__host, __port)
            serv.factory = f
        f.service = serv
        serv.setName("amqp")
        serv.parent = self

        print "connecting signals"
        f.read("otfbot", "otfbot", self.handle_command)

        self.addService(serv)

    def register_ctl_command(self, f, namespace=None, name=None):
        if self.controlservice:
            if namespace is None:
                namespace = []
            if not type(namespace) == list:
                namespace = [namespace, ]
            namespace.insert(0, self.name)
            self.controlservice.register_command(f, namespace, name)


class AmqpProtocol(AMQClient):
    """The protocol is created and destroyed each time a connection is created and lost."""

    def connectionMade(self):
        """Called when a connection has been made."""
        AMQClient.connectionMade(self)

        # Flag that this protocol is not connected yet.
        self.connected = False

        # Authenticate.
        deferred = self.start({"LOGIN": self.factory.user, "PASSWORD": self.factory.password})
        deferred.addCallback(self._authenticated)
        deferred.addErrback(self._authentication_failed)

    def _authenticated(self, ignore):
        """Called when the connection has been authenticated."""
        # Get a channel.
        d = self.channel(1)
        d.addCallback(self._got_channel)
        d.addErrback(self._got_channel_failed)

    def _got_channel(self, chan):
        self.chan = chan

        d = self.chan.channel_open()
        d.addCallback(self._channel_open)
        d.addErrback(self._channel_open_failed)

    def _channel_open(self, arg):
        """Called when the channel is open."""

        # Flag that the connection is open.
        self.connected = True

        # Now that the channel is open add any readers the user has specified.
        for l in self.factory.read_list:
            self.setup_read(l[0], l[1], l[2])

        # Send any messages waiting to be sent.
        self.send()

        # Fire the factory's 'initial connect' deferred if it hasn't already
        if not self.factory.initial_deferred_fired:
            self.factory.deferred.callback(self)
            self.factory.initial_deferred_fired = True

    def read(self, exchange, routing_key, callback):
        """Add an exchange to the list of exchanges to read from."""
        if self.connected:
            # Connection is already up. Add the reader.
            self.setup_read(exchange, routing_key, callback)
        else:
            # Connection is not up. _channel_open will add the reader when the
            # connection is up.
            pass

    # Send all messages that are queued in the factory.
    def send(self):
        """If connected, send all waiting messages."""
        if self.connected:
            while len(self.factory.queued_messages) > 0:
                m = self.factory.queued_messages.pop(0)
                self._send_message(m[0], m[1], m[2])

    # Do all the work that configures a listener.
    @inlineCallbacks
    def setup_read(self, exchange, routing_key, callback):
        """This function does the work to read from an exchange."""
        queue = exchange  # For now use the exchange name as the queue name.
        consumer_tag = exchange  # Use the exchange name for the consumer tag for now.

        # Declare the exchange in case it doesn't exist.
        yield self.chan.exchange_declare(exchange=exchange, type="topic", durable=True, auto_delete=False)

        # Declare the queue and bind to it.
        yield self.chan.queue_declare(queue=queue, durable=True, exclusive=False, auto_delete=False)
        yield self.chan.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)

        # Consume.
        yield self.chan.basic_consume(queue=queue, no_ack=True, consumer_tag=consumer_tag)
        queue = yield self.queue(consumer_tag)

        # Now setup the readers.
        d = queue.get()
        d.addCallback(self._read_item, queue, callback)
        d.addErrback(self._read_item_err)

    def _channel_open_failed(self, error):
        print "Channel open failed:", error

    def _got_channel_failed(self, error):
        print "Error getting channel:", error

    def _authentication_failed(self, error):
        print "AMQP authentication failed:", error

    @inlineCallbacks
    def _send_message(self, exchange, routing_key, msg):
        """Send a single message."""
        # First declare the exchange just in case it doesn't exist.
        yield self.chan.exchange_declare(exchange=exchange, type="direct", durable=True, auto_delete=False)

        msg = Content(msg)
        msg["delivery mode"] = 2  # 2 = persistent delivery.
        d = self.chan.basic_publish(exchange=exchange, routing_key=routing_key, content=msg)
        d.addErrback(self._send_message_err)

    def _send_message_err(self, error):
        print "Sending message failed", error

    def _read_item(self, item, queue, callback):
        """Callback function which is called when an item is read."""
        # Setup another read of this queue.
        d = queue.get()
        d.addCallback(self._read_item, queue, callback)
        d.addErrback(self._read_item_err)

        # Process the read item by running the callback.
        callback(item)

    def _read_item_err(self, error):
        print "Error reading item: ", error


class AmqpFactory(protocol.ReconnectingClientFactory):
    protocol = AmqpProtocol

    def __init__(self, root, parent, spec_file=None, vhost=None, user=None, password=None):
        spec_file = spec_file or 'amqp0-8.xml'
        self.spec = txamqp.spec.load(spec_file)
        self.user = user or 'guest'
        self.password = password or 'guest'
        self.vhost = vhost or '/'
        self.delegate = TwistedDelegate()
        self.deferred = Deferred()
        self.initial_deferred_fired = False

        self.p = None  # The protocol instance.
        self.client = None  # Alias for protocol instance

        self.queued_messages = []  # List of messages waiting to be sent.
        self.read_list = []  # List of queues to listen on.

        self.root = root
        self.parent = parent

        self.config = root.getServiceNamed('config')
        self.logger = logging.getLogger("amqp")

    def buildProtocol(self, addr):
        p = self.protocol(self.delegate, self.vhost, self.spec)
        p.factory = self  # Tell the protocol about this factory.

        self.p = p  # Store the protocol.
        self.client = p

        # Reset the reconnection delay since we're connected now.
        self.resetDelay()

        return p

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        print "Client connection lost."
        self.p = None

        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def send_message(self, exchange=None, routing_key=None, msg=None):
        """Send a message."""
        # Add the new message to the queue.
        self.queued_messages.append((exchange, routing_key, msg))

        # This tells the protocol to send all queued messages.
        if self.p != None:
            self.p.send()

    def read(self, exchange=None, routing_key=None, callback=None):
        """Configure an exchange to be read from."""
        assert(exchange != None and routing_key != None and callback != None)

        # Add this to the read list so that we have it to re-add if we lose the connection.
        self.read_list.append((exchange, routing_key, callback))

        # Tell the protocol to read this if it is already connected.
        if self.p != None:
            self.p.read(exchange, routing_key, callback)
