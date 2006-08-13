#!/usr/bin/python

from xml.sax import saxutils
import string, pprint

def normalize_whitespace(text):
    "Remove redundant whitespace from a string"
    return ' '.join(text.split())

class ParseConfig(saxutils.DefaultHandler):
	def __init__(self):
		self.current=[]
		self.config={}
		self.current_mod=""
		self.op=-1
		self.net=""
		self.chan=""
	
	def startElement(self, name, attrs):
		self.current.append(str(name))
		if name == "modul":
			self.current_mod=attrs.get('name', None)
		if name == "general":
			self.config['general']={}
		if name == "network":
			if 'network' not in self.config:
				self.config['network'] = {}
			self.config['network'][attrs.get('name','')] = {}
			self.net=attrs.get('name','')
		if name == "channel":
			if 'channel' not in self.config['network'][self.net]:
				self.config['network'][self.net]['channel'] = {}
			self.config['network'][self.net]['channel'][attrs.get('name','')] = {}
			self.chan = attrs.get('name','')
		if self.current[-1] == "modul":
			if self.current[1] == "general":
				if not 'module' in self.config[self.current[1]]: 
					self.config[self.current[1]]['module'] = {}
				if not self.current_mod in self.config[self.current[1]]['module']: 
					self.config[self.current[1]]['module'][self.current_mod]={}
			elif self.current[1] == "network" and not self.current[2] == "channel":
				if not 'module' in self.config[self.current[1]][self.net]:
					self.config[self.current[1]][self.net]['module'] = {}
				if not self.current_mod in self.config[self.current[1]][self.net]['module']:
					self.config[self.current[1]][self.net]['module'][self.current_mod] = {}
			elif self.current[1] == "network" and self.current[2] == "channel":
				if not 'module' in self.config[self.current[1]][self.net]['channel'][self.chan]:
					self.config[self.current[1]][self.net]['channel'][self.chan]['module'] = {}
				if not self.current_mod in self.config[self.current[1]][self.net]['channel'][self.chan]['module']:
					self.config[self.current[1]][self.net]['channel'][self.chan]['module'][self.current_mod] = {}

		if name == "param" and self.current[-2] == "modul":
			if self.current[1] == "general":
				mod=self.config[self.current[1]]['module'][self.current_mod]
			elif self.current[1] == "network" and not self.current[2] == "channel":
				mod=self.config[self.current[1]][self.net]['module'][self.current_mod]
			elif self.current[1] == "network" and self.current[2] == "channel":
				mod=self.config[self.current[1]][self.net]['channel'][self.chan]['module'][self.current_mod]
			name = str(attrs.get('name',''))
			if name in mod:
				if type(mod[name]) != 'list':
					tmp=mod[name]
					mod[name]=[]
					mod[name].append(tmp)
			if name in mod and type(mod[name]) == 'list':
				mod[name].append(attrs.get('value',''))
			else:
				mod[attrs.get('name','')] = attrs.get('value','')
			if self.current[1] == "general":
				self.config[self.current[1]]['module'][self.current_mod] = mod
			elif self.current[1] == "network" and not self.current[2] == "channel":
				self.config[self.current[1]][self.net]['module'][self.current_mod] = mod
			elif self.current[1] == "network" and self.current[2] == "channel":
				self.config[self.current[1]][self.net]['channel'][self.chan]['module'][self.current_mod] = mod
		if name == "operator":
			self.op=self.op+1
			if not 'operator' in self.config[self.current[1]]: 
				self.config[self.current[1]]['operator']=[]
			self.config[self.current[1]]['operator'].append({})
	
	def characters(self, ch):
		if len(self.current) == 3 and self.current[2] in ('nickname','realname','server','port'):
			if self.current[1] == "general":
				self.config[self.current[1]][self.current[2]] = normalize_whitespace(ch)
			if self.current[1] == "network":
				self.config[self.current[1]][self.net][self.current[2]] = normalize_whitespace(ch)
		if len(self.current) == 4 and self.current[2] == "operator":
			self.config[self.current[1]]['operator'][self.op][self.current[3]] = normalize_whitespace(ch)
		if self.current[-1] == "enable" and normalize_whitespace(ch).lower() == "false":
			if self.current[1] == "general":
				self.config[self.current[1]]['module'][self.current_mod] = {'disabled': 'disabled'}
			if self.current[1] == "network" and not self.current[2] == "channel":
				self.config[self.current[1]][self.net]['module'][self.current_mod] = {'disabled': 'disabled'}
			if self.current[1] == "network" and self.current[2] == "channel":
				self.config[self.current[1]][self.net]['channel'][self.chan]['module'][self.current_mod] = {'disabled': 'disabled'}
 

	def endElement(self, name):
		self.current.pop()
		if name == "chatbot":
			pp = pprint.PrettyPrinter(width=1)
			pp.pprint(self.config)

from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

if __name__ == '__main__':
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = ParseConfig()

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    parser.parse("config.xml")
