from optparse import OptionParser
def parse():
	parser = OptionParser()
	parser.add_option("-c","--config",dest="configfile",metavar="FILE",help="Location of configfile",type="string")
	parser.add_option("-d","--debug",dest="debug",metavar="LEVEL",help="Show debug messages of level LEVEL (10, 20, 30, 40 or 50). Implies -f.", type="int", default=0)
	parser.add_option("-f","--nodetach",dest="foreground",help="Do not fork into background.",action="store_true", default=False)

	parser.add_option("-u","--user",dest="userid",help="if run as root, the bot needs a userid to chuid to.",type="int", default=0)
	parser.add_option("-g","--group",dest="groupid",help="if run as root, the bot needs a groupid to chgid to.",type="int", default=0)

	(options,args)=parser.parse_args()
	if options.debug and options.debug not in (10,20,30,40,50):
		parser.error("Unknown value for --debug")
	return (options, args)
