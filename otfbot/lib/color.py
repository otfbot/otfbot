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

colormap = {
    "white": 0,
    "black": 1,
    "navy": 2,
    "green": 3,
    "red": 4,
    "brown": 5,
    "purple": 6,
    "orange": 7,
    "yellow": 8,
    "light_green": 9,
    "teal": 10,
    "cyan": 11,
    "blue": 12,
    "pink": 13,
    "grey": 14,
    "light_grey": 15}


def filtercolors(input):
    """
        Filters all irc colors out of a given string
    """
    for i in xrange(1, 16):
        input = input.replace(chr(3) + str(i), "")
    return input


def changecolor(fgcolor, bgcolor=None):
    """
        Returns a string that with the current irc color set to something
        different.
        Expects both arguments to be one of the strings defined in colormap:
        "white, black, navy, green, red, brown, purple, orange, yellow,
        light_green, teal, cyan, blue, pink, grey, light_grey"
        The background color is optional
    """
    if fgcolor not in colormap:
        raise ValueError("Unknown foreground color: \"" +
            str(fgcolor) + "\"")
    if bgcolor is not None and bgcolor not in colormap:
        raise ValueError("Unknown background color: \"" +
            str(bgcolor) + "\"")
    colorstring = chr(3) + str(colormap[fgcolor])
    if bgcolor is not None:
        colorstring += "," + str(colormap[bgcolor])
    return colorstring


def resetcolors():
    """
        Returns a string that will reset all currently active irc colors.
    """
    return chr(3)
