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
# (c) 2007 by Robert Weidlich

class Scheduler:
    """Wrapper class for the scheduling functions of twisted.internet.reactor.ReactorTime"""
    def __init__(self,reactor):
        self.reactor=reactor
    def addJob(self,time,function,*args,**kwargs):
        """executes the given function after time seconds with arguments (*args) and keyword arguments (**kwargs)"""
        self.reactor.callLater(time,function,*args,**kwargs)

    def addPeriodicJob(self,delay,function,kwargs={}):
        """executes the given function every delay seconds with keyword arguments (**kwargs)"""
        def func(delay,function,**kwargs):
            args=(delay,function)
            if not function(**kwargs):
                self.reactor.callLater(delay,func,*args,**kwargs)
        args=(delay,function)
        self.reactor.callLater(delay,func,*args,**kwargs)