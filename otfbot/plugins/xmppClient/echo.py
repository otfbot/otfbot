from otfbot.lib.pluginSupport.decorators import callback
from otfbot.lib.pluginSupport import plugin

from twisted.words.xish import domish

class Plugin(plugin.Plugin):
    def __init__(self, bot):
        self.bot = bot
        self.bot.logger.debug("Hello world")
    @callback
    def onMessage(self, msg):
        if not msg.body:
            return

        if msg["type"] == 'chat' and hasattr(msg, "body") \
            and not str(msg.body)[0:4]=="?OTR":

            reply = domish.Element((None, "message"))
            self.logger.debug("To: %s"%msg['from'])
            self.logger.debug("From: %s"%msg['to'])
            self.logger.debug("Message: %s"%str(msg.body))
            reply["to"] = msg["from"]
            reply["from"] = msg["to"]
            reply["type"] = 'chat'
            reply.addElement("body", content="echo: " + str(msg.body))

            self.bot.send(reply)
