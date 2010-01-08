from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service

from otfbot.services import config as configService
from otfbot.lib import version

class Options(usage.Options):
        optParameters = [["config","c","otfbot.yaml","Location of configfile"]]

class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "otfbot"
    description = "OtfBot - The friendly Bot"
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in myproject.
        """

        application = service.MultiService()
        application.version=version._version
        
        configS=configService.loadConfig(options['config'], "plugins/*/*.yaml")
        if not configS:
            print "please run helpers/generateconfig.py"
            sys.exit(1)
        configS.setServiceParent(application)

        service_names=configS.get("services", [], "main")
        service_classes=[]
        service_instances=[]
        for service_name in service_names:
            #corelogger.info("starting Service %s" % service_name)
            service_classes.append(__import__("otfbot.services."+service_name, fromlist=['botService']))
            service_instances.append(service_classes[-1].botService(application, application))
            service_instances[-1].setServiceParent(application)

        return application


# Now construct an object which *provides* the relevant interfaces
# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.

serviceMaker = MyServiceMaker()
