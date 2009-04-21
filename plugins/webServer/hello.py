from lib import chatMod
class Plugin(chatMod.chatMod):
    def __init__(self, wps):
        self.wps=wps
        wps.registerCallback(self, 'GET')
    def GET(self, path, headers, rfile, wfile, handler):
        if path=='/hello.html':
            wfile.write("<h1>Hello World!</h1>")
