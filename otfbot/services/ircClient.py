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
# (c) 2008 - 2010 by Robert Weidlich
# (c) 2008 - 2010 by Alexander Schier
#

"""
    Providing a client interface to IRC
"""
from twisted.application import internet, service
from twisted.internet import protocol, reactor, error, ssl
from twisted.words.protocols import irc

import logging
import string
import time

from otfbot.lib.pluginSupport import pluginSupport
from otfbot.lib.user import IrcUser, MODE_CHARS, MODE_SIGNS


class botService(service.MultiService):
    name = "ircClient"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        service.MultiService.__init__(self)

    def startService(self):
        self.controlservice = self.root.getServiceNamed('control')
        self.logger = logging.getLogger(self.name)
        self.config = self.root.getServiceNamed('config')
        if not self.controlservice:
            logger.warning("cannot register control-commands as " +
                            "no control-service is available")
        else:
            self.register_ctl_command(self.connect)
            self.register_ctl_command(self.disconnect)
            self.register_ctl_command(lambda: self.namedServices.keys(),
                                      name="list")
        for network in self.config.getNetworks():
            if self.config.getBool('enabled', 'True', 'main', network):
                self.connect(network)
        service.MultiService.startService(self)

    def connect(self, network):
        f = BotFactory(self.root, self, network)
        sname = self.config.get("server", "localhost", "main", network)
        port = int(self.config.get('port', 6667, 'main', network))
        if (self.config.getBool('ssl', False, 'main', network)):
            s = ssl.ClientContextFactory()
            serv = internet.SSLClient(host=sname, port=port,
                                      factory=f, contextFactory=s)
            repr = "<IRC Connection with SSL to %s:%s>"
            serv.__repr__ = lambda: repr % (sname, port)
        else:
            serv = internet.TCPClient(host=sname, port=port, factory=f)
            serv.__repr__ = lambda: "<IRC Connection to %s:%s>" % (sname, port)
        f.service = serv
        serv.setName(network)
        serv.parent = self
        self.addService(serv)

    def disconnect(self, network):
        if network in self.namedServices:
            self.removeService(self.namedServices[network])
            return "Disconnected from " + network
        else:
            return "Not connected to " + network

    def register_ctl_command(self, f, namespace=None, name=None):
        if self.controlservice:
            if namespace is None:
                namespace = []
            if not type(namespace) == list:
                namespace = [namespace, ]
            namespace.insert(0, self.name)
            self.controlservice.register_command(f, namespace, name)


class BotFactory(protocol.ReconnectingClientFactory):
    """The Factory for the Bot"""

    def __init__(self, root, parent, network):
        self.root = root
        self.parent = parent
        self.protocolClass = Bot
        self.network = network
        self.config = root.getServiceNamed('config')
        self.logger = logging.getLogger(network)

    def __repr__(self):
        return "<BotFactory for network %s>" % self.network

    def startedConnecting(self, connector):
        self.logger.info("Started to connect")

    def clientConnectionLost(self, connector, reason):
        self.protocol = None
        self.service.protocol = None
        if not reason.check(error.ConnectionDone):
            mstr = "Got disconnected from %s: %s"
            self.logger.warn(mstr % (connector.host, reason.getErrorMessage()))
            protocol.ReconnectingClientFactory.\
                                clientConnectionLost(self, connector, reason)
        else:
            self.parent.removeService(self.service)

    def clientConnectionFailed(self, connector, reason):
        mstr = "Connection to %s failed: %s"
        self.logger.warn(mstr % (connector.host, reason.getErrorMessage()))
        protocol.ReconnectingClientFactory.\
                                clientConnectionLost(self, connector, reason)

    def buildProtocol(self, addr):
        proto = self.protocolClass(self.root, self)
        self.protocol = proto
        self.service.protocol = proto
        self.resetDelay()
        return proto

#    def stopFactory(self):
#        #import inspect
#        #for o in inspect.stack():
#        #    self.logger.debug(str(o))
#        self.logger.info("Got Signal to stop factory, stopping service")
#        self.service.disownServiceParent()
#        self.service.stopService()


class creatingDict(dict):
    """helper class: a dict, which adds unknown keys with value 0 on access"""

    def __getitem__(self, item):
        if not item in self:
            self[item] = 0
            print "created non-existant key %s" % repr(item)
        return dict.__getitem__(self, item)


class Bot(pluginSupport, irc.IRCClient):
    """ The Protocol of our IRC-Bot
        @ivar plugins: contains references to all plugins, which are loaded
        @type plugins: list
        @ivar users: contains a dict of all users in the channels we are in
        @type users: dict
        @ivar channels: all channels we are currently in
        @type channels: list
        @ivar network: the name of the network we are connected to
        @type network: string
        @ivar logger: a instance of the standard python logger
        @ivar nickname: the nick of the bot
    """
    pluginSupportPath = "otfbot/plugins/ircClient" #path were the plugins are
    pluginSupportName = "ircClient" #prefix for config
    sourceURL = "http://www.otfbot.org/download/"
    erroneousNickFallback = "otfbot"

    modchars = {16: 'a', 8: 'o', 4: 'h', 2: 'v', 0: ' '}
    modcharvals = {16: '!', 8: '@', 4: '%', 2: '+', 0: ' '}

    def __init__(self, root, parent):
        pluginSupport.__init__(self, root, parent)
        self.config = root.getServiceNamed('config')
        self.network = self.parent.network
        self.ircClient = self.parent.parent
        self.logger = logging.getLogger(self.network)
        if self.config.getBool('answerToCTCPVersion', True, 'main', self.network):
            self.versionName = "OTFBot"
            self.versionNum = root.version.short()
            self.versionEnv = ''

        self.channels = []
        self.realname = self.config.get("realname", "A Bot", "main", self.network)
        self.password = self.config.get('password', None, 'main', self.network)
        self.nickname = self.config.get("nickname", "OtfBot", 'main', self.network)
        self.nickname = unicode(self.nickname).encode("iso-8859-1")
        self.hostmask=""
        tmp = self.config.getChannels(self.network)
        if tmp:
            self.channels = tmp

        lps = self.config.get("linesPerSecond", "2", "main", self.network)
        self.lineRate = 1.0 / float(lps)

        self.user_list={} #nick!user@host -> IRCUser
        # my usermmodess
        self.mymodes = {}
        # modes for channels
        self.channelmodes = {}
        self.serversupports = {}


        self.logger.info("Starting new Botinstance")
        self.startPlugins()
        self.register_my_commands()
        self.startTimeoutDetection()

    def startTimeoutDetection(self):
        self.lastLine = time.time()
        scheduler = self.root.getServiceNamed('scheduler')
        scheduler.callPeriodic(60, self._check_sendLastLine)

    def getUsers(self, channel=None):
        """ Get a list of users in channel
            @rtype: dict
            @return: a list of users
        """
        ret=[]
        if not channel:
            return self.user_list.values()
        for user in self.user_list:
            if self.user_list[user].hasChannel(channel):
                ret.append(self.user_list[user])
        return ret

    def _check_sendLastLine(self):
        timeout = self.config.get("timeout", 120, "main", self.network)
        if time.time() - self.lastLine > timeout:
            #self.logger.debug("Timeout in sight. Sending a ping.")
            self.ping()
        return True

    def register_ctl_command(self, f, namespace=None, name=None):
        if not self.controlservice:
            return
        if namespace is None:
            namespace = []
        if not type(namespace) == list:
            namespace = list(namespace)
        namespace.insert(0, self.network)
        self.ircClient.register_ctl_command(f, namespace, name)

    def register_my_commands(self):
        #TODO: fill this list up
        self.register_ctl_command(self.join)
        self.register_ctl_command(self.leave, name="part")
        self.register_ctl_command(self.getUsers)
        self.register_ctl_command(self.setNick, name="rename")
        self.register_ctl_command(lambda: self.channels, name="listchannels")
        self.register_ctl_command(self.kick)
        self.register_ctl_command(self.sendmsg, name="say")
        self.register_ctl_command(self.ping)

    def startPlugins(self):
        pluginSetting = self.pluginSupportName + "Plugins"
        plugins = self.config.get(pluginSetting, [], "main", set_default=False)
        disabled = self.config.get("pluginsDisabled", [], "main", self.network)
        for pluginName in plugins:
            if not pluginName in disabled:
                self.startPlugin(pluginName)

    def startPlugin(self, pluginName):
        plugin = pluginSupport.startPlugin(self, pluginName)
        #TODO: this is only a workaround until the plugins
        #      register their callbacks
        if plugin:
            for callback in dir(plugin):
                self.registerCallback(plugin, callback)

    def getFactory(self):
        """ get the factory
            @rtype: BotFactory
            @return: the current factory
        """
        return self.factory

    def auth(self, user):
        """
            call this, to see which rights C{user} has
            @type user: string
            @param user: the full hostmask of the user
            @rtype: int
            @return: the level of access rights (0 = nothing, 10 = everything)
        """
        level = 0
        for plugin in self.plugins.values():
            try:
                retval = plugin.auth(user)
                if retval > level:
                    level = retval
            except AttributeError:
                pass
        return level

    def encode_line(self, line, encoding, fallback):
        enc = self.config.get("encoding", "UTF-8", "main")
        try:
            line = unicode(line, encoding).encode(enc)
        except UnicodeDecodeError:
            #self.logger.debug("Unicode Decode Error with String:"+str(msg))
            #Try with Fallback encoding
            line = unicode(line, fallback).encode(enc)
        except UnicodeEncodeError:
            pass
            #self.logger.debug("Unicode Encode Error with String:"+str(msg))
            #use msg as is
        return line

    def sendmsg(self, channel, msg, encoding="UTF-8", fallback="iso-8859-15"):
        """
            call B{only} this to send messages to channels or users
            it converts the message from iso-8859-15 to a encoding given
            in the config
            @type     channel:     string
            @param    channel:     send the message to this channel or user
            @type     msg:         string
            @param    msg:         the message to send
            @type     encoding:    string
            @param    encoding:    the encoding of C{msg}
            @type     fallback:    string
            @param    fallback:    try this one as encoding for C{msg},
                                   if C{encoding} doesn't work
        """
        if not type(msg) == list:
            msg = [msg]
        for line in msg:
            line = self.encode_line(line, encoding, fallback)

            #From the RFC:
            # IRC messages are always lines of characters terminated with a
            # CR-LF (Carriage Return - Line Feed) pair, and these messages
            # shall not exceed 512 characters in length, counting all
            # characters including the trailing CR-LF. Thus, there are 510
            # characters maximum allowed for the command and its parameters.
            # There is no provision for continuation message lines.
            self.msg(channel, line, 450)
            self.privmsg(self.nickname, channel, line)

    def sendme(self, channel, action, encoding="UTF-8", fallback="iso8859-15"):
        """
            call B{only} this to send actions (/me) to channels
            it converts the message from iso-8859-15 to a encoding given
            in the config
            @type    channel:    string
            @param    channel:    send the message to this channel or user
            @type    action:        string
            @param    action:        the message to send
            @type    encoding:    string
            @param    encoding:    the encoding of C{msg}
            @param    fallback:    the encoding of C{msg}
        """
        if not type(action) == list:
            action = [action]
        for line in action:
            line = self.encode_line(line, encoding, fallback)
            self.describe(channel, line)
            self.action(self.nickname, channel, line)
            time.sleep(0.5)

    # Callbacks
    def connectionMade(self):
        """
            this is called by twisted
            , when the connection to the irc-server was made
        """
        self.logger.info("made connection to " + self.transport.addr[0])
        irc.IRCClient.connectionMade(self)
        self._apirunner("connectionMade")

    def connectionLost(self, reason):
        """ this is called by twisted,
            if the connection to the IRC-Server was lost
            @type reason:    twisted.python.failure.Failure
        """
        self.logger.info("lost connection: " + str(reason))
        irc.IRCClient.connectionLost(self)
        self._apirunner("connectionLost", {"reason": reason})
        self.stopPlugins()

    def signedOn(self):
        """ called by twisted,
            when we signed on the IRC-Server
        """
        self.logger.debug(self.nickname)
        self.logger.info("signed on " + self.network + " as " + self.nickname)
        channelstojoin = self.channels
        self.channels = []
        for channel in channelstojoin:
            if(self.config.getBool("enabled", "false", "main", \
                                   self.network, channel)):
                pw = self.config.get("password", "", "main", \
                                     self.network, channel)
                if (pw != ""):
                    self.join(unicode(channel).encode("iso-8859-1"),
                                            unicode(pw).encode("iso-8859-1"))
                else:
                    self.join(unicode(channel).encode("iso-8859-1"))
        self._apirunner("signedOn")

    def joined(self, channel):
        """ called by twisted,
            if we joined a channel
            @param channel: the channel we joined
            @type channel: string
        """
        channel = channel.lower()
        self.logger.info("joined " + channel)
        self.channels.append(channel)
        self.channelmodes[channel] = {}
        self.sendLine("WHO %s" % channel)
        self._apirunner("joined", {"channel": channel})
        self.config.set("enabled", True, "main", self.network, channel)

    def left(self, channel):
        """ called by twisted,
            if we left a channel
            @param channel: the channel we left
            @type channel: string
        """
        channel = channel.lower()
        self.logger.info("left " + channel)
        self._apirunner("left", {"channel": channel})
        for user in self.user_list:
            if self.user_list[user].hasChannel(channel):
                #if we do not know you're there, then you aren't there
                self.user_list[user].removeChannel(channel)
        self.channels.remove(channel)
        # disable the channel for the next start of the bot
        self.config.set("enabled", "False", "main", self.network, channel)

    def isupport(self, options):
        for o in options:
            kv = o.split('=', 1)
            if len(kv) == 1:
                kv.append(True)
            self.serversupports[kv[0]] = kv[1]
        if 'PREFIX' in self.serversupports:
            mode, sym = self.serversupports['PREFIX'][1:].split(")")
            for i in range(0, len(mode)):
                self.modchars[1 ** i] = mode[i]
                self.modcharvals[i ** i] = sym[i]
            self.rev_modchars = \
                    dict([(v, k) for (k, v) in self.modchars.iteritems()])
            self.rev_modcharvals = \
                    dict([(v, k) for (k, v) in self.modcharvals.iteritems()])

    def command(self, user, channel, command, options):
        """callback for !commands
        @param user: the user, which issues the command
        @type user: string
        @param channel: the channel to which the message was sent or my
                        nickname if it was a private message
        @type channel: string
        @param command: the !command without the !
        @type command: string
        @param options: eventual options specified
                        after !command (e.g. "!command foo")
        @type options: string"""
        channel = channel.lower()
        self._apirunner("command", {"user": user, "channel": channel,
                                    "command": command, "options": options})

    def privmsg(self, user, channel, msg):
        """ called by twisted,
            if we received a message
            @param user: the user, which send the message
            @type user: string
            @param channel: the channel to which the message was sent or my
                            nickname if it was a private message
            @type channel: string
            @param msg: the message
            @type msg: string
        """
        channel = channel.lower()
        try:
            char = msg[0].decode('UTF-8').encode('UTF-8')
        except UnicodeDecodeError:
            char = msg[0].decode('iso-8859-15').encode('UTF-8')
        if char == self.config.get("commandChar", "!", "main").encode("UTF-8"):
            tmp = msg[1:].split(" ", 1)
            command = tmp[0]
            if len(tmp) == 2:
                options = tmp[1]
            else:
                options = ""
            self._apirunner("command", {"user": user, "channel": channel,
                                       "command": command, "options": options})
            #return

        #FIXME: iirc the first line had a problem, if the bot got a nickchange
        #       from network and self.nickname != real nickname. the forced
        #       NICK should be used to update self.nickname and then we can
        #       use the first line again
        #if channel.lower() == self.nickname.lower():
        if not channel.lower()[0] in self.supported.getFeature('CHANTYPES'):
            self._apirunner("query", {"user": user,
                                      "channel": channel, "msg": msg})
            return
        # to be called for messages in channels
        self._apirunner("msg", {"user": user, "channel": channel, "msg": msg})

    def irc_unknown(self, prefix, command, params):
        """ called by twisted
            for every line that has no own callback
        """
        self._apirunner("irc_unknown", {"prefix": prefix, "command": command,
                                        "params": params})

    def noticed(self, user, channel, msg):
        """ called by twisted,
            if we got a notice
            @param user: the user which send the notice
            @type user: string
            @param channel: the channel to which the notice was sent (could be
                            our nick, if the message was only sent to us)
            @type channel: string
            @param msg: the message
            @type msg: string
        """
        channel = channel.lower()
        self._apirunner("noticed", {"user": user,
                                    "channel": channel, "msg": msg})

    def action(self, user, channel, message):
        """ called by twisted,
            if we received a action
            @param user: the user which send the action
            @type user: string
            @param channel: the channel to which the action was sent (could be
                            our nick, if the message was only sent to us)
            @type channel: string
            @param msg: the message
            @type msg: string
        """
        channel = channel.lower()
        self._apirunner("action", {"user": user, "channel": channel,
                                   "msg": message})

    def modeChanged(self, user, chan, set, modes, args):
        """ called by twisted
            if a usermode was changed
        """
        chan = chan.lower()
        user = user.lower()
        mstr = "mode change: user %s channel %s set %s modes %s args %s"
        # self.logger.debug(mstr % (user, chan, set, modes, args))
        if len(modes) != len(args):
            self.logger.debug("length of modes and args mismatched")
        elif user == chan: # my modes
            for i in range(0, len(modes)):
                if set:
                    self.mymodes[modes[i]] = args[i]
                else:
                    del self.mymodes[modes[i]]
        else:
            # track usermodes
            for i in range(0, len(modes)):
                # is a usermode
                if modes[i] in MODE_CHARS:
                    # user is known to bot
                    assert(args[i] in self.user_list)
                    if args[i] in self.user_list:
                        # user in channel
                        if set:
                            self.user_list[args[i]].setMode(chan, modes[i])
                        else:
                            self.user_list[args[i]].removeMode(chan, modes[i])
                    else:
                        self.logger.info(user + " not known to me")
                else: # channelmodes
                    am = self.supported.getFeature('CHANMODES')['addressModes']
                    if modes[i] in am: # channel modes with lists
                        if set:
                            if modes[i] not in self.channelmodes[chan]:
                                self.channelmodes[chan][modes[i]] = []
                            self.channelmodes[chan][modes[i]].append(args[i])
                        else:
                            #TODO: remove this check if fetching the initial
                            #      state works
                            if args[i] in self.channelmodes[chan][modes[i]]: 
                                self.channelmodes[chan][modes[i]].remove(args[i])
                    else: #flagging or key-value modes
                        if set:
                            self.channelmodes[chan][modes[i]] = args[i]
                        else:
                            del self.channelmodes[chan][modes[i]]
        self._apirunner("modeChanged", {"user": user, "channel": chan,
                                        "set": set, "modes": modes,
                                        "args": [str(arg) for arg in args]})

    def kickedFrom(self, channel, kicker, message):
        """ called by twisted,
            if the bot was kicked
        """
        channel = channel.lower()
        self.logger.info("I was kicked from " + channel + " by " + kicker)
        self._apirunner("kickedFrom", {"channel": channel, "kicker": kicker,
                                       "message": message})
        self.channels.remove(channel)
        # disable the channel for the next start of the bot
        self.config.set("enabled", False, "main", self.network, channel)
        for user in self.user_list:
            if self.user_list[user].hasChannel(channel):
                #if we do not know you're there, then you aren't there
                self.user_list[user].removeChannel(channel)

    def userKicked(self, kickee, channel, kicker, message):
        """ called by twisted,
            if a user was kicked
        """
        channel = channel.lower()
        self._apirunner("userKicked", {"kickee": kickee, "channel": channel,
                                       "kicker": kicker, "message": message})
        self.user_list[kickee].removeChannel(channel)
        #TODO: remove user, if len( .getChannels())==0?

    def userJoined(self, user, channel):
        """ called by twisted,
            if a C{user} joined the C{channel}
        """
        channel = channel.lower()
        nick = user.split("!")[0]
        us = user.split("@", 1)[0].split("!")[1]
        if user in self.user_list:
            u = self.user_list[user]
        else:
            u = IrcUser(nick, us, user.split("@")[1], nick, self)
            self.user_list[user]=u
        u.addChannel(channel)
        self._apirunner("userJoined", {"user": user, "channel": channel})

    def userLeft(self, user, channel):
        """ called by twisted,
            if a C{user} left the C{channel}
        """
        channel = channel.lower()
        nick = user.split("!")[0]
        self._apirunner("userLeft", {"user": user, "channel": channel})
        self.user_list[user].removeChannel(channel)
        #TODO: remove user, if len( .getChannels())==0?

    def userQuit(self, user, quitMessage):
        """ called by twisted,
            if a C{user} quits
        """
        self._apirunner("userQuit", {"user": user, "quitMessage": quitMessage})
        del(self.user_list[user])

    def yourHost(self, info):
        """ called by twisted
            with information about the IRC-Server we are connected to
        """
        #self.logger.debug(str(info))
        self._apirunner("yourHost", {"info": info})

    def ctcpUnknownQuery(self, user, channel, messages):
        """ called by twisted,
            if a C{user} sent a ctcp query
        """
        channel = channel.lower()
        self._apirunner("ctcpQuery", {"user": user, "channel": channel,
                "messages": messages})

    def userRenamed(self, oldname, newname):
        """ called by twisted,
            if a user changed his nick
        """
        self._apirunner("userRenamed", {"oldname": oldname, "newname": new})
        for user in self.user_list:
            if self.user_list[user].nick.lower()==oldname.lower():
                u=self.user_list[user]
                del(self.user_list[user])
                u.nick=newname
                self.user_list[u.getHostMask()]=u

    def topicUpdated(self, user, channel, newTopic):
        """ called by twisted
            if the topic was updated
        """
        channel = channel.lower()
        self._apirunner("topicUpdated", {"user": user,
                "channel": channel, "newTopic": newTopic})

    def irc_RPL_WHOREPLY(self, prefix, params):
        """
            "<channel> <user> <host> <server> <nick> <H|G>[*][@|+] :<hopcount> <real name>"
        """
        # modes: H = Here, G = Gone, r=registerd, B=Bot
        (t, channel, user, host, server, nick, modes, hopsrealname) = params
        channel = channel.lower()
        (hops, realname) = hopsrealname.split(" ", 1)
        mask="%s!%s@%s"%(nick, user, host)
        if mask in self.user_list:
            self.user_list[mask].realname=realname
        else:
            u = IrcUser(nick, user, host, realname, self)
            self.user_list[mask] = u
        if modes[-1] in MODE_CHARS:
            s = modes[-1]
        else:
            s = " "
        self.user_list[mask].addChannel(channel)
        self.user_list[mask].setMode(channel, s)
        self._apirunner("irc_RPL_WHOREPLY", {"channel": channel, "user": mask, "server": server, "realname": realname})

    #def irc_RPL_USERHOST(self, prefix, params):
    #    for rpl in params[1].strip().split(" "):
    #        tmp = rpl.split('=', 1)
    #        if len(tmp) == 2:
    #            (nick, hostmask) = tmp
    #        else:
    #            if not self.nickname == rpl:
    #                msgs = "Error parsing RPL_USERHOST: %s, %s"
    #                self.logger.warning(msgs % (prefix, params))
    #            continue
    #        nick = nick.replace("*", "")
    #        hm = hostmask.split('@', 1)
    #        if nick in self.userlist:
    #            self.userlist[nick].user = hm[0][1:]
    #            self.userlist[nick].host = hm[1]
    #        else:
    #            msgs = 'received RPL_USERHOST for "%s", who is not in list'
    #            self.logger.warning(msgs % nick)

    def irc_INVITE(self, prefix, params):
        """ called by twisted,
            if the bot was invited
        """
        channel = params[1].lower()
        self._apirunner("invitedTo", {"channel": channel, "inviter": prefix})

    def irc_RPL_BOUNCE(self, prefix, params):
        """ Overridden to get isupport work correctly """
        self.isupport(params[1:-1])

    def irc_JOIN(self, prefix, params):
        """ Overridden to get the full hostmask """
        nick = string.split(prefix, '!')[0]
        channel = params[-1]
        if nick.lower() == self.nickname.lower():
            self.hostmask=prefix
            self.joined(channel)
        else:
            self.userJoined(prefix, channel)

    def irc_PART(self, prefix, params):
        """ Overridden to get the full hostmask """
        nick = string.split(prefix, '!')[0]
        channel = params[0]
        if nick.lower() == self.nickname.lower():
            self.left(channel)
        else:
            self.userLeft(prefix, channel)

    def irc_QUIT(self, prefix, params):
        """ Overridden to get the full hostmask """
        self.userQuit(prefix, params[0])

    def lineReceived(self, line):
        """ called by twisted
            for every line which was received from the IRC-Server
        """
        #self.logger.debug(str(line))
        self._apirunner("lineReceived", {"line": line})
        irc.IRCClient.lineReceived(self, line)

    def sendLine(self, line):
        self.lastLine = time.time()
        self._apirunner("sendLine", {"line": line})
        #self.logger.debug(str(line))
        irc.IRCClient.sendLine(self, line)

    def ping(self):
        self.sendLine("PING %f" % time.time())

    def disconnect(self):
        """disconnects cleanly from the current network"""
        self._apirunner("stop")
        self.quit('Bye')
