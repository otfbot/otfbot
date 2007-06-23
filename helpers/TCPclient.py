#!/usr/bin/python
from twisted.internet import protocol, error, reactor
from twisted.protocols import basic
import readline
readline.parse_and_bind("tab: complete")

class ARLCompleter:
    def __init__(self,logic):
        self.logic = logic

    def traverse(self,tokens,tree):
        if tree is None:
            return []
        elif len(tokens) == 0:
            return []
        if len(tokens) == 1:
            return [x+' ' for x in tree if x.startswith(tokens[0])]
        else:
            if tokens[0] in tree.keys():
                return self.traverse(tokens[1:],tree[tokens[0]])
            else:
                return []
        return []

    def complete(self,text,state):
        try:
            tokens = readline.get_line_buffer().split()
            if not tokens or readline.get_line_buffer()[-1] == ' ':
                tokens.append("")
            results = self.traverse(tokens,self.logic) + [None]
            return results[state]
        except Exception,e:
            print e


class BotProtocol(basic.LineOnlyReceiver):
	prompt="prompt"
	def lineReceived(self, data):
		noask=False
		if data[0] == "0":
			noask=True
			if data[1] == "1":
				logic={}
				values={}
				for x in data[3:].split(":"):
					if x[0] == "+":
						tmp=x[1:].split(",")
						key=tmp.pop(0)
						values[key]={}
						for y in tmp:
							values[key][y] = None
					else:
						tmp=x.split(",")
						if len(tmp) == 1:
							logic[tmp[0]]=None
						else:
							key=tmp.pop(0)
							logic[key]={}
							for y in tmp:
								if y[0] == "+":
									logic[key] = values[y[1:]]
								else:
									logic[key][y] = None
				completer = ARLCompleter(logic)
				readline.set_completer(completer.complete)
			elif data[1] == "2":
				self.prompt=data[3:]
			elif data[1] == "0":
				noask=False
		else:
			print data
		if not noask:
			self.ask()

	def connectionMade(self):
		print "connection made"
		self.sendLine("hallo")
		
	def ask(self):
		#end=False
		#while not end:
			try:
				input = raw_input(self.prompt+"> ")
				self.sendLine("shell prompt")
				self.sendLine("shell readline")
				self.sendLine(input)
			except EOFError:
		#		end=True
				reactor.stop()
				print

class BotProtocolFactory(protocol.ClientFactory):
        protocol=BotProtocol

f=BotProtocolFactory()
print reactor.connectTCP("localhost", 5022, f)
reactor.run()
