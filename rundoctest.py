import sys
from optparse import OptionParser

parser = OptionParser()
(options, args) = parser.parse_args()
if len(args) != 1:
    print "usage: test.py otfbot.plugins.service.somePlugin"
    print "i.e.: test.py otfbot.plugins.ircClient.ki"
    sys.exit(1)

import doctest
try:
    print args[0]
    module = __import__(args[0], fromlist=["*"])
    print module
    doctest.testmod(module, verbose=True)
except ImportError, e:
    print "import error for module \"%s\" %s" % (args[0], e)
