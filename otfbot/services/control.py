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
# (c) 2007 Robert Weidlich
#


import logging, logging.handlers, time, inspect

from twisted.application import internet, service
from twisted.internet import reactor

import yaml #needed for parsing dicts from set config

class botService(service.MultiService):
    """ allows to control the behaviour of the bot during runtime
    
        this class only does the work, you need another class, most suitable is a bot-module, to have a userinterface
    """
    name="control"
    commandTree={}
    commandList={}
    #functionList={}
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
        service.MultiService.__init__(self)
        self.logger=logging.getLogger("control")
        self.register_command(self.help)
        #FIXME: does not really fit here
        self.register_command(reactor.stop)

    """ Add a command to the control service
            @type f: callable
            @param f: the callable to be called, when the command is issued
    """
    def register_command(self, f, namespace=None, name=None):
        if name is None:
            name=f.__name__
        if not namespace:
            if not f.__name__ in self.commandTree:
                 self.commandTree[f.__name__] = f
            else:
                self.logger.info("Not overwriting existing Handler for "+f.__name__)
            #namespace=[]
        else:
            if not type(namespace) == list:
                namespace = [namespace,]
            cur=self.commandTree
            for n in namespace:
                if not n in cur:
                    cur[n] = {}
                cur = cur[n]
            if hasattr(cur,'__getitem__'):
                    cur[name] = f
            else:
                self.logger.error("Not replacing leaf with node at "+namespace)
        #namespace.append(name)
        #self.functionList[f]=namespace
        if not name in self.commandList:
            self.commandList[name] = f
        else:
            #tmp=self.functionList[self.commandList[name]]
            self.commandList[name]=[]
            #self.commandList[name].append(" ".join(tmp))
            #self.commandList[name].append(" ".join(namespace)) 

    def handle_command(self, string):
        s=string.split(" ")
        #print self.commandList
        if not type(s) == list:
            s=[s,]
        if s[0] in self.commandList:
            if callable(self.commandList[s[0]]):
                return self._exec(self.commandList[s[0]], s[1:])
            else:
                return "Command \""+s[0]+"\" ambigious: "+", ".join(self.commandList[s[0]])
        s.reverse()
        cur=self.commandTree
        while len(s) > 0:
            n = s.pop() 
            if not n in cur:
                return None
            if callable(cur[n]):
                s.reverse()
                return self._exec(cur[n], s)
            else:
                cur=cur[n]
                
    def _exec(self, f, args):
        try:
            return f(*args)
        except TypeError:
            args=inspect.getargspec(f)[0]
            if hasattr(f,'im_self'):
                args.reverse()
                args.pop()
                args.reverse()
            return "Usage: "+f.__name__+ " "+" ".join(args)                
        
    def help(self):
        return "Available commands: "+", ".join(self._get_cmd_for_subtree(self.commandTree))
    
    def _get_cmd_for_subtree(self, dict):
        r = []
        for k, v in dict.iteritems():
            if callable(v):
                r.append(k)
            else:
                sr = self._get_cmd_for_subtree(v)
                for ee in sr:
                    r.append(k+" "+ee)
        return r
    
    def _cmd_log_get(self, argument):
        index=1
        num=3
        if len(argument):
            args=argument.split(" ")
            if len(args)==2:
                try:
                    index=int(args[1])
                except ValueError:
                    pass
            try:
                num=min(int(args[0]), 10)
            except ValueError:
                pass
        for loghandler in logging.getLogger('').handlers:
            if loghandler.__class__ == logging.handlers.MemoryHandler:
                messages=[]
                for entry in loghandler.buffer[-(index + num): -index]:
                    messages.append(loghandler.formatter.format(entry))
                return messages

    def _cmd_config(self,argument):
        return "type \"config set\" or \"config get\" for usage information"

    def _cmd_config_reload(self, argument):
        self.parent.getServiceNamed("config").loadConfig()
        return "reloaded config from file"

    def _cmd_config_set(self, argument):
        #how this works:
        #args[x][:8] is checked for network= or channel=. channel= must come after network=
        #args[x][8:] is the network/channelname without the prefix
        #" ".join(args[x:]) joins all arguments after network= and channel= to a string from word x to the end of input
        args=argument.split(" ")
        if len(args)>=4 and len(args[0])>=8 and len(args[1])>=8 and args[0][:8]=="network=" and args[1][:8]=="channel=":
            try:
                (module, setting)=args[2].split(".", 1)
                self.parent.getServiceNamed("config").set(setting, yaml.load(" ".join(args[3:])), module, args[0][8:], args[1][8:])
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[0][8:], args[1][8:])
            except ValueError:
                return "Error: your setting is not in the module.setting form"
        elif len(args)>=3 and len(args[0])>=8 and args[0][:8]=="network=":
            try:
                (module, setting)=args[1].split(".", 1)
                self.parent.getServiceNamed("config").set(setting, yaml.load(" ".join(args[2:])), module, args[0][8:])
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[0][8:])
            except ValueError:
                return "Error: your setting is not in the module.setting form"
        elif len(argument):
            try:
                (module, setting)=args[0].split(".", 1)
                self.parent.getServiceNamed("config").set(args[0], yaml.load(" ".join(args[1:])), module)
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module)
            except ValueError:
                return "Error: your setting is not in the module.setting form"
        else:
            return "config set [network=networkname] [channel=#somechannel] setting value"

    def _cmd_config_get(self, argument):
        if len(argument)==0:
            return "config get setting [network] [channel]"
        args=argument.split(" ")
        try:
            (module, setting)=args[0].split(".", 1)
            if len(args)==1:
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module, set_default=False)
            elif len(args)==2:
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[1], set_default=False)
            elif len(args)==3:
                return self.parent.getServiceNamed("config").get(setting, "[unset]", module, args[1], args[2], set_default=False)
        except ValueError:
            return "Error: your setting is not in the module.setting form"
