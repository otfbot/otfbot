from otfbot import otfbot
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from zope.interface import implements
from twisted.python import usage
import time

class Options(usage.Options):
	    optParameters = []

class otfbotServiceMaker(object):
	implements(IServiceMaker, IPlugin)
	tapname="otfbot"
	description = "OTFBot the friendly Bot"
	options=Options

	def makeService(self, options):
		self.bot=otfbot()
		self.bot.main()
		while True:
			time.sleep(1)

serviceMaker=otfbotServiceMaker()
