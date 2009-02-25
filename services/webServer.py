from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from lib.pluginSupport import pluginSupport

from twisted.application import service
import thread, logging

class botService(service.MultiService):
	name="webServer"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		service.MultiService.__init__(self)
	def startService(self):
		self.config=self.root.getNamedServices()['config']
		self.server=myHTTPServer(("0.0.0.0", 8080), myHTTPRequestHandler, self.root, self)
		self.thread=thread.start_new_thread(self.server.serve_forever, ())
		service.MultiService.startService(self)  

class myHTTPServer(HTTPServer):
	def __init__(self, server_address, RequestHandlerClass, root, parent):
		self.root=root
		self.parent=parent
		HTTPServer.__init__(self, server_address, RequestHandlerClass)
		self.wps=webPluginSupport(root, self)

	def finish_request(self, request, client_address):
		self.request=request
		self.client_address=client_address
		self.RequestHandlerClass(request, client_address, self, self.wps)

class webPluginSupport(pluginSupport):
	pluginSupportName="webServer"
	pluginSupportPath="plugins/webServer"
	def __init__(self, root, parent):
		self.root=root
		self.parent=parent
		pluginSupport.__init__(self, root, self.parent)
		self.logger=logging.getLogger("webServer")
		self.startPlugins()

#TODO: the Requesthandler is reinstanced on every request. the pluginSupport should be in a singleton
class myHTTPRequestHandler(pluginSupport, BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server, wps):
		self.wps=wps
		BaseHTTPRequestHandler.__init__(self, request, client_address, server)
	def do_GET(self):
		self.wps._apirunner("GET", {'path': self.path, 'headers': self.headers, 'rfile': self.rfile, 'wfile': self.wfile, 'handler': self})
