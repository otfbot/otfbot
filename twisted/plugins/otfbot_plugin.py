from otfbot import otfbot
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from zope.interface import implements
from twisted.python import usage

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

serviceMaker=otfbotServiceMaker()
