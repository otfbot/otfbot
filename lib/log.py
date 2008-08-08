









# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# from http://twistedmatrix.com/trac/browser/tags/releases/twisted-8.1.0/twisted/python/log.py
import logging
from twisted.python import log, reflect
class PythonLoggingObserver(object):
    """
    Output twisted messages to Python standard library L{logging} module.

    WARNING: specific logging configurations (example: network) can lead to
    a blocking system. Nothing is done here to prevent that, so be sure to not
    use this: code within Twisted, such as twisted.web, assumes that logging
    does not block.
    """

    def __init__(self, loggerName="twisted"):
        """
        @param loggerName: identifier used for getting logger.
        @type loggerName: C{str}
        """
        self.logger = logging.getLogger(loggerName)
	self.logger.info("added twisted-logger")

    def emit(self, eventDict):
        """
        Receive a twisted log entry, format it and bridge it to python.

        By default the logging level used is info; log.err produces error
        level, and you can customize the level by using the C{logLevel} key::

        >>> log.msg('debugging', logLevel=logging.DEBUG)

        """
        if 'logLevel' in eventDict:
            level = eventDict['logLevel']
        elif eventDict['isError']:
            level = logging.ERROR
        else:
            level = logging.INFO
        text = self.textFromEventDict(eventDict)
        if text is None:
            return
        self.logger.log(level, text)

    def start(self):
        """
        Start observing log events.
        """
        log.addObserver(self.emit)

    def stop(self):
        """
        Stop observing log events.
        """
        log.removeObserver(self.emit)
    def textFromEventDict(self,eventDict):
    	"""
    	Extract text from an event dict passed to a log observer. If it cannot
    	handle the dict, it returns None.
	
    	The possible keys of eventDict are:
     	- C{message}: by default, it holds the final text. It's required, but can
       	be empty if either C{isError} or C{format} is provided (the first
       	having the priority).
     	- C{isError}: boolean indicating the nature of the event.
     	- C{failure}: L{failure.Failure} instance, required if the event is an
       	error.
     	- C{why}: if defined, used as header of the traceback in case of errors.
     	- C{format}: string format used in place of C{message} to customize
       	the event. It uses all keys present in C{eventDict} to format
       	the text.
    	Other keys will be used when applying the C{format}, or ignored.
    	"""
    	edm = eventDict['message']
    	if not edm:
	        if eventDict['isError'] and 'failure' in eventDict:
            		text = ((eventDict.get('why') or 'Unhandled Error')
                    	+ '\n' + eventDict['failure'].getTraceback())
        	elif 'format' in eventDict:
	            	text = _safeFormat(eventDict['format'], eventDict)
        	else:
        	    	# we don't know how to log this
            		return
    	else:
        	text = ' '.join(map(reflect.safe_str, edm))
    	return text