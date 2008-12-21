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
# (c) 2008 by Thomas Wiegart
#
HAS_PYXMLTV=True
try:
	import xmltv
except ImportError:
	HAS_PYXMLTV=False

import chatMod
import time

class Plugin(chatMod.chatMod):
	def __init__(self,bot):
		self.bot = bot
		if not HAS_PYXMLTV:
			self.bot.depends("xmltv python module")
		xmltvfile = datadir + "/" + self.bot.getConfig("xmltvfile","","tvMod")
		self.tv = tv(xmltvfile)
		standardsender = self.bot.getConfig("standardsender","ard,zdf,rtl,sat.1,n24,pro7,vox","tvMod")
		self.standardsender = []
		for i in standardsender.split(","):
			self.standardsender.append(i.lower().replace(" ",""))
	
	def command(self, user, channel, command, options):
		user = user.split("!")[0]
		if command == "tv":
			if options == "":
				programm = self.tv.get_programm_now()
			o1 = options.split(" ")[0].replace(".","").replace(":","")
			if len(o1) == 4:
				programm = self.tv.get_programm_at_time(o1 + "00")
			programm = self.parse_programm(programm)
			for i in programm:
				if i['station'][0].lower().replace(" ","") in self.standardsender:
					self.bot.sendmsg(user,unicode(str(chr(2)) + i['station'][0] + str(chr(2)) + " (" + str(i['start'][8:10]) + ":" + str(i['start'][10:12]) + "): " + i['title'] + " (" + i['language'] + ")").encode("utf8"))
		else:
			pass
	
	def parse_programm(self,programm):
		output = []
		for i in programm:
			start = i['start']
			stop = i['stop']
			titel = i['title'][0][0]
			language = i['title'][0][1]
			station = self.tv.get_station_name(i['channel'])
			output.append({'start':start,'stop':stop,'title':titel,'language':language,'station':station})
		return output
	
class tv():
	def __init__(self,xmltvfile):
		self.stations = xmltv.read_channels(xmltvfile)
		self.programm = xmltv.read_programmes(xmltvfile)
		self.stations = self.get_stations(self.stations)
	
	def get_stations(self,xmlstations):
		stations = {}
		for i in xmlstations:
			stations[i['id']] = i['display-name'][0]
		return stations
	
	def get_station(self,name):
		for i in self.stations:
			if self.stations[i][0].lower().replace(" ","") == name.lower().replace(" ",""):
				return i
		return 0
	
	def get_station_name(self,stationid):
		return self.stations[stationid]
	
	def get_programm_at_time(self,zeit,datum="today"):
		if datum == "today":
			ltime = time.localtime()
			datum = str(ltime[0]) + str(ltime[1]) + str(ltime[2])
			del ltime
		sendungen = []
		for i in self.programm:
			if int(i['start'].split(" ")[0]) <= int(datum + zeit) and int(datum + zeit) < int(i['stop'].split(" ")[0]):
				#Sendung ist im Zeitraum
				sendungen.append(i)
		return sendungen
	
	def get_programm_at_time_and_station(self,station,zeit,datum="today"):
		sendungen_all = self.get_programm_at_time(zeit,datum)
		sendungen = []
		station_id = self.get_station(station)
		for i in sendungen_all:
			if i['channel'] == station_id:
				sendungen.append(i)
		return sendungen
	
	def get_programm_now(self):
		ltime = time.localtime()
		zeit = str(ltime[3]) + str(ltime[4]) + "00"
		programm = self.get_programm_at_time(zeit)
		return programm
