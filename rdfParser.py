import xml.sax
import xml.sax.handler

#Copyright (C) 2005 Alexander Schier
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along
#with this program; if not, write to the Free Software Foundation, Inc.,
#51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


class rdfHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.elements = {}
		self.links = []
		
		self.inItem = 0;
		self.inTitle = 0;
		self.inLink = 0;
		
		self.currentTitle = "";
		self.currentLink = "";
	def startElement(self, name, attributes):
		if name == "item":
			self.inItem = 1
		if name == "title":
			self.inTitle = 1
		if name == "link":
			self.inLink = 1
	def characters(self, data):
		if self.inItem:
			if self.inTitle:
				self.currentTitle += data
			if self.inLink:
				self.currentLink += data
	def endElement(self, name):
		if name == "title":
			self.inTitle = 0;
		if name == "link":
			self.inLink = 0;
		if name == "item":
			self.elements[self.currentLink] = self.currentTitle;
			self.links.append(self.currentLink)
			self.currentTitle = ""
			self.currentLink = ""
			self.inItem = 0

def parse(url):
	try:
		parser = xml.sax.make_parser()
		handler = rdfHandler()
		parser.setContentHandler(handler)
		parser.parse(url)
		return {'links': handler.links, 'elements': handler.elements}
	except Exception:
		print "rdfParser: Parse Exception"
		return {'links': [], 'elements': []}
