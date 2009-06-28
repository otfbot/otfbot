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
# (c) 2009 by Alexander Schier
#

import time
from lib import chatMod

class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot

    def command(self, user, channel, command, options):
        if command == "moon" or command == "mond":
            symbol=""
            name=""
            
            #http://avila.star-shine.ch/astro/berechnungen.html
            known_fullmoon_date=915245340 #seconds since 1970
            
            phase=(time.time()-known_fullmoon_date) /(60*60*24)/ 29.530588
            phase=phase-int(phase)
            
            if phase < 0.05:
                symbol="[ (  ) ]"
                name="Vollmond"
            elif phase < 0.20:
                symbol="[ C   ]" #grosser Teil
                name="abnehmender Mond"
            elif phase < 0.30:
                symbol="[ C   ]"
                name="Halbmond"
            elif phase < 0.45:
                symbol="[ (   ]" #kleiner Teil
                name="abnehmender Mond"
            elif phase < 0.65:
                symbol="[     ]"
                name="Neumond"
            elif phase < 0.80:
                symbol="[   ) ]" #kleiner Teil
                name="zunehmender Mond"
            elif phase < 0.80:
                symbol="[   D ]"
                name="Halbmond"
            else:
                symbol="[   D ]" #grosser Teil
                name="zunehmender Mond"
            self.bot.sendmsg(channel, "%s %s"%(symbol, name))
