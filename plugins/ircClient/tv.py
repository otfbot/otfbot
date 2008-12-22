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
import time,sys

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
		public = 0
		filterstandard = 0
		programm = []
		ltime = time.localtime()
		if command == "tv":
			o = options.split(" ")
			o1 = o[0].replace(".","").replace(":","")
			if o[len(options.split(" ")) -1] == "public":
				public = 1
				o.remove("public")
			if options == "":
				o = []
			if len(o) != 0 and o[0].lower() == "help":
				self.bot.sendmsg(user," !tv <- Zeigt das aktuelle TV-Programm an.")
				self.bot.sendmsg(user," !tv <uhrzeit> <- Zeigt das Programm fuer <uhrzeit> (hh:mm) an.")
				self.bot.sendmsg(user," !tv <uhrzeit> <sendername> <- zeigt das Programm fuer <uhrzeit> auf <sendername> an.")
				self.bot.sendmsg(user," !tv <sendername> <- zeigt das aktuelle Programm auf <sendername>.")
				self.bot.sendmsg(user," !tv liststations <- zeigt alle verfuegbaren Sender an.")
				self.bot.sendmsg(user," !tvsearch <begriff> <- sucht auf allen Sendern nach <begriff>.")
			elif len(o) != 0 and o[0].lower() == "liststations":
				stations = []
				for i in self.tv.stations:
					stations.append(self.tv.stations[i][0])
				self.bot.sendmsg(channel,"bekannte Sender: " + ",".join(stations))
			if o1 != "public" and len(o) == 1:
				try:
					int(o1)
					if int(o1) > 2400 or int(o1[2:4]) > 59:
						self.bot.sendmsg(channel,"corrupted time!")
						return 0
					programm = self.tv.get_programm_at_time(o1 + "00")
					programm = self.parse_programm(programm)
					filterstandard = 1
				except:
					if not self.tv.get_station(o1) and o1 != "help":
						self.bot.sendmsg(channel,"Station not found! See !tv help")
					else:
						programm = self.tv.get_programm_at_time_and_station(o1,str(ltime[3]) + str(ltime[4]) + "00")
				programm = self.parse_programm(programm)
			elif len(o) == 2:
				if not self.tv.get_station(o[1]):
					self.bot.sendmsg(channel,"Station not found! See !tv help")
					return 0
				else:
					if o1 == "now":
						o1 = str(ltime[3]) + str(ltime[4])
					try:
						int(o1)
						if int(o1) > 2400 or int(o1[2:4]) > 59:
							self.bot.sendmsg(channel,"corrupted time! See !tv help")
						programm = self.tv.get_programm_at_time_and_station(o[1],o1 + "00")
					except:
						if not self.tv.get_station(o1) and o1 != "help":
							self.bot.sendmsg(channel,"Station not found! See !tv help")
						else:
							programm = self.tv.get_programm_at_time_and_station(o1,str(ltime[3]) + str(ltime[4]) + "00")
					programm = self.parse_programm(programm)
			else:
				programm = self.tv.get_programm_now()
				programm = self.parse_programm(programm)
				filterstandard = 1
			for i in programm:
				if filterstandard == 1 and i['station'][0].lower().replace(" ","") not in self.standardsender:
					pass
				else:
					if not public:
						self.bot.sendmsg(user,unicode(str(chr(2)) + i['station'][0] + str(chr(2)) + " (" + str(i['start'][8:10]) + ":" + str(i['start'][10:12]) + "-" + str(i['stop'][8:10]) + ":" + str(i['stop'][10:12]) + "): " + i['title'] + " (" + i['language'] + ")").encode("utf8"))
					else:
						self.bot.sendmsg(channel,unicode(str(chr(2)) + i['station'][0] + str(chr(2)) + " (" + str(i['start'][8:10]) + ":" + str(i['start'][10:12]) + "-" + str(i['stop'][8:10]) + ":" + str(i['stop'][10:12]) + "): " + i['title'] + " (" + i['language'] + ")").encode("utf8"))
		elif command.lower() == "tvsearch":
			result = self.tv.search(options)
			result = self.parse_programm(result)
			for i in result[:3]:
				self.bot.sendmsg(channel,unicode(str(chr(2)) + i['station'][0] + str(chr(2)) + " (" + str(i['start'][8:10]) + ":" + str(i['start'][10:12]) + "-" + str(i['stop'][8:10]) + ":" + str(i['stop'][10:12]) + "): " + i['title'] + " (" + i['language'] + ")").encode("utf8"))
			if result == []:
				self.bot.sendmsg(channel,"keine passende Sendung gefunden!")
			
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
			if self.stations[i][0].lower().replace(" ","").replace(".","").replace("-","") == name.lower().replace(" ","").replace(".","").replace("-",""):
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
	
	def search(self,begriff):
			result = []
			for i in self.programm:
				if begriff.lower() in i['title'][0][0].lower():
					result.append(i)
			return result
	
	def get_programm_now(self):
		ltime = time.localtime()
		zeit = str(ltime[3]) + str(ltime[4]) + "00"
		programm = self.get_programm_at_time(zeit)
		return programm
