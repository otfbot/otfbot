#!/usr/bin/python
#
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
# (c) 2005, 2006, 2007 by Alexander Schier

import threading, time
class Schedule(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.times=[]
		self.functions=[]
		self.stopme=False

	def stop(self):
		self.stopme=True

	def run(self):
		while not self.stopme:
			time.sleep(60)
			toremove=[]
			for i in range(len(self.times)):
				self.times[i]=self.times[i]-1
				if self.times[i]<=0:
					self.functions[i]()
					toremove.append(i)
			toremove.reverse()
			for i in toremove:
				del self.times[i]
				del self.functions[i]


	def addScheduleJob(self, wait, function):
		self.times.append( int(wait) )
		self.functions.append(function)
