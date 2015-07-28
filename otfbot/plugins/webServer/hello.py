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
# (c) 2015 by Robert Weidlich
#

from otfbot.lib.pluginSupport import plugin
from otfbot.lib.pluginSupport.decorators import callback


class Plugin(plugin.Plugin):
    def __init__(self, bot):
        self.bot = bot

    @callback
    def GET(self, path, headers, request):
        if path == '/hello.html':
            return (self.bot.NO_FURTHER_PROCESSING, "<h1>Hello World!</h1>")
