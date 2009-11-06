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
# (c) 2008 by Robert Weidlich
# (c) 2008 by Alexander Schier
# 

from twisted.application import internet, service
from twisted.internet import protocol, reactor, error, ssl
from twisted.words.protocols import irc

import logging
import string, time

from lib.pluginSupport import pluginSupport
from lib.User import IrcUser


class botService(service.MultiService):
    name="ircClient"
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        service.MultiService.__init__(self)
    
    def startService(self):
        self.controlservice=self.root.getServiceNamed('control')
        self.logger=logging.getLogger(self.name)
        self.config=self.root.getServiceNamed('config')
        if not self.controlservice:
            logger.warning("cannot register control-commands as no control-service is available")
        else:
            self.register_ctl_command(self.connect)
            self.register_ctl_command(self.disconnect)
            self.register_ctl_command(lambda : self.namedServices.keys(), name="list")
        for network in self.config.getNetworks():
            if self.config.getBool('enabled', 'True', 'main', network):
                self.connect(network)
        service.MultiService.startService(self)

    def connect(self, network):
        f = BotFactory(self.root, self, network)
        servername=self.config.get("server", "localhost", "main", network)
        port = int(self.config.get('port','6667','main', network))
        if (self.config.getBool('ssl','False','main', network)):
            s = ssl.ClientContextFactory()
            serv=internet.SSLClient(host=servername, port=port, factory=f,contextFactory=s)
            serv.__repr__=lambda: "<IRC Connection with SSL to %s:%s>"%(servername, port)
        else:
            serv=internet.TCPClient(host=servername, port=port, factory=f)
            serv.__repr__=lambda: "<IRC Connection to %s:%s>"%(servername, port)
        f.service=serv
        serv.setName(network)
        serv.parent=self
        self.addService(serv)
    
    def disconnect(self, network):
    	if network in self.namedServices:
    		self.removeService(self.namedServices[network])
    		return "Disconnected from "+network
    	else:
            return "Not connected to "+network
    
    def register_ctl_command(self, f, namespace=None, name=None):
        if self.controlservice:
            if namespace is None:
                namespace=[]
            if not type(namespace) == list:
                namespace = [namespace,]
            namespace.insert(0, self.name)
            self.controlservice.register_command(f, namespace, name)

class BotFactory(protocol.ClientFactory):
    """The Factory for the Bot"""

    def __init__(self, root, parent, network):
        self.root=root
        self.parent=parent
        self.protocol=Bot
        self.network=network
        self.config=root.getServiceNamed('config')
        self.logger=logging.getLogger(network)

    def __repr__(self):
        return "<BotFactory for network %s>"%self.network

    def clientConnectionLost(self, connector, reason):
        self.protocol=None
        self.service.protocol=None
        if not reason.check(error.ConnectionDone):
            self.logger.warn("Got disconnected from "+connector.host+": "+str(reason.getErrorMessage()))
            #protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        else:
            self.parent.removeService(self.service)
        
    def clientConnectionFailed(self, connector, reason):
        self.logger.warn("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
        #protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    
    def buildProtocol(self,addr):
        proto=self.protocol(self.root, self)
        self.protocol=proto
        self.service.protocol=proto
        return proto
    
#    def stopFactory(self):
#        #import inspect
#        #for o in inspect.stack():
#        #    self.logger.debug(str(o))
#        self.logger.info("Got Signal to stop factory, stopping service as well")
#        self.service.disownServiceParent()
#        self.service.stopService()
    
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
    pluginSupportPath = "plugins/ircClient" #path were the plugins are
    pluginSupportName = "ircClient" #prefix for config
    sourceURL = "http://otfbot.berlios.de/"

    modchars = {16: 'a', 8: 'o', 4: 'h', 2: 'v', 0: ' '}
    modcharvals = {16: '!', 8: '@', 4: '%', 2: '+', 0: ' '}
    def warn_and_execute(self, method, *args, **kwargs):
        self.logger.debug("deprecated call to %s with args %s"%(str(method), str(args)))
        #XXX: use bot.config.method instead
        return method(*args, **kwargs)

    def __init__(self, root, parent):
        pluginSupport.__init__(self, root, parent)
        self.config=root.getServiceNamed('config')
        self.network=self.parent.network
        self.ircClient=self.parent.parent
        self.logger = logging.getLogger(self.network)
        if self.config.getBool('answerToCTCPVersion', True, 'main', self.network):
            self.versionName="OTFBot"
            self.versionNum=root.version
            self.versionEnv=''

        self.channels=[]
        self.realname=self.config.get("realname", "A Bot", "main", self.network)
        self.password=self.config.get('password', None, 'main', self.network)
        self.nickname=unicode(self.config.get("nickname", "OtfBot", 'main', self.network)).encode("iso-8859-1")
        tmp=self.config.getChannels(self.network)
        if tmp:
            self.channels=tmp
        
        self.lineRate = 1.0/float(self.config.get("linesPerSecond","2","main",self.network))

        # all users known to the bot, nick => IrcUser
        self.userlist    = {}
        # usertracking, channel=>{User => level}
        self.users       = {}

        self.serversupports  = {}
        
        self.logger.info("Starting new Botinstance")

        self.startPlugins()
        self.register_my_commands()
        self.register_pluginsupport_commands()
    
    def register_ctl_command(self, f, namespace=None, name=None):
        if namespace is None:
            namespace=[]
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
        self.register_ctl_command(lambda : self.channels, name="listchannels" )
        self.register_ctl_command(self.kick)
        self.register_ctl_command(self.sendmsg, name="say")
        self.register_ctl_command(self.ping)
    
    def startPlugin(self, pluginName):
        plugin=pluginSupport.startPlugin(self, pluginName)
        #TODO: this is only a workaround until the plugins register their callbacks
        if plugin:
            for callback in dir(plugin):
                self.registerCallback(plugin, callback)

    def getChannelUserDict(self):
        """ Get a dict with userslists
            @rtype: dict
            @return: a dict with the channelnames as keys
        """
        return self.users
    def getUsers(self, channel):
        """ Get a list of users in channel
            @rtype: dict
            @return: a list of users
        """
        return self.getChannelUserDict()[channel]
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
        level=0
        for plugin in self.plugins.values():
            try:
                retval=plugin.auth(user)
                if retval > level:
                    level=retval
            except AttributeError:
                pass
        return level

    def depends(self, dependency):
        """raise an Exception, if the dependency is not active"""
        if not self.plugins.has_key(dependency):
            raise self.DependencyMissing(dependency)
    
    def encode_line(self, line, encoding, fallback):
        try:
            line=unicode(line, encoding).encode(self.config.get("encoding", "UTF-8", "main"))
        except UnicodeDecodeError:
            #self.logger.debug("Unicode Decode Error with String:"+str(msg))
            #Try with Fallback encoding
            line=unicode(line, fallback).encode(self.config.get("encoding", "UTF-8", "main"))
        except UnicodeEncodeError:
            pass
            #self.logger.debug("Unicode Encode Error with String:"+str(msg))
            #use msg as is
        return line

    def sendmsg(self, channel, msg, encoding="UTF-8", fallback="iso-8859-15"):
        """
            call B{only} this to send messages to channels or users
            it converts the message from iso-8859-15 to a encoding given in the config
            @type    channel:    string
            @param    channel:    send the message to this channel or user
            @type    msg:        string
            @param    msg:        the message to send
            @type    encoding:    string
            @param    encoding:    the encoding of C{msg}
            @type    fallback:    string
            @param    fallback:    try this one as encoding for C{msg}, if C{encoding} doesn't work
        """
        if not type(msg)==list:
            msg=[msg]
        for line in msg:
            line=self.encode_line(line, encoding, fallback)
            
            #from the RFC:
            #IRC messages are always lines of characters terminated with a CR-LF
            #(Carriage Return - Line Feed) pair, and these messages shall not
            #exceed 512 characters in length, counting all characters including
            #the trailing CR-LF. Thus, there are 510 characters maximum allowed
            #for the command and its parameters.
            #There is no provision for continuation message lines.
            while len(line):
                #TODO: Better splitting algorithm
                self.msg(channel, line[:450])
                self.privmsg(self.nickname, channel, line[:450])
                time.sleep(0.5) #TODO is this still needed with self.lineRate setting?
                line=line[450:]
        
    def sendme(self, channel, action, encoding="UTF-8", fallback="iso-8859-15"):
        """
            call B{only} this to send actions (/me) to channels
            it converts the message from iso-8859-15 to a encoding given in the config
            @type    channel:    string
            @param    channel:    send the message to this channel or user
            @type    action:        string
            @param    action:        the message to send
            @type    encoding:    string
            @param    encoding:    the encoding of C{msg}
            @param    fallback:    the encoding of C{msg}
        """
        if not type(action)==list:
            action=[action]
        for line in action:
            line=self.encode_line(line, encoding, fallback)
            
            self.me(channel, line)
            self.action(self.nickname, channel, line)
            time.sleep(0.5)
    
    # Callbacks
    def connectionMade(self):
        """ 
            this is called by twisted
            , when the connection to the irc-server was made
        """
        self.logger.info("made connection to "+self.transport.addr[0])
        irc.IRCClient.connectionMade(self)
        self._apirunner("connectionMade")

    def connectionLost(self, reason):
        """ this is called by twisted,
            if the connection to the IRC-Server was lost
            @type reason:    twisted.python.failure.Failure
        """
        #self.logger.info("lost connection: "+str(reason))
        irc.IRCClient.connectionLost(self)
        self._apirunner("connectionLost",{"reason": reason})
    
    def signedOn(self):
        """ called by twisted,
            when we signed on the IRC-Server
        """
        self.logger.info("signed on "+self.network+" as "+self.nickname)
        channelstojoin=self.channels
        self.channels=[]
        for channel in channelstojoin:
            if(self.config.getBool("enabled", "false", "main", self.network, channel)):
                pw = self.config.get("password","", "main", self.network, channel)
                if (pw != ""):
                    self.join(unicode(channel).encode("iso-8859-1"),unicode(pw).encode("iso-8859-1"))
                else:
                    self.join(unicode(channel).encode("iso-8859-1"))
        self._apirunner("signedOn")

    def joined(self, channel):
        """ called by twisted,
            if we joined a channel
            @param channel: the channel we joined
            @type channel: string
        """
        channel=channel.lower()
        self.logger.info("joined "+channel)
        self.channels.append(channel)
        self.users[channel]={}
        #self.sendLine("WHO")
        self._apirunner("joined",{"channel":channel})
        self.config.set("enabled", True, "main", self.network, channel)

    def left(self, channel):
        """ called by twisted,
            if we left a channel
            @param channel: the channel we left
            @type channel: string
        """
        channel=channel.lower()
        self.logger.info("left "+channel)
        self._apirunner("left",{"channel":channel})
        del self.users[channel]
        self.channels.remove(channel)
        self.config.set("enabled", "False", "main", self.network, channel) #disable the channel for the next start of the bot

    def isupport(self, options):
        for o in options:
            kv = o.split('=',1)
            if len(kv) == 1:
                kv.append(True)
            self.serversupports[kv[0]] = kv[1]
        if 'PREFIX' in self.serversupports:
            mode, sym = self.serversupports['PREFIX'][1:].split(")")
            for i in range(0,len(mode)):
                self.modchars[1**i] = mode[i]
                self.modcharvals[i**i] = sym[i]
            self.rev_modchars    = dict([(v, k) for (k, v) in self.modchars.iteritems()])
            self.rev_modcharvals = dict([(v, k) for (k, v) in self.modcharvals.iteritems()])

    #def myInfo(self, servername, version, umodes, cmodes):
        #self.logger.debug("myinfo: servername="+str(servername)+" version="+str(version)+" umodes="+str(umodes)+" cmodes="+str(cmodes))
    def command(self, user, channel, command, options):
        """callback for !commands
        @param user: the user, which issues the command
        @type user: string
        @param channel: the channel to which the message was sent or my nickname if it was a private message
        @type channel: string
        @param command: the !command without the !
        @type command: string
        @param options: eventual options specified after !command (e.g. "!command foo")
        @type options: string"""
        channel=channel.lower()
        self._apirunner("command",{"user":user,"channel":channel,"command":command, "options":options})

    def privmsg(self, user, channel, msg):
        """ called by twisted,
            if we received a message
            @param user: the user, which send the message
            @type user: string
            @param channel: the channel to which the message was sent or my nickname if it was a private message
            @type channel: string
            @param msg: the message
            @type msg: string
        """
        channel=channel.lower()
        try:
            char=msg[0].decode('UTF-8').encode('UTF-8')
        except UnicodeDecodeError:
            char=msg[0].decode('iso-8859-15').encode('UTF-8')
        if char==self.config.get("commandChar", "!", "main").encode("UTF-8"):
            tmp=msg[1:].split(" ", 1)
            command=tmp[0]
            if len(tmp)==2:
                options=tmp[1]
            else:
                options=""
            self._apirunner("command",{"user":user,"channel":channel,"command":command,"options":options})
            #return

        # to be removed
        self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})

        #if channel.lower() == self.nickname.lower():
        if not channel.lower()[0] in "#+&!":
            self._apirunner("query",{"user":user,"channel":channel,"msg":msg})
            return
        
        # to be called for messages in channels
        self._apirunner("msg",{"user":user,"channel":channel,"msg":msg})

    def irc_unknown(self, prefix, command, params):
        """ called by twisted
            for every line that has no own callback
        """
        #print command, params
        self._apirunner("irc_unknown",{"prefix":prefix,"command":command,"params":params})

    def noticed(self, user, channel, msg):
        """ called by twisted,
            if we got a notice
            @param user: the user which send the notice
            @type user: string
            @param channel: the channel to which the notice was sent (could be our nick, if the message was only sent to us)
            @type channel: string
            @param msg: the message
            @type msg: string
        """
        channel=channel.lower()
        self._apirunner("noticed",{"user":user,"channel":channel,"msg":msg})
                
    def action(self, user, channel, message):
        """ called by twisted,
            if we received a action
            @param user: the user which send the action
            @type user: string
            @param channel: the channel to which the action was sent (could be our nick, if the message was only sent to us)
            @type channel: string
            @param msg: the message
            @type msg: string
        """        
        channel=channel.lower()
        self._apirunner("action",{"user":user,"channel":channel,"msg":message})

    def modeChanged(self, user, channel, set, modes, args):
        """ called by twisted
            if a usermode was changed
        """
        channel=channel.lower()
        # track usermodes
        for i in range(0, len(args)):
            m=False
            if modes[0] in ("+","-"):
                m=modes[0]
                modes=modes[1:]
            if modes[0] in self.rev_modchars:
                if (m and m == "+") or set:
                    self.users[channel][self.userlist[args[i]]] += self.rev_modchars[modes[0]]
                elif (m and m == "-") or not set:
                    self.users[channel][self.userlist[args[i]]] -= self.rev_modchars[modes[0]]
                else:
                    self.logger.error("Internal error during modeChange: "+set+" "+modes+" "+str(args))
            else:
                self.logger.info("Change of channel mode "+modes[0]+" not tracked")
            modes=modes[1:]
        self._apirunner("modeChanged",{"user":user,"channel":channel,"set":set,"modes":modes,"args":args})

    def kickedFrom(self, channel, kicker, message):
        """ called by twisted,
            if the bot was kicked
        """
        channel=channel.lower()
        self.logger.info("I was kicked from "+channel+" by "+kicker)
        self._apirunner("kickedFrom",{"channel":channel,"kicker":kicker,"message":message})
        self.channels.remove(channel)
        self.config.set("enabled", False, "main", self.network, channel) #disable the channel for the next start of the bot
        del(self.users[channel])

    def userKicked(self, kickee, channel, kicker, message):
        """ called by twisted,
            if a user was kicked
        """
        channel=channel.lower()
        self._apirunner("userKicked",{"kickee":kickee,"channel":channel,"kicker":kicker,"message":message})
        del self.users[channel][self.userlist[kickee]]

    def userJoined(self, user, channel):
        """ called by twisted,
            if a C{user} joined the C{channel}
        """
        channel=channel.lower()
        nick = user.split("!")[0]
        if self.userlist.has_key(nick):
            u = self.userlist[nick]
        else:
            u = IrcUser(user)
            self.userlist[nick] = u
        self.users[channel][u] = 0
        self._apirunner("userJoined",{"user":user,"channel":channel})

    def userLeft(self, user, channel):
        """ called by twisted,
            if a C{user} left the C{channel}
        """
        channel=channel.lower()
        nick = user.split("!")[0]        
        self._apirunner("userLeft",{"user":user,"channel":channel})
        del self.users[channel][self.userlist[nick]]

    def userQuit(self, user, quitMessage):
        """ called by twisted,
            of a C{user} quits
        """
        self._apirunner("userQuit",{"user":user,"quitMessage":quitMessage})
        nick = user.split("!")[0]
        for c in self.users:
            if self.users[c].has_key(self.userlist[nick]):
                del self.users[c][self.userlist[nick]]
        del self.userlist[nick]

    def yourHost(self, info):
        """ called by twisted
            with information about the IRC-Server we are connected to
        """
        #self.logger.debug(str(info))
        self._apirunner("yourHost",{"info":info})
    
    def ctcpUnknownQuery(self, user, channel, messages):
        """ called by twisted,
            if a C{user} sent a ctcp query
        """
        channel=channel.lower()
        self._apirunner("ctcpQuery",{"user":user,"channel":channel,"messages":messages})
        
    def userRenamed(self, oldname, newname):
        """ called by twisted,
            if a user changed his nick
        """
        self._apirunner("userRenamed",{"oldname":oldname,"newname":newname})
        for chan in self.users:
            if self.users[chan].has_key(oldname):
                self.users[chan][newname]=self.users[chan][oldname]
                del self.users[chan][oldname]
        if self.userlist.has_key(oldname):
             self.userlist[newname] = self.userlist[oldname]
             del self.userlist[oldname]

    def topicUpdated(self, user, channel, newTopic):
        """ called by twisted
            if the topic was updated
        """
        channel=channel.lower()
        self._apirunner("topicUpdated",{"user":user,"channel":channel,"newTopic":newTopic})

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        self._apirunner("irc_RPL_ENDOFNAMES",{"prefix":prefix,"params":params})

    def irc_RPL_NAMREPLY(self, prefix, params):
        self._apirunner("irc_RPL_NAMREPLY",{"prefix":prefix,"params":params})
        nicks = params[3].strip().split(" ")
        for nick in nicks:
            if nick[0] in "@%+!":
                s=nick[0]
                nick=nick[1:]
            else:
                s=" "
            if self.userlist.has_key(nick):
                u = self.userlist[nick]
            else:
                u = IrcUser(nick+"!user@host")
                self.userlist[nick] = u
            if hasattr(self, "rev_modcharvals"): #for irc servers which do not provide this (miniircd)
                self.users[params[2]][u] = self.rev_modcharvals[s]
        while len(nicks):
            #send USERHOST request for 5 nicks at the same time
            #(maximum allowed by RFC)
            self.sendLine("USERHOST "+" ".join(nicks[:5]))
            nicks=nicks[5:]
            
    def irc_RPL_USERHOST(self, prefix, params):
        for rpl in params[1].strip().split(" "):
            tmp=rpl.split('=',1)
            if len(tmp)==2:
                (nick, hostmask)=tmp
            else:
                self.logger.warning("Error parsing RPL_USERHOST: %s, %s"%(prefix, params))
                continue
            nick = nick.replace("*","")
            hm=hostmask.split('@',1)
            if self.userlist.has_key(nick):
                self.userlist[nick].user=hm[0][1:]
                self.userlist[nick].host=hm[1]
            else:
                self.logger.warning("received RPL_USERHOST for \"%s\", who is not in list"%nick)
    
    def irc_INVITE(self, prefix, params):
        """ called by twisted,
            if the bot was invited
        """
        channel=params[1].lower()
        self._apirunner("invitedTo",{"channel":channel,"inviter":prefix})

    def irc_RPL_BOUNCE(self, prefix, params):
        """ Overridden to get isupport work correctly """
        self.isupport(params[1:-1])

    def irc_JOIN(self, prefix, params):
        """ Overridden to get the full hostmask """
        nick = string.split(prefix,'!')[0]
        channel = params[-1]
        if nick == self.nickname:
            self.joined(channel)
        else:
            self.userJoined(prefix, channel)

    def irc_PART(self, prefix, params):
        """ Overridden to get the full hostmask """
        nick = string.split(prefix,'!')[0]
        channel = params[0]
        if nick == self.nickname:
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
        self._apirunner("lineReceived", {"line":line})
        irc.IRCClient.lineReceived(self,line)
    
    def sendLine(self, line):
        self._apirunner("sendLine",{"line":line})
        irc.IRCClient.sendLine(self, line)

    def ping(self):
        self.sendLine("PING %f"%time.time())
    
    def disconnect(self):
        """disconnects cleanly from the current network"""
        self._apirunner("stop")
        self.quit('Bye')
