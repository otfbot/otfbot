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
# (c) 2005, 2006 by Alexander Schier
# (c) 2006 by Robert Weidlich
# 

"""Chat Bot"""
svnversion="$Revision$".split(" ")[1]
from twisted.words.protocols import irc

from twisted.internet import reactor, protocol, error, ssl
import os, random, string, re, sys, traceback, atexit
import functions, config, scheduler


# some constants, can be retrieved from serveranswer while connecting.
modchars={'a':'!','o':'@','h':'%','v':'+'}
modcharvals={'!':4,'@':3,'%':2,'+':1,' ':0}

###############################################################################
# Parse commandline options
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--config",dest="configfile",metavar="FILE",help="Location of configfile",type="string")
parser.add_option("-d","--debug",dest="debug",metavar="LEVEL",help="Show debug messages of level LEVEL (10, 20, 30, 40 or 50). Implies -f.", type="int", default=0)
parser.add_option("-f","--nodetach",dest="foreground",help="Do not fork into background.",action="store_true", default=False)

parser.add_option("-u","--user",dest="userid",help="if run as root, the bot needs a userid to chuid to.",type="int", default=0)
parser.add_option("-g","--group",dest="groupid",help="if run as root, the bot needs a groupid to chgid to.",type="int", default=0)

(options,args)=parser.parse_args()
if options.debug and options.debug not in (10,20,30,40,50):
    parser.error("Unknown value for --debug")
###############################################################################
#check for root rights
if os.getuid()==0:
    if options.userid and options.userid!=0 and options.groupid and options.groupid!=0:
        from twisted.python.util import switchUID
        #os.chroot(".") #DOES NOT WORK. pwd.getpwuid fails in switchUID, when chrooted.
        switchUID(options.userid, options.groupid)
    else:
        print "Otfbot should not be run as root."
        print "please use -u and -g to specify a userid/groupid"
        sys.exit(1)
###############################################################################
# Detaching from console
if options.foreground == False and not options.debug > 0:
    try:
        import subprocess
        subprocess.Popen([sys.argv[0],"-f"])
        sys.exit(0)
    except ImportError:
        pass
###############################################################################
# Setup Logging
import logging
import logging.handlers
# Basic settings for logging
# logging to logfile
filelogger = logging.handlers.RotatingFileHandler('otfbot.log','a',20480,5)
#filelogger = logging.FileHandler('otfbot.log','a')
logging.getLogger('').setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-18s %(module)-18s %(levelname)-8s %(message)s')
filelogger.setFormatter(formatter)
logging.getLogger('').addHandler(filelogger)
#corelogger.addHandler(filelogger)

if options.debug > 0:
    # logging to stdout
    console = logging.StreamHandler()
    logging.getLogger('').setLevel(options.debug)
    formatter = logging.Formatter('%(asctime)s %(name)-10s %(module)-18s %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    #corelogger.addHandler(console)
corelogger = logging.getLogger('core')
corelogger.info("Starting OtfBot - Version svn "+str(svnversion))

def logerror(logger, module, exception):
    logger.error("Exception in Module "+module+": "+str(exception))
    tb_list = traceback.format_tb(sys.exc_info()[2])
    for entry in tb_list:
        for line in entry.strip().split("\n"):
            logger.error(line)

###############################################################################
# Function which is called, when the program terminates.
def exithook():
    # remove Pidfile
    os.remove(pidfile)
    writeConfig()
    corelogger.info("Bot shutted down")
    corelogger.info("-------------------------")

# Load modules
sys.path.insert(1,"modules")
classes=[]
for file in os.listdir("modules"):
    if len(file)>=3 and file[-3:]==".py":
        classes.append(__import__(file[:-3]))
        classes[-1].datadir = "modules/"+classes[-1].__name__+"-data"
        corelogger.debug("Loading module "+classes[-1].__name__)


# react on signals
#import signal
#def signalhandler(signal, frame):
#    corelogger.info("Got Signal "+str(signal))
#signal.signal(signal.SIGHUP,signalhandler)
#signal.signal(signal.SIGTERM,signalhandler)

###############################################################################
# some config functions
theconfig=None
def setConfig(option, value, module=None, network=None, channel=None):
    theconfig.set(option, value, module, network, channel)
    writeConfig()
        
def hasConfig(option, module=None):
    return theconfig.has(option, module)
def getConfig(option, defaultvalue="", module=None, network=None, channel=None):
    return theconfig.get(option, defaultvalue, module, network, channel)
def getBoolConfig(option, defaultvalue="", module=None, network=None, channel=None):
    if theconfig.get(option, defaultvalue, module, network, channel) in ["True","true","On","on","1"]:
        return True
    return False

def loadConfig(myconfigfile):
    if os.path.exists(myconfigfile):
        myconfig=config.config(logging, myconfigfile)
    else:
        myconfig=config.config(logging)
        for myclass in classes:
            try:
                modconfig=myclass.default_settings()
                for item in modconfig.keys():
                    myconfig.set(item, modconfig[item])
            except AttributeError:
                pass
        
        myconfig.set('enabled', 'false', 'main', 'irc.samplenetwork')
        myconfig.set('enabled', 'false', 'main', 'irc.samplenetwork', '#example')
        myconfig.set('nickname', 'OtfBot', 'main')
        myconfig.set('encoding', 'UTF-8', 'main')
        myconfig.set('pidfile','otfbot.pid','main')
        
        file=open(myconfigfile, "w")
        file.write(myconfig.exportxml())
        file.close()
        #no logger here: the user needs to read this on console, not in logfile
        print "Default Settings loaded."
        print "Edit config.xml to configure the bot."
        sys.exit(0)
    return myconfig

def writeConfig():
    file=open(configfile, "w")
    #options=config.keys()
    #options.sort()
    #for option in options:
    #    file.write(option+"="+config[option]+"\n")
    file.write(theconfig.exportxml())
    file.close()
schedulethread=scheduler.Schedule()
schedulethread.start()

def addScheduleJob(time, function):
    schedulethread.addScheduleJob(time, function)
    
class Bot(irc.IRCClient):
    """The Protocol of our IRC-Bot"""
    def __init__(self):
        #list of mods, which the bot should use
        #you may need to configure them first
        self.classes = classes
        self.users={}
        self.channels=[]
        self.network=None
    
        self.mods = []
        self.numMods = 0

        self.versionName="OtfBot"
        self.versionNum="svn "+str(svnversion)
        self.versionEnv="" #sys.version
        self.logging = logging
        self.logger = logging.getLogger("core")
        self.logger.info("Starting new Botinstance")
        self.startMods()
        self.scheduler = scheduler.Scheduler(self.getReactor())
    
    def _apirunner(self,apifunction,args={}):
        """Pass all calls to modules callbacks through this method, they are checked whether they should be execeted or not"""
        for mod in self.mods:
            if (args.has_key("channel") and args["channel"] in self.channels and self.getBoolConfig("enabled","True",mod.name,self.network,args["channel"])) or not args.has_key("channel") or args["channel"] not in self.channels:
                try:
                    getattr(mod,apifunction)(**args)
                except Exception, e:
                    logerror(self.logger, mod.name, e)
    
    # public API
    def startMods(self):
        workingdir=os.getcwd()
        for chatModule in self.classes:
            #if self.getConfig("enabled","true",chatModule.__name__,self.network)
            self.mods.append( chatModule.chatMod(self) )
            self.mods[-1].setLogger(self.logger)
            self.mods[-1].name = chatModule.__name__
            #try:
            #    self.mods[-1].start()
            #except AttributeError:
            #    pass
        self._apirunner("start")
    # configstuff, should maybe be moved to a config-instance at self.config
    def setConfig(self, option, value, module=None, network=None, channel=None):
        return setConfig(option, value, module, network, channel)
    def hasConfig(self, option, module=None):
        return hasConfig(option, module)
    def getConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
        return getConfig(option, defaultvalue, module, network, channel)
    def getBoolConfig(self, option, defaultvalue="", module=None, network=None, channel=None):
        return getBoolConfig(option, defaultvalue, module, network, channel)
    def getSubOptions(self, list):
        return theconfig.getsubopts(list)
    def getNetworks(self):
        return theconfig.getNetworks()
    def getChannels(self,net):
        return theconfig.getChannels(net)
    def loadConfig(self):
        return loadConfig(configfile)
    def writeConfig(self):
        return writeConfig()
    def getUsers(self):
        return self.users
    def getReactor(self):
        return reactor
    def getFactory(self):
        return self.factory
    def auth(self, user):
        """test if the user is privileged"""
        level=0
        for mod in self.mods:
            try:
                retval=mod.auth(user)
                if retval > level:
                    level=retval
            except AttributeError:
                pass
        return level
    
    def sendmsg(self, channel, msg, encoding="iso-8859-15", fallback="iso-8859-15"):
        """msg function, that converts from iso-8859-15 to a encoding given in the config"""
        try:
            msg=unicode(msg, encoding).encode(self.getConfig("encoding", "UTF-8", "main"))
        except UnicodeDecodeError:
            #self.logger.debug("Unicode Decode Error with String:"+str(msg))
            #Try with Fallback encoding
            msg=unicode(msg, fallback).encode(self.getConfig("encoding", "UTF-8", "main"))
        except UnicodeEncodeError:
            pass
            #self.logger.debug("Unicode Encode Error with String:"+str(msg))
            #use msg as is
            
        self.msg(channel, msg)
        self.privmsg(self.nickname, channel, msg)
        
    def sendme(self, channel, action, encoding="iso-8859-15"):
        """msg function, that converts from iso-8859-15 to a encoding given in the config"""
        action=unicode(action, encoding).encode(self.getConfig("encoding", "UTF-8", "main"))
            
        self.me(channel, action)
        self.action(self.nickname, channel, action)
    
    def reloadModules(self):
        for chatModule in self.classes:
            self.logger.info("reloading "+chatModule.__name__)
            reload(chatModule)
        for chatMod in self.mods:
            try:
                chatMod.stop()
            except Exception, e:
                logerror(self.logger, mod.name, e)
        self.mods=[]
        self.startMods()    
    
    # Callbacks
    def connectionMade(self):
        self.network=self.transport.addr[0]
        tmp=self.getChannels(self.network)
        if tmp:
            self.channels=tmp
        self.nickname=unicode(self.getConfig("nickname", "OtfBot", 'main', self.network)).encode("iso-8859-1")
        if len(self.network.split(".")) < 2:
            nw = self.network
        else:
            nw = self.network.split(".")[-2]
        self.logger = self.logging.getLogger(nw)
        self.logger.info("made connection to "+self.network)
        irc.IRCClient.connectionMade(self)
        for mod in self.mods:
            mod.setLogger(self.logger)
            mod.network=self.network
        self._apirunner("connectionMade")

    def connectionLost(self, reason):
        #self.logger.info("lost connection: "+str(reason))
        irc.IRCClient.connectionLost(self)
        self._apirunner("connectionLost",{"reason": reason})
    
    def signedOn(self):
        self.logger.info("signed on "+self.network+" as "+self.nickname)
        channelstojoin=self.channels
        self.channels=[]
        for channel in channelstojoin:
            if(getBoolConfig("enabled", "false", "main", self.network, channel)):
                self.join(unicode(channel).encode("iso-8859-1"))
        self._apirunner("signedOn")

    def joined(self, channel):
        self.logger.info("joined "+channel)
        self.channels.append(channel)
        self.users[channel]={}
        self._apirunner("joined",{"channel":channel})

    def left(self, channel):
        self.logger.info("left "+channel)
        del self.users[channel]
        self.channels.remove(channel)
        self._apirunner("left",{"channel":channel})

    def privmsg(self, user, channel, msg):
        self._apirunner("privmsg",{"user":user,"channel":channel,"msg":msg})
        self._apirunner("msg",{"user":user,"channel":channel,"msg":msg})
        #nick = user.split("!")[0]
        #if channel == self.nickname and self.auth(nick) > 9:
        #if msg == "!who":
        #    self.sendLine("WHO "+channel)
        #if msg[:6] == "!whois":
        #    self.sendLine("WHOIS "+msg[7:])
        #if msg == "!user":
        #    self.sendmsg(channel,str(self.users))

    def irc_unknown(self, prefix, command, params):
        #self.logger.debug(str(prefix)+" : "+str(command)+" : "+str(params))
        #parse /names-list which is sent when joining a channel
        if command == "RPL_NAMREPLY":
            for nick in params[3].strip().split(" "):
                if nick[0] in "@%+!":
                    s=nick[0]
                    nick=nick[1:]
                else:
                    s=" "
                self.users[params[2]][nick]={'modchar':s}
        self._apirunner("irc_unknown",{"prefix":prefix,"command":command,"params":params})

    def noticed(self, user, channel, msg):
        self._apirunner("noticed",{"user":user,"channel":channel,"msg":msg})
                
    def action(self, user, channel, message):
        self._apirunner("action",{"user":user,"channel":channel,"message":message})

    def modeChanged(self, user, channel, set, modes, args):
        self._apirunner("modeChanged",{"user":user,"channel":channel,"set":set,"modes":modes,"args":args})
        i=0
        for arg in args:
            if modes[i] in modchars.keys() and set == True:
                if modcharvals[modchars[modes[i]]] > modcharvals[self.users[channel][arg]['modchar']]:
                    self.users[channel][arg]['modchar'] = modchars[modes[i]]
            elif modes[i] in modchars.keys() and set == False:
                #FIXME: ask for the real mode
                self.users[channel][arg]['modchar'] = ' '
            i=i+1

    def userKicked(self, kickee, channel, kicker, message):
        self._apirunner("userKicked",{"kickee":kickee,"channel":channel,"kicker":kicker,"message":message})

    def userJoined(self, user, channel):
        self._apirunner("userJoined",{"user":user,"channel":channel})
        self.users[channel][user.split("!")[0]]={'modchar':' '}

    def userLeft(self, user, channel):
        self._apirunner("userLeft",{"user":user,"channel":channel})
        del self.users[channel][user.split("!")[0]]

    def userQuit(self, user, quitMessage):
        self._apirunner("userQuit",{"user":user,"quitMessage":quitMessage})
        for chan in self.users:
            if self.users[chan].has_key(user):
                del self.users[chan][user]

    def yourHost(self, info):
        pass
    
    #def ctcpQuery(self, user, channel, messages):
    #    (query,t) = messages[0]
    #    answer = None
    #    #if query == "VERSION":
    #    #    answer = "chatBot - a python IRC-Bot"
    #    if answer: 
    #        self.ctcpMakeReply(user.split("!")[0], [(query,answer)])
    #        self.logger.info("Answered to CTCP "+query+" Request from "+user.split("!")[0])
        
    def userRenamed(self, oldname, newname):
        for chan in self.users:
            if self.users[chan].has_key(oldname):
                self.users[chan][newname]=self.users[chan][oldname]
                del self.users[chan][oldname]
        self._apirunner("userRenamed",{"oldname":oldname,"newname":newname})

    def topicUpdated(self, user, channel, newTopic):
        self._apirunner("topicUpdated",{"user":user,"channel":channel,"newTopic":newTopic})

    def lineReceived(self, line):
        #self.logger.debug(str(line))
        # adding a correct hostmask for join, part and quit
        if line.split(" ")[1] == "JOIN" and line[1:].split(" ")[0].split("!")[0] != self.nickname:
            self.userJoined(line[1:].split(" ")[0],string.lower(line.split(" ")[2][1:]))
            #self.joined(line[1:].split(" ")[0],line.split(" ")[2][1:])
        elif line.split(" ")[1] == "PART" and line[1:].split(" ")[0].split("!")[0] != self.nickname:
            self.userLeft(line[1:].split(" ")[0],line.split(" ")[2])
        elif line.split(" ")[1] == "QUIT":
            self.userQuit(line[1:].split(" ")[0],line.split("QUIT :")[1])
        else:
            irc.IRCClient.lineReceived(self,line)

class BotFactory(protocol.ReconnectingClientFactory):
    """The Factory for the Bot"""
    protocol = Bot
    instances = {}

    def _addnetwork(self,addr,nw):
        self.instances[addr] = nw

    def _removenetwork(self,addr):
        if self.instances.has_key(addr):
            del self.instances[addr]
    
    def _getnetwork(self,addr):
        return self.instances[addr]

    def _getnetworkslist(self):
        return self.instances.keys()

    def _checkforshutdown(self):
        if len(self.instances)==0:
            corelogger.info("Not Connected to any network. Shutting down.")
            schedulethread.stop()
            #TODO: add sth to stop modules
            reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        clean = error.ConnectionDone()
        if reason.getErrorMessage() == str(clean):
            self._removenetwork(connector.host)
            self._checkforshutdown()
            corelogger.info("Cleanly disconnected from "+connector.host)
        else:
            corelogger.error("Disconnected from "+connector.host+": "+str(reason.getErrorMessage())+".")
        #    connector.connect()
        
    def clientConnectionFailed(self, connector, reason):
        corelogger.error("Connection to "+connector.host+" failed: "+str(reason.getErrorMessage()))
        self._removenetwork(connector.host)
        self._checkforshutdown()
    
    def buildProtocol(self,addr):
        proto=protocol.ReconnectingClientFactory.buildProtocol(self,addr)
        self._addnetwork(addr.host, proto)
        return proto

try:
    configfile=parser.configfile
except AttributeError:
    configfile="config.xml"
theconfig=loadConfig(configfile)

# writing PID-File
pidfile=theconfig.get('pidfile','otfbot.pid','main')
f=open(pidfile,'w')
f.write(str(os.getpid())+"\n")
f.close()

# registering the exithook function
atexit.register(exithook)

networks=theconfig.getNetworks()
connections={}
if networks:
    f = BotFactory()
    for network in networks:
        if(getBoolConfig('enabled', 'unset', 'main', network)):
            #channels=theconfig.getChannels(network)
            #if not channels:
            #    channels=[]
            #for channel in channels:
            #    if(not getBoolConfig('enabled','unset','main', network)):
            #        channels.remove(channel)
            if (getBoolConfig('ssl','False','main',network)):
                s = ssl.ClientContextFactory()
                connections[network]=reactor.connectSSL(unicode(network).encode("iso-8859-1"), int(getConfig('port','6697','main',network)), f,s);
            else:
                connections[network]=reactor.connectTCP(unicode(network).encode("iso-8859-1"), int(getConfig('port','6667','main',network)), f)
    reactor.run()
