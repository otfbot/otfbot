from lib import chatMod, functions
import time

class Plugin(chatMod.chatMod):
    def __init__(self,bot):
        self.linesperminute={}
        self.new_linesperminute={}
        self.minute={}
    def msg(self, user, channel, msg):
        new_minute=int(time.strftime("%M"))
        if not self.minute.has_key(channel) or self.minute[channel] != new_minute:
            self.minute[channel]=new_minute
            if not self.new_linesperminute.has_key(channel):
                self.new_linesperminute[channel]=0
            self.linesperminute[channel]=self.new_linesperminute[channel]
            self.new_linesperminute[channel]=0
        else:
            self.new_linesperminute[channel]+=1
    def getLinesPerMinute(self, channel):
        if self.linesperminute.has_key(channel):
            return self.linesperminute[channel]
        else:
            return 0
