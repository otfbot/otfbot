from lib import chatMod, functions
import time

class Plugin(chatMod.chatMod):
    def __init__(self,bot):
        self.linesperminute={}
        self.new_lines={}
        self.timestamp={}
    def msg(self, user, channel, msg):
        self.calcLPM(channel)
        self.new_lines[channel][-1]+=1
    def calcLPM(self, channel):
        new_timestamp=int(time.time())
        if not self.timestamp.has_key(channel):
            self.timestamp[channel]=new_timestamp
        if not self.new_lines.has_key(channel):
            self.new_lines[channel]=[0,0,0,0,0]
        if new_timestamp - self.timestamp[channel] >= 60:
            self.linesperminute[channel]=reduce(lambda x,y:x+y, self.new_lines[channel][:-1])*60/4.0/(new_timestamp - self.timestamp[channel])
            self.new_lines[channel]=self.new_lines[channel][1:]
            self.new_lines[channel].append(0)
            self.timestamp[channel]=new_timestamp
    def getLinesPerMinute(self, channel):
        self.calcLPM(channel)
        if not self.linesperminute.has_key(channel):
            self.linesperminute[channel]=0
        return self.linesperminute[channel]