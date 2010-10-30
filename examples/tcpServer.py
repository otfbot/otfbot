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
# (c) 2010 by Finn Wilke
#

"""
    This is an example of the usage of the tcpServer service
    using unix sockets.
"""

import sys
import os.path
import socket


USAGE = " <filename of unix socket> [stuff to send to tcpServer service]"

if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
    print sys.argv[0] + USAGE
    exit(1)

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(sys.argv[1])

for arg in sys.argv[2:-1]:
    s.send(arg + " ")
s.send(sys.argv[-1])
s.send("\r\n")
s.close()
