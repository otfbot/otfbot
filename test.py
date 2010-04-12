import sys
from optparse import OptionParser

parser = OptionParser()
(options, args)=parser.parse_args()
if len(args) != 1:
    print "usage: test.py someMod"
    sys.exit(1)

import doctest
try:
    print args[0]
    module = __import__(args[0], fromlist=["*"])
    print module
    doctest.testmod(module, verbose=True)
except ImportError:
    print "import error for module \"%s\"" % args[0]
