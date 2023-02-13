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
# (c) 2015 by Robert Weidlich
#

from twisted.application import service, internet
from twisted.web import server, resource

import logging

from otfbot.lib.pluginSupport import pluginSupport


class Root(pluginSupport, resource.Resource):
    pluginSupportName = "webServer"
    pluginSupportPath = "otfbot/plugins/webServer"

    isLeaf = True

    def __init__(self, root, parent, *args, **kwargs):
        self.root = root
        self.parent = parent
        pluginSupport.__init__(self, root, parent)
        resource.Resource.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger("webServer")
        self.startPlugins()

    def render(self, request):
        kwargs = {
            'path': str(request.path, "utf-8"),
            'headers': request.getAllHeaders(),
            'request': request
        }
        return self._apirunner(str(request.method, "ascii"), kwargs)


class botService(service.MultiService):
    name = "webServer"

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        service.MultiService.__init__(self)

    def startService(self):
        self.config = self.root.getServiceNamed('config')
        site = server.Site(Root(self.root, self.parent))
        site.log = lambda x: None
        self.root = internet.TCPServer(8080, site, interface='::')
        self.root.name = "www"
        self.root.setServiceParent(self)
        service.MultiService.startService(self)
