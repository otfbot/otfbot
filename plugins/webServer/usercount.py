from lib import chatMod
class Plugin(chatMod.chatMod):
    def __init__(self, wps):
        self.wps=wps
        wps.registerCallback(self, 'GET')
    def GET(self, path, headers, rfile, wfile, handler):
        if path=='/users':
            ns=self.wps.root.getServiceNamed("ircClient").namedServices
            for n in ns:
                cud=ns[n].protocol.getChannelUserDict()
                for c in cud:
                    wfile.write("%s.%s: %s"%(n, c, len(cud[c])))
        if path=='/lines':
            for network in self.wps.root.getServiceNamed("ircClient").services:
                for channel in network.protocol.getChannelUserDict().keys():
                    wfile.write("%s.%s: %s"%(network.name, channel, network.protocol.plugins['plugins.ircClient.count'].getLinesPerMinute(channel)))
#app.getServiceNamed("ircClient").services[0].protocol.plugins['plugins.ircClient.ki']
