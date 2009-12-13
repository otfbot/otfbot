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

class Plugin:
    def __init__(self, root, parent):
        self.root=root
        self.parent=parent
    def register_ctl_command(self, f, namespace=None, name=None):
        """ register commands in control service """    
        if namespace is None:
            namespace=[]
        if not type(namespace) == list:
            namespace = list(namespace)
        namespace.insert(0, self.name.split(".")[-1])
        self.bot.register_ctl_command(f, namespace, name)
 
    def setLogger(self,logger):
        """ set the logger """
        self.logger = logger
    
    class Meta:
        name=__module__
        description="Basic Plugin"
        serviceDepends=[]
        #serviceDepends.append("control")
        pluginDepends=[]
        #pluginDepends.append("something")