# -*- coding: utf-8 -*-
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
# (c) 2005 - 2010 by Alexander Schier
# (c) 2006 - 2010 by Robert Weidlich
#

""" A Twistd plugin to generate a initial configuration file for OTFBot
"""

from otfbot import services
from otfbot.lib import version
from otfbot.plugins import ircClient
try:
    from otfbot.plugins import ircServer
except ImportError:
    pass
from otfbot.services import config as configService
from otfbot.services.auth import YamlWordsRealm as auth
from otfbot.lib.user import BotUser

from twisted.application import internet, service
from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.internet import reactor
from twisted.python import usage

from zope.interface import implements

import sys
import glob
import os


class Options(usage.Options):
    optParameters = [["config", "c", "otfbot.yaml", "Location of configfile"]]


class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "gen-otfbot-config"
    description = "Generate a basic configuration for OtfBot"
    options = Options

    def makeService(self, options):
        application = service.MultiService()

        config = configService.configService(options['config'])

        # ircClient plugins
        path = os.path.abspath(ircClient.__path__[0])
        files = glob.glob(os.path.join(path, "*.py"))
        modules = []
        for file in files:
            plugin = os.path.basename(file)[:-3]
            if not plugin == "__init__":
                modules.append(plugin)
        config.set("ircClientPlugins", modules, 'main')

        if 'ircServer' in sys.modules:
            # ircServer plugins
            path = os.path.abspath(ircServer.__path__[0])
            files = glob.glob(os.path.join(path, "*.py"))
            modules = []
            for file in files:
                plugin = os.path.basename(file)[:-3]
                if not plugin == "__init__":
                    modules.append(plugin)
            config.set("ircServerPlugins", modules, 'main')

        # detect services
        path = os.path.abspath(services.__path__[0])
        files = glob.glob(os.path.join(path, "*.py"))

        modules = []
        for file in files:
            plugin = os.path.basename(file)[:-3]
            if not plugin == "__init__" and not plugin == "config":
                modules.append(plugin)
        config.set("services", modules, 'main')

        sys.stdout.write("Network Name: ")
        name = raw_input().strip()
        config.set('enabled', True, 'main', name)
        sys.stdout.write("Server hostname: ")
        config.set('server', raw_input().strip(), 'main', name)
        sys.stdout.write("First Channel: ")
        config.set('enabled', True, 'main', name, raw_input().strip())
        sys.stdout.write("Nickname: ")
        config.set('nickname', raw_input().strip(), 'main')
        config.set('encoding', 'UTF-8', 'main')

        config.set('errfile', 'error.log', 'logging')
        config.writeConfig()

        try:
            os.mkdir("data")
        except OSError:
            pass
        authS = auth("userdb", "data/userdb.yaml")
        sys.stdout.write("create admin user\nnickname: ")
        user = BotUser(raw_input().strip().lower())
        sys.stdout.write("password (will be echoed in cleartext): ")
        user.setPasswd(raw_input().strip())
        authS.addUser(user)
        authS.save()

        reactor.addSystemEventTrigger('after', 'startup', reactor.stop)

        return config

serviceMaker = MyServiceMaker()
