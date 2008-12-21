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
# (c) 2008 Robert Weidlich
#

class controlInterface:
	""" allows to control the behaviour of the bot during runtime
	
		this class only does the work, you need another class, most suitable is a bot-module, to have a userinterface
	"""
	def __init__(self, control):
		"""
			@type bot: a L{Bot} Instance
		"""
		self.subcmd=""
		self.subcmdval=""
		self.controlClass=control
	
	def _output(self, out):
		""" helper function which set the encoding to utf8
		"""
		if type(out)==list:
			for i in xrange(len(out)):
				out[i]=unicode(out[i]).encode("UTF-8")
			return out
		else:
			return unicode(out).encode("utf-8")	
	
	def input(self, request):
		""" Pass your command to this function and get the output
			@param request: command and arguments
			@type request: string
			@rtype: string
			@return: the output of the command
		"""
		# try to guess, what the user wants
		tmp = request.strip().split(" ")
		# try 1: a command in the current namespace
		func = getattr(self.controlClass,"_cmd_"+self.subcmd+"_"+tmp[0], None)
		args = " ".join(tmp[1:])
		# try 2: directly called subcommand
		if not callable(func) and len(tmp) > 1:
			func = getattr(self.controlClass,"_cmd_"+tmp[0]+"_"+tmp[1], None)
			args = " ".join(tmp[2:])
		# try 3: a toplevel command
		if not callable(func):
			func = getattr(self.controlClass,"_cmd_"+tmp[0], None)
			args = " ".join(tmp[1:])
		# try 4: change the namespace
		if not callable(func):
			found=False;
			for c in dir(self):
				if c[5:5+len(tmp[0])] == tmp[0]:
					self.subcmd=tmp[0]
					return self._output("Changing to namespace "+tmp[0])
		if callable(func):
			return self._output(func(args))
		else:
			return self._output("No such command: "+str(tmp[0]))