# -*- coding: UTF-8 -*-
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

def filtercolors(string):
    return string.replace(chr(3) + "1", "").replace(chr(3) + "2", "").replace(chr(3) + "3", "").replace(chr(3) + "4", "").replace(chr(3) + "5", "").replace(chr(3) + "6", "").replace(chr(3) + "7", "").replace(chr(3) + "8", "").replace(chr(3) + "9", "").replace(chr(3) + "10", "").replace(chr(3) + "11", "").replace(chr(3) + "12", "").replace(chr(3) + "13", "").replace(chr(3) + "14", "").replace(chr(3) + "15", "").replace(chr(3), "")
