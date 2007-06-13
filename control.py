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
class configShell:
    DESTROY_ME=234
    def __init__(self, bot):
        self.bot=bot
        self.configlevel=[]

    def _getlevellist(self):
        if len(self.configlevel) == 0:
            return self.bot.getNetworks()
        elif len(self.configlevel) == 1:
            return self.bot.getChannels(self.configlevel[0])
        else:
            return self.bot.getSubOptions(self.configlevel)
    
    def _ls(self):
        out=""
        lst=self._getlevellist()
        for i in range(1,len(lst)):
            out=out+str(i)+" "+lst[i-1]+" | "
        return out
        
    def _cd(self, string):
        if string == ".." and len(self.configlevel)>=0:
            self.configlevel.pop()
        else:
            num=int(string)
            if 0 < num and num < len(self._getlevellist())+1:
                self.configlevel.append(self._getlevellist()[num-1])
            else:
                return "No such setting: "+str(num)
    
    def _get(self,string):
        msg=string.split(" ")
        #self.logger.debug(msg)
        if len(msg) == 4:
            res=self.bot.getConfig(msg[0], "",msg[1],msg[2],msg[3])
        elif len(msg) == 3:
            res=self.bot.getConfig(msg[0], "", msg[1], msg[2])
        elif len(msg) == 2:
            res=self.bot.getConfig(msg[0], "", msg[1])
        elif len(msg) == 1:
            res=self.bot.getConfig(msg[0], "")
        if len(msg) == 0 or len(msg) > 4:
            return "Syntax: config get key [modul] [network] [channel]"
        else:
            #self.logger.debug(".".join(msg))
            #self.logger.debug(res)
            return ".".join(msg)+"="+res
    
    def _set(self, string):
        #FIXME: 
        #msg=msg[4:]
        #tmp=msg.split("=")
        #if len(tmp) != 2:
        #    self.bot.sendmsg(nick, "Syntax: config set key=value")
        #    return
        #self.bot.setConfig(tmp[0], tmp[1])
        return "function is out of order"
    
    def input(self, request):
        tmp = request.strip().split(" ",1)
        if len(tmp) == 1:
            command = tmp[0]
            argument = ""
        else:
            (command, argument) = tmp
        if command == "ls":
            return self._ls()
        elif command == "cd":
            return self._cd(argument)
        elif command == "quit":
            return self.DESTROY_ME
        elif command == "get":
            return self._get(argument)
        elif command == "set":
            return self._set(argument)
        else:
            return "Some helpful text"
            #self.bot.sendmsg(nick, "Syntax: config [get <key> [modul] [network] [channel]|set <key=value>]")


class controlInterface:
    MODUS_DEFAULT=0
    MODUS_CONFIGSHELL=1
    def __init__(self, bot):
        self.bot=bot
        self.modus=self.MODUS_DEFAULT
        self.configshell=None
    
    def input(self, request):
        tmp = request.strip().split(" ",1)
        if len(tmp) == 1:
            command=tmp[0]
            argument=""
        else:
            (command, argument) = tmp
        if command == "config":
            self.configshell=configShell(self.bot)
            return "Entering configshell ..."
        elif self.configshell:
            output = self.configshell.input(request)
            if (output == self.configshell.DESTROY_ME):
                self.configshell=None
                return "Leaving configshell ..."
            else:
                return output
        elif command == "help":
            return "Available commands: reload, stop|quit, disconnect [network], connect network [port], listnetworks, changenick newnick, join channel, part channel [message], listchannels"
        elif command == "reload":
            self.bot.reloadModules()
            return "Reloading all modules ..."
        elif command == "listmodules":
            module=[]
            for mod in self.bot.mods:
                module.append(mod.name)
            return str(module)
        elif command == "stop" or command == "quit":
            conns=self.bot.getConnections()
            for c in conns:
                conns[c].disconnect()
            return "Disconnecting from all networks und exiting ..."                
        elif command == "disconnect":
            args = argument.split(" ")
            conns=self.bot.getConnections()
            if len(args) == 2:
                if conns.has_key(args[1]):
                    conns[args[1]].disconnect()
                    return "Disconnecting from "+str(conns[args[1]].getDestination())
                else:
                    return "Not connected to "+str(args[1])
            else:
                self.bot.quit("Bye.")
                return "Disconnecting from current network. Bye."                
        elif command == "connect":
            args = argument.split(" ")
            if len(args) < 1 or len(args) > 2:
                return "Usage: connect irc.network.tld [port]"
            else:
                if len(args) == 2:
                    port=args[2]
                else:
                    port=6667
                self.bot.addConnection(args[1],port)
                return "Connecting to "+str(self.bot.getConnections()[args[1]].getDestination())
        elif command == "listnetworks":
            ne=""
            for n in self.bot.getConnections():
                ne=ne+" "+n
            return "Currently connected to:"+unicode(ne).encode("utf-8")
        elif command == "listchannels":
            ch=""
            for c in self.bot.channel:
                ch=ch+" "+c
            return "Currently in:"+unicode(ch).encode("utf-8")
        elif command == "changenick":
            if argument == "":
                return "Usage: changenick newnick"
            else:
                self.bot.setNick(argument)
        elif command == "join":
            if argument == "":
                return "Usage: join channel"
            else:
                self.bot.join(argument)
                return "Joined "+str(argument)
        elif command == "part":
            args=argument.split(" ",1)
            if len(args) == 0:
                return "Usage: part channel [message]"
            else:
                if len(args) > 1:
                    partmsg=args[1]
                else:
                    partmsg=""
                self.bot.leave(args[0],partmsg)
                return "Left "+args[0]
        elif command == "kick":
            args=msg.split(" ",2)
            if len(args) < 2:
                return "Usage: kick channel user [message]"
            else:
                if len(args) == 2:
                    self.bot.kick(args[0],args[1])
                else:
                    self.bot.kick(args[0],args[1],args[3])
                return "Kicked "+args[1]+" from "+args[0]+"."
