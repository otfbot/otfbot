#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import random
import chatMod, functions


def default_settings():
	settings={};
	settings['marvinMod.filename']='marvin.txt'
	settings['marvinMod.percent']='20'
	settings['marvinMod.fileencoding']='iso-8859-15'
	return settings
		
class chatMod(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.marvin=functions.loadList(bot.getConfig("filename", "marvin.txt", "marvinMod"))

    def msg(self, user, channel, msg):
        #if channel == self.bot.nickname:
        #if msg[0]=="!" or msg[:len(self.bot.nickname)]==self.bot.nickname:
        if (msg[0]=="!" or self.bot.nickname in msg) and len(self.marvin):
            number=random.randint(0,100)
            chance=int(self.bot.getConfig("percent", "20", "marvinMod"))
            if number <chance:
                self.bot.sendmsg(channel, random.choice(self.marvin), self.bot.getConfig("fileencoding", "iso-8859-15", "marvinMod"))
