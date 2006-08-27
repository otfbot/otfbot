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
# (c) 2006 by Robert Weidlich
#

import string, re, functions
import urllib

def default_settings():
	settings={};
	return settings
		
class chatMod:
	def __init__(self, bot):
		self.bot = bot
		self.channels={}
		
	def joined(self, channel):
		self.channels[channel]=1
	
	def msg(self, user, channel, msg):
		nick=user.split("!")[0]
		if msg[:5] == "!kurs":
			data = urllib.urlopen("http://de.old.finance.yahoo.com/d/quotes.csv?s="+msg.split(" ")[1]+"&f=nsl1d1t1cohgvc4&e=.csv").read().strip().split(';')
			date = data[3].split("/")
			d = { 'name' : data[0], 
			      'symbol' : data[1],
			      'kurs' : data[2],
			      'day' : date[1]+"."+date[0]+"."+date[2],
			      'time' : data[4],
			      'change_kurs' : data[5].split(" - ")[0],
			      'change_percent' : data[5].split(" - ")[1],
			      'last_day' : data[6],
			      'top_range' : data[7],
			      'low_range' : data[8],
			      'avr_vol' : data[9],
			      'currency' : data[10] }
			# \x03C C=Colorcode
			answer = nick+": am "+d['day']+" um "+d['time']+" lag der Kurs von "+d['name']+" ("+d['symbol']+") bei "+d['kurs']+" "+d['currency']
			if d['change_kurs'] != "N/A":
				if d['change_kurs'][:1] == "+":
					color="3"
				else:
					color="4"
				answer = answer +", das sind \x03"+color+d['change_kurs']+" "+d['currency']+"\x03 oder \x03"+color+d['change_percent']+"\x03 Unterschied zum Vortag."
			if d['low_range'] != "N/A":
				answer = answer + " Im Tagesverlauf schwankte der Kurs von "+d['low_range']+" "+d['currency']+" bis "+d['top_range']+" "+d['currency']+"."
			if d['kurs'] == "N/A":
				answer = "Der geforderte Kurs wurde nicht gefunden."
			self.bot.sendmsg(channel,answer)
		if msg[:4] == "!wkn":
			res=[]
			for line in urllib.urlopen("http://de.finsearch.yahoo.com/de/index.php?s=de_sort&nm="+" ".join(msg.split(" ")[1:])+"&tp=S").read().split("\n"):
				if line[:3] == " <a":
					res.append(re.sub('.*s\=([^"]*)">([^<]*)<.*',r'\1;\2',line).split(";"))
			if len(res) < 4:
				to = len(res)
			else:
				to = 4
			for i in range(to):
				self.bot.sendmsg(channel,res[i][0]+"\t"+res[i][1])
	def reload(self):
		self.answers = functions.loadProperties(self.answersFile)
