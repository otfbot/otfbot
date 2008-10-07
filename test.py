import sys
from optparse import OptionParser
sys.path.insert(1,"lib") # Path for auxilary libs of otfbot
sys.path.insert(1,"modules")

parser=OptionParser()
(options, args)=parser.parse_args()
if len(args)!=1:
	print "usage: test.py someMod"
	sys.exit(1)

import doctest
try:
	module=__import__(args[0])
	doctest.testmod(module)
except ImportError:
	print "import error for module \"%s\""%args[0]

