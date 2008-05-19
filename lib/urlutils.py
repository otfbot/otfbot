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
# (c) 2008 by Alexander Schier
#
import urllib2
def download(url):
	try:
		urllib2.install_opener(urllib2.build_opener(urllib2.HTTPRedirectHandler()))
		req = urllib2.Request(url)
		svnrevision="$Revision: 187 $".split(" ")[1]
		req.add_header("user-agent", "OTFBot (svn r%s; otfbot.berlios.de)"%(svnrevision))
		url=urllib2.urlopen(req)
		data=url.read()
		url.close()
		return data
	except urllib2.HTTPError, e:
		return str(e)
	except urllib2.URLError, e:
		return req.get_host()+": "+str(e.reason[1])
