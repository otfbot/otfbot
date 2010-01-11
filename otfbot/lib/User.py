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
# (c) 2008 - 2010 by Alexander Schier
# (c) 2009 - 2010 by Robert Weidlich
#

from twisted.words import service

class BotUser(service.User):
    password=""
    def __init__(self, name):
        self.name=name
    def __repr__(self):
        return "<BotUser %s>" % self.name

class IrcUser(service.User):
    password=""
    def __init__(self, hostmask):
        self.name = hostmask.split("!",1)[0]
        self.user = hostmask.split("!",1)[1].split("@",1)[0]
        self.host = hostmask.split("!",1)[1].split("@",1)[1]
        self.botuser = None
        super(IrcUser,self).__init__(self.name)
    def setBotuser(self, botuser):
        self.botuser=botuser
    def getBotuser(self):
        return self.botuser
    def hasBotuser(self):
        return self.botuser!=None
    
    def getHostMask(self):
        return self.name+"!"+self.user+"@"+self.host
    
    def __repr__(self):
        return "<IrcUser %s>" % self.getHostMask()
