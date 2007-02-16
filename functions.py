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
# (c) 2005, 2006 by Alexander Schier
# (c) 2006 by Robert Weidlich
#

def loadProperties(propertiesFile):
	properties={}
	if propertiesFile=="":
		return {}
	try:
		propFile = open(propertiesFile, "r")
		content = propFile.read()
		propFile.close()
		for line in content.split("\n"):
			if len(line) >1 and line[0] != "#":
				pair = line.split("=", 1)
				if len(pair)==2:
					properties[pair[0]] = pair[1]
	except IOError:
		print "loadProperties: Creating", propertiesFile
		propFile = open(propertiesFile, "w")
		propFile.close()
	return properties
	
def loadList(listFile):
	if listFile=="":
		return []
	list=[]
	try:
		file = open(listFile, "r")
		content = file.read()
		file.close()
		for word in content.split("\n"):
			if word != "" and word[0] != '#':
				list.append(word)
	except IOError:
		print "loadList: Creating", listFile
		file = open(listFile, "w")
		file.close()
	return list

