from lib import chatMod
import logging

class Plugin(chatMod.chatMod):
    def __init__(self, wps):
        self.wps=wps
        wps.registerCallback(self, 'GET')
        self.logger = logging.getLogger("feedMod")
    def GET(self, path, headers, rfile, wfile, handler):
        if path=='/users':
            ircClient=self.wps.root.getServiceNamed("ircClient")
            ns=ircClient.namedServices
            for n in ns.keys():
                if not ns[n[ or not ns[n].protocol:
                    self.logger.warning("Error, %s is not connected.")
                    continue
                cud=ns[n].protocol.getChannelUserDict()
                for c in cud:
                    ops=0
                    hops=0
                    voices=0
                    for user in cud[c].keys():
                        if cud[c][user] & ns[n].protocol.rev_modchars['o']:
                            ops+=1
                        elif cud[c][user] & ns[n].protocol.rev_modchars['h']:
                            hops+=1
                        elif cud[c][user] & ns[n].protocol.rev_modchars['v']:
                            voices+=1
                    wfile.write("%s.%s: %s\n"%(n, c, len(cud[c])))
                    #wfile.write("%s.%s.total: %s\n"%(n, c, len(cud[c])))
                    #wfile.write("%s.%s.ops: %s\n"%(n, c, ops))
                    #wfile.write("%s.%s.hops: %s\n"%(n, c, hops))
                    #wfile.write("%s.%s.voices: %s\n"%(n, c, voices))
        if path=='/lines':
            for network in self.wps.root.getServiceNamed("ircClient").services:
                if network and network.protocol: #no NoneType Exception on disconnected network
                    for channel in network.protocol.getChannelUserDict().keys():
                        wfile.write("%s.%s: %s\n"%(network.name, channel, network.protocol.plugins['ircClient.count'].getLinesPerMinute(channel)))
#app.getServiceNamed("ircClient").services[0].protocol.plugins['plugins.ircClient.ki']
