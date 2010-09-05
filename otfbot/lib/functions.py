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
# (c) 2006 - 2010 by Robert Weidlich
#

""" Contains some helper functions """

import os


def loadProperties(propertiesFile, ambiguous=False, enc="ISO-8859-15"):
    """ Loads data from a file into a dict

        The data in the file should have the format
        key=valu. If the file doesn't exist, it
        will be created. If no filename is given
        an empty dict is returned.

        @param propertiesFile: The file to deal with
        @type propertiesFile: string
        @rtype: dict
    """
    properties = {}
    if propertiesFile == "":
        return {}
    if os.path.exists(propertiesFile):
        propFile = open(propertiesFile, "r")
        content = unicode(propFile.read(), enc, errors='replace')
        propFile.close()
        for line in content.split("\n"):
            if len(line) > 1 and line[0] != "#":
                pair = line.split("=", 1)
                if len(pair) == 2:
                    #skip === bla === i.e. from dokuwiki headline
                    if pair[1][0] == "=":
                        continue
                    if ambiguous:
                        if not pair[0] in properties:
                            properties[pair[0]] = []
                        properties[pair[0]].append(pair[1])
                    else:
                        properties[pair[0]] = pair[1]
    else:
        #print "loadProperties: Creating", propertiesFile
        if (not os.path.isdir(os.path.dirname(propertiesFile))):
            os.makedirs(os.path.dirname(propertiesFile))
        propFile = open(propertiesFile, "w")
        propFile.close()
    return properties


def loadList(listFile):
    """ loads data from a file into a list

        This function loads simply each line of the file into a list.
        If the filename is empty, a empty list is returned. If the file given
        doesn't exist, it will be created.
        @param listFile: the file to deal with
        @type listFile: string
        @rtype: list
    """
    if listFile == "":
        return []
    list = []
    if os.path.exists(listFile):
        file = open(listFile, "r")
        content = file.read()
        file.close()
        for word in content.split("\n"):
            if word != "" and word[0] != '#':
                list.append(word)
    else:
        if (not os.path.isdir(os.path.dirname(listFile))):
            os.makedirs(os.path.dirname(listFile))
        file = open(listFile, "w")
        file.close()
    return list
