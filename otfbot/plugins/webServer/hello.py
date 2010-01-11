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
# (c) 2005 - 2010 by Alexander Schier
#

from otfbot.lib import chatMod
class Plugin(chatMod.chatMod):
    def __init__(self, wps):
        self.wps=wps
        wps.registerCallback(self, 'GET')
    def GET(self, path, headers, rfile, wfile, handler):
        if path=='/hello.html':
            wfile.write("<h1>Hello World!</h1>")
