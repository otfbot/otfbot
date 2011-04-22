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
# (c) 2009 - 2010 by Robert Weidlich
#

""" Provides global version information
"""

MAJOR=1
MINOR=0
MICRO=0
EXTRA=""

simple_version="%d.%d.%d%s"%(MAJOR, MINOR, MICRO, EXTRA)

try:

    import sys
    import os.path

    from twisted.python import versions
    from otfbot.lib.vername import ver2name


    class GitVersion(versions.Version):

        def _getSVNVersion(self):
            mod = sys.modules.get(self.__module__)
            if mod:
                f = os.path.dirname(mod.__file__)
                for i in range(1, 3):
                    f = os.path.split(f)[0]
                git = os.path.join(f, '.git')
                if not os.path.exists(git):
                    print "no git dir"
                    return None
                master = os.path.join(git, 'refs', 'heads', 'master')
                if not os.path.exists(master):
                    print "no masterref"
                    return None
                f = open(master, 'r')
                ver = f.readline().strip()
                return ver[:7]

        def _formatSVNVersion(self):
            ver = self._getSVNVersion()
            if ver is None:
                return ''
            return ' (Git commit %s)' % (ver,)

        def short(self):
            """
            from twisted.python.versions.Version
            Return a string in canonical short version format,
            <major>.<minor>.<micro>[+rSVNVer].
            """
            s = self.base()
            svnver = self._getSVNVersion()
            if svnver:
                s += "+" + str(svnver) + " (%s)"%ver2name(svnver)
            return s

    _version = GitVersion('OTFBot', MAJOR, MINOR, MICRO, EXTRA)
except ImportError:
    pass
