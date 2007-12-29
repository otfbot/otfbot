# This file is part of OtfBot.
#
# OtfBot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OtfBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OtfBot; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
# (c) 2006 by Alexander Schier
#
# much to read, sry ;) hope u like it
#/*
#.oO(remember the python Framework itself is NOT GPL - what it makes difficult to deal with and to trust in...)
#Thanks to "Wete" and "p_kater" for the very good input (ideas) for this game, and of course 
#{replace your nicks if you want} "allo" and "cato" (for the basement at least)
#Let's make this game famous :)
#Note: Still under construction
#*/
import shutil, time, random, string, os 
import chatMod
from string import Template #obsolete
#game modified and "prettyfied" by neTear 12/2007 with Midnight Commander, just because python sucks...

import twisted.internet.task as hack #*scnr* twisted seems to be ugly sometimes. Todo: rename that ....
#import pdb <-lol I WANT to see the stack!

# AND NOW to something completely different! On the behalf of "Monty" - to sound more serious this was the name of my last dog ...
# reactor/.callLater seems to have a problem with ns, even if inherited by "self" (see your scheduler.py), 
# you won't have a pointer (handle? whatever called in Python [addition:Reference])  to your timer within your class, shame on twisted.* ?
# Well, it's not a bug obvisioly. Everytime you call a reactor.callLater you
# have another reference, This is OOP and the same in other script languages like tcl perl and so on
# So now we have an own "timehook" for this game, 
# ...but there seems to be something really ugly within twisted (which doesn't matter for the gameplay at all), some error messages
# when task.loopingCall has been stopped, I did not track that for now, just learning another language ...
# a) workaround (and at least the solution for the bot itself) - with the class "task" and an own timerhook
# b) well, I decided to add some features, eyecandy and enhancements for a a better gameplay, too... oneday this game should be multilinugal 
# Todo s: (grep them)
# trunc/bound irc msg? don't know (at the moment) if and how it takes place beyound this playground
# irc outputs configurable/translated
# channel userlist, even maybe the solution for multi-channel-support of this game
# you already know, there are "always" several things to do... see yourself
######################## config still under development ............. 
ANSWER_TIME=120 #90 time for player to send in an answer
QUIZ_TIME=60   #60 time waiting for quiz answers
TIMEOUT=120 #300 idle time until game stops to "game_waiting", "waiting_for_gamemaster" NIP-Question
STARTPHASE=999 #not used yet. TODO - after this timeout game should start (maybe for autostarting) which mode can be toogled during gameplay, we should think about the howto
FLOODPROTECTION=42 # I thought this game needs something like that o_O
#we now use them as default base values, - gamespeed will be controlled by the new timer[hook]
GAMEADMINNOTIFY=60 #sends just a "highlight" to a sleeping "gameadmin" =0 disabled,do not do this without "STARTPHASE"
GAMEADMINKICK=46 #kick the lazy gameadmin after notify, [re]starter|aborter will be the new one 
#TODO timeouts by bot config
#some eycandy, some tries
#TODO get a real nice default one, to be tested with main clients....
#konservation seems to have a problem with these data, mIRC first char if this is [CTRL]led # need to dump raw data?
#NIPPREFIX="\x02\x031,15NIP\x033\x02\x0F" #nip gameplay pre output
#NIPPREFIX="|\x0316,14NIP\x033\x0F" #nip gameplay pre output this - may be set to =""
NIPPREFIX="|\x0316,14NIP\x033\x0F" #nip gameplay pre output this - may be set to =""

#NIPPREFIX="\x0311,8|\x0311,7|\x0311,4|\x0311,5|\x0311,1|\x0F" #nip gameplay pre output
#NIPPREFIX="\x038.\x037.\x034.\x035.\x031.\x0F" #nip gameplay pre output
#####
### REQ_TIME will be/setto your timeouts within new functions....

RULES="http://otf-chat.xenim.de/wiki/bot:nobody-is-perfect"
#there are serveral synonyms for commands... 
#some (m)IRCstuff... I LOVE eyecandy! (but it must not disturb)
#irssi > set mirc_blink_fix on
#and x-chat mIRC cZ are okay with these raw color values
BOLD="\x02" #tooglelike 
NORM="\x0F" #resetallMIRColorslike
UNDERLINE="\x1F" # tooglelike 
DBLUE="\x032"
DGREEN="\x033"
RED="\x034"
DRED="\x035"
CYAN="\x0311"
DCYAN="\x0310"
BLUE="\x0312"
DGREY="\x0314"
GREY="\x0315"
LGREY="\x0316"
MAGENTA="\x0313"
DMAGENTA="\x036"
#TODO define NIPPREFIXs here and Colors, maybe good in an init function....
#These are $category depending colored "2nd Pre-things" - well I don't know how to assign them (TODO have to be fixed in code)
#
#pchar="\xc2\xb7" #middle dot hmmm sometimes unicode is ... todo 
pchar="_" #fix for none monospace clients, well no monospace within irc no good face
PRE_N="\x031,1"+pchar+"\x0F "	#Black after Standard Prefix as default nr 2, and special ones for special conditions
PRE_Q="\x034,4"+pchar+"\x0F "	#Red - Send me the Question /The question is/was
PRE_A="\x033,3"+pchar+"\x0F "	#Dark Green right Answer
PRE_C="\x039,9"+pchar+"\x0F "	#Light Green for possible answers are (c like conjuntive)
PRE_H="\x038,8"+pchar+"\x0F "	#Yellow for SCORE-LIST
PRE_S="\x037,7"+pchar+"\x0F "	#dark yellow for scoring
PRE_H="\x0311,11"+pchar+"\x0F "	#cyan for help messages
PRE_X="\x036,6"+pchar+"\x0F "	#magenta for messages to gameadmin
PRE_G="\x035,5"+pchar+"\x0F "	#dark red for game status things....
PRE_P="\x0312,12"+pchar+"\x0F " #Light blue for Punishments
PRE_Z="\x035,5"+pchar+"\x0F " #Dark Red also for Hall of fame? try?


#TODO tidy up this const stuff
#make all the vars local later, build them in function, 
cchar="!" #default hardcoded init here, should all be in one function...
hofdatafile=""
nipdatadir=""
TGAMEADMIN=BOLD+"Spieladmin"+BOLD #just the word -> multilingual
TGAMEMASTER=BOLD+"Spielmeister"+BOLD #same her
TNIPQUESTION=BOLD+BLUE+"NIP-FRAGE"+NORM #word for Question of Question, What has been the Question?
TNIPGAME="" # todo not used yet The Name of game
#Todo build "HELP" from "knowncommands" (nip-internal)
HELPUSER=cchar+"join "+cchar+"part (mitspielen/aussteigen) "+cchar+"score "+cchar+"rules "+cchar+"players"
HELPADMIN=cchar+"abortgame "+cchar+"restartgame "+cchar+"add/remove Mitspieler "+cchar+"gamespeed "+cchar+"autoremove "+cchar+"autostart "+cchar+"kill "
#temporaly  ... Todo (->wiki)
HELPBUG="Genervte "+BOLD+"irssi"+BOLD+"-Anwender moegen ein \"/set mirc_blink_fix on\" machen, oder x-chat,chatzilla,mIRC oder Telnet... benutzen ;)"

#game phases
NO_GAME=0
WAITING_FOR_PLAYERS=1
WAITING_FOR_QUESTION=2 
WAITING_FOR_QUIZMASTER_ANSWER=3
WAITING_FOR_ANSWERS=4
QUIZ=5
GAME_WAITING=6

class chatMod(chatMod.chatMod): #chatmod? this is game ... later :) 
        #hofdatafile=""
	def __init__(self, bot):
	        self.bot=bot
	        self.dl=10 #0 print nothing, 10 prints something 60 prints timehooks (polltime) - too verbose for log, but good to track game flow
		self.default_nip()
		self.bot=bot
		self.init_vars()
		self.allscore={}
		
		self.init_autocmd() #known cmds for this mod
		self.nT_init() #init the looptimer with polltime (will be used for different timeoutsetups
		self.polltime=2    #timer poll in seconds, well, easier than in C, no care about a floating point, nice (not all is bad). (new) 
		self.gl_ts=0       #timestamp for timeouts, needs to be initialised - <=0 is the hook
		#   WELL, THIS^  takes less resources internally, we do not need an accurate timer inhere 
		self.gamespeed=1 #default gamespeed=1 normal 2= faster timeouts/2, should enough for now
		self.timerinfo=0 #to show timeouts for user
		self.minplayersold=0 #toogle cmd "testing"
		self.autoremove=1 #"!autoremove" toggles 0|1, if set to 1 - players will be removed from list when they do not send in question/answer 
		self.splitpoints=1 #!splitpoints" toggles between 0|1, used to show splittet points. if true returns details in scoring 
		self.autostart=0  #!autostart in conjunction with startphase-timeerhook TODO
		self.hookaction="None" #which function to call on timerhook, we might use exec() in future
		self.hof_show_max_player=8  #max player from HoF to send in channel #
		self.hof_max_player=99 #max players in hof-file todo, crop file after resorting/reloading
		self.fp_time=FLOODPROTECTION #time(out) used in game
		self.fp_ts=0 #same as self.gl_ts this one is used for floodprotection
		self.fp_init() #fp timer init
		self.is_fp=0 #"is floodprotected" just a flag, we could use timer.running, but one day we should have a nip class :) (better for reading code)
		self.nameofgame="\x038,1\x02|_\x02-\x037~\x034N\x035\x02o\x02 \x034B\x037o\x038\x02d\x02y \x037i\x034s \x035\x02p\x02\x034e\x037r\x038f\x02e\x02c\x037t\x034~\x035\x02-\x02\x034_\x038|\x0F" #"colors are fun when you don't abuse them"
		#todo make const and or config ^^^ (xml sucks for config?)
		#self.dl=10 #0 print nothing to stdout #10 prints something, #NIL #60 prints timehooks (too verbose for a log)		

		if self.dl:
		   print "*** NIP Mod loaded somewhat EARlier***"
		   print "NIPdebug: Entering Level "+str(self.dl)
		   #print "NIPdebug Command char is "+cchar
	        self.hof=self.nip_hof(self.nipdatadir+self.hofdatafile,"read") #
		cchar=self.cchar   
		##########################################################
		#########################################################
		####################################################
		
	def default_nip(self):
	    #first using global vars, try to make them local when everything works
	    #the best would be to make a function for all outputs.... nip_sendmsg,- guess, this game as being opensource will become famous
	    self.cchar=cchar
	    self.nipdatadir=self.bot.getConfig("datadir","modules/nip-data/","NIP",None,None)
	    self.hofdatafile=self.bot.getConfig("HoFdata","niphof.txt","NIP",None,None)
	    self.channels=self.bot.getConfig("channels","#heise-otf #nobody-is-perfect","NIP",None,None).split() #all channels where NIPmod will throw messages from and allow to start a game
	    self.minplayers=int(self.bot.getConfig("minPlayer","5","NIP",None,None)) #assert
	    self.maxplayers=int(self.bot.getConfig("maxPlayer","12","NIP",None,None)) #Todo assert
	    
	    #self.hofdatafile=self.bot.getConfig("otherchannel","True","NIP",None,None) inform on other channels than active gamechannel, allow score and hof... later
	    
	    if self.dl:
	       print "NIPdebug: commandchar "+self.cchar
	       print "NIPdebug: NipDataDir "+self.nipdatadir
	       print "NIPdebug: HoFFile "+self.hofdatafile
	       print "NIPdebug: minPlayers "+str(self.minplayers)
	       print "NIPdebug: maxPlayers "+str(self.maxplayers)
	    
	def init_vars(self):
	        #self.default_nip()
		self.phase=NO_GAME
		self.players=[]
		self.gameadmin="" #needed for deciding when to start the game
		self.gamemaster="" #different for each round.
		self.gamemasterold="" #used to catch lazy user, who wants to cheat by removing and adding himself as gamemaster!
		self.gamechannel="" #this is not multichannel compatible! # now it is ;)
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.scores={} #splitted scores, would be nice to handle both in one array, just need doing the calc in "add_allscore"
		self.guessed=[] #users, which already have guessed
		self.additional_info=None
		self.aborted=0 #new just another flag (used for the GAMEADMINNOTIFIER within end_of_quiz, maybe used with several values in future, !=0 means game was aborted manually)
                self.abortcnt=0
		self.resetcnt=0 #used to punish a gamemaster who resets game to WAITING_FOR_QUESTION, and to control how often he could do that
		self.hookaction="startphase" #Todo: write timer action for it, flag is NEEDED for flow when exists
		
		#self.get_hof(hofdatafile)
		
	def init_vars_for_restart(self):
	        #self.phase=
		self.abortcnt=0 #used for Mfoo-style like Are you really sure...
		#self.resetcnt=0 we do that when we have a new gamemaster below
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.scores={}
		self.guessed=[] #users, which already have guessed
		self.additional_info=None

		#each player will be gamemaster, in order ## now cheat protected :) because remove does work everytime (add not)
		#if len(self.gamemaster) > 0:       #I tried to handle with .gamemaster=None did not succeed on the fly because .append adds ""... I told you that python sucks...
		#cheat protection
		#Todo put both in function ...
		if self.dl:
		   print "NIPdebug: Try to catch a cheater while restarting"
		if len(self.gamemasterold) > 0: #we have a cheat candidate
		   if str(self.gamemasterold) in self.players: # and he is back in same round, so 
		         self.bot.sendmsg(self.gamechannel,NIPPREFIX+PRE_P+self.gamemasterold+" Du versuchst zu "+BOLD+"mogeln"+BOLD+"? 2 Punkte Abzug und gleich nochmal der "+TGAMEMASTER) #to bechanged
			 #todo really -x points?
			 self.add_allscore(str(self.gamemasterold),-2)
			 self.gamemaster=self.gamemasterold
			 #self.gamemasterold=""
                   else:
		      self.gamemasterold="" #did not rejoin the game....	        
		#if len(self.gamemasterold) == 0: #change only if 
		if len(self.gamemasterold) == 0:
		   #changing gamemaster if no cheater
		   if len(self.gamemaster) > 0:
		      self.players.append(self.gamemaster) #puts him back to the end # they cannot!
		      		
		   self.gamemaster=self.players[0] #sets the next
		   self.players=self.players[1:]   #
		   self.gamemasterold=""
		   self.resetcnt=0
		   if self.dl:
		      print "NIPdebug: Setting new Gamemaster to: "+self.gamemaster
		self.gamemasterold=="" #to be sure , could be counter -2 -1 0
	#############################################   NEW workaround and solution for callLater and other new stuff
        def nTimerhook(self):
	        #concluding note, *this* seems to be thread-safe!
		self.gl_ts-=self.polltime #somewhat funny  -=
		#### I've to build my own switch/case? tz ...
		if self.gl_ts <= 0:
		   #try:
		   if self.nHack.running:
		      try:
		       self.nHack.stop() #stops twisted.internet.task.LoopingCall...., well at this point twisted throws error messages, did not follow yet
		      except:
		       if self.dl:
		          print "NIPdebug: Timer should be stopped, but isn't"

		   if self.hookaction=="end_of_quiz": #hmm, exec() might be a security threat... so let' if it, if you are sure use exec() for hookaction
		           if self.dl:
			      print "NIPdebug: hookaction reached "+str(self.hookaction)
		           self.hookaction="None"
		           self.end_of_quiz()
		   
		   elif self.hookaction=="end_of_answertime":
		           if self.dl:
			      print "NIPdebug: hookaction reached "+str(self.hookaction)
		           self.hookaction="None"
		           self.end_of_answertime()
			   
		   elif self.hookaction=="notify_gameadmin":
		           if self.dl:
			      print "NIPdebug: hookaction reached "+str(self.hookaction)
		           self.hookaction="None"
		           self.notify_gameadmin()
		
		   elif self.hookaction=="kick_gameadmin":
		           if self.dl:
			      print "NIPdebug: hookaction reached "+str(self.hookaction)
		           self.hookaction="None"
		           self.kick_gameadmin()
		   
		   elif self.hookaction=="startphase":
		           if self.dl:
			      print "NIPdebug: hookaction reached "+str(self.hookaction)
		           self.hookaction="None" #
		           self.show_players()
		           #None as Nullpointer would be nice means additional code.... so string
		
		#Good place for debugging stuff at this point, but vvvvvvery verbose - do not want to spam the logs.... [nil] (not in list) so add yours
		if self.dl > 50:
		   tstatus=str(self.nHack.running)
	           print "NIPdebug: Timer running:"+tstatus+" gl_ts=" +str(self.gl_ts)+"  Gamephase="+str(self.phase)+" hookaction="+str(self.hookaction)+" [NIL]"
		
	def nT_init(self):
	        self.nHack=hack.LoopingCall(self.nTimerhook) #this is the workaround, do not delete object until you have an own init when timer is used
			
	def nTimerset(self, REQ_TIME, REQ_ACTION):
	        #try:
		if self.nHack.running:
	                self.nHack.stop()
		self.timerinfo=REQ_TIME/self.gamespeed
		
		self.hookaction=REQ_ACTION
		self.gl_ts=REQ_TIME/self.gamespeed
		self.nHack.start(self.polltime)
		if self.dl:
		   print "NIPdebug: Starting Timer: polltime=" +str(self.polltime)+" REQ_ACTION:"+str(self.hookaction)+" REQTIME:"+str(self.gl_ts)
		   
	#Floodprotection
	def fp_init(self):	
	    if self.dl:
	       print "\nNIPdebug: Floodprotection init"
	    self.fp=hack.LoopingCall(self.fp_hook) #hmm, another instance does not hurt RAM is cheap ;)
	    self.fpsent=0
	    #what is needed to floodprotect any command?
	    #1 an always running instance of something like this polltime 1sec
	    #2 a timestamp %s
	    #3 a list with commands to protect and a timestamp
	    #4 something for the bot itself?
	    
	def fp_hook(self):
	    self.fp_ts-=(self.polltime+2)
	    if self.fp_ts <= 0:
	       if self.fp.running:
	               self.fp.stop()
		       if self.dl:
		          print "NIPdebug: FP Timer stopped, okay"
	       #hook
	       self.is_fp=0
	       self.fpsent=0
	    if self.dl>50:
	       print "Floodprotection hook "+str(self.fp_ts)
	       
	def set_fp(self, REQ_FP_TIME):
	    self.fp_ts=REQ_FP_TIME
	    if self.fp.running:
	           self.fp.stop()
		   if self.dl:
		      print "NIPdebug: FP Timer stopped, okay"
            self.is_fp=1
	    self.fp.start(self.polltime+2) # no need for accuracy
	    if self.dl:
	       print "NIPdebug: Setting FP to "+str(REQ_FP_TIME)+" sec"
	
	def nip_fp_msg(self,cchannel):
	    if self.dl:
	       print "NIPdebug: Send in Flood-Message" 
	    #we have the gamechannel after we joined now
	    if not self.fpsent:
	       self.bot.sendmsg(cchannel, NIPPREFIX+PRE_H+DGREY+"Das geht erst wieder in "+str(self.fp_ts)+" Sek.")
	       self.fpsent=1
	##########################################################
	
	
	def notify_gameadmin(self):
	        if self.gameadmin!="":
	               self.nTimerset(GAMEADMINKICK, "kick_gameadmin")
	               self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+TGAMEADMIN+" "+str(self.gameadmin)+" "+cchar+"restartgame",self.bot.getConfig("encoding", "UTF-8"))
		else:  
		       self.show_players()
		       self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+"Weiter geht's mit "+BOLD+cchar+"restartgame "+BOLD)
		       self.phase=GAME_WAITING  
		       
        def kick_gameadmin(self):
	        if self.gameadmin!="":
	               atext=""
	               #if str(self.gameadmin) in self.players: 
		       if str(self.gameadmin) in self.players or str(self.gameadmin)==self.gamemaster: #removing from all
		              #Gameadmin also removed from players"
		              self.del_player(str(self.gameadmin))
		              atext="Spielt nicht mehr mit."
		       
	               self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+TGAMEADMIN+" "+UNDERLINE+str(self.gameadmin)+UNDERLINE+" wurde des Amtes enthoben."+atext+" "+BOLD+cchar+"restartgame"+BOLD)
                       self.gameadmin=""
		else:  
		       self.show_players()
		       self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+"Weiter geht's mit "+BOLD+cchar+"restartgame "+BOLD)
		       
		self.phase=GAME_WAITING
		       
		
	def stop_timer(self):
	        if self.nHack.running:
		   self.nHack.stop()
		   #print "Timer stopped"
		if self.nHack.running:
		   print "Timer stopped but running, Must not happen" #this happend once, cannot reproduce
		#for some conditions we need 0 for status info, does not hurt to do so in everycase
		self.gl_ts=0   	
		
	def add_player(self, addnick):
	    #important TODO: catch nicks with "=" and longer than (maybe) 12 chars, and ... not wanted in game.... "=" is used as separator in hof...
	    addnick=addnick[:12] #
	    if addnick in self.players:
	       return 0
	    else:
	       if self.check_maxplayer():
	          if addnick!=self.gamemaster:
	             self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+addnick+" ist jetzt Mitspieler.")
	             self.players.append(addnick)
	          return 1
	       
	      
	       
	def del_player(self, delnick):
	    #cheatprotection
	    if self.phase==WAITING_FOR_QUESTION or self.phase==WAITING_FOR_QUIZMASTER_ANSWER:
	       if delnick==str(self.gamemaster):
	          #print "setting gamemasterold to:"+delnick
	          self.gamemasterold=delnick
	    #/
	    #del_player rest
	    c=0
	    if delnick in self.players:
	       c=1
	       self.players.remove(delnick)
               	    
	    if self.gameadmin==delnick:
	       self.gameadmin=""

	    if self.gamemaster==delnick:
	       c=1
	       self.gamemaster=""
	       self.nTimerset(5,"notify_gameadmin") #just to shorten wait time 
	    
	    if c:
	       self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+delnick+" ist jetzt kein Mitspieler mehr.")
	       
	       
	def show_players(self):
	    #Todo, .maxplayer (addplayer)
	    pnr=len(self.players)
	    if pnr > -1: # if this "if" does not fail, remove THIS if :)
		   pnr=0
		   splayers=""
		   for tplayer in self.players:
		       if tplayer==self.gameadmin:
		          tplayer=UNDERLINE+BOLD+tplayer+BOLD+UNDERLINE
		       if tplayer!=self.gamemaster:
		          splayers=splayers+" "+tplayer
		       pnr+=1
		   if self.gamemaster:
		       splayers=splayers+" "+BOLD+self.gamemaster+BOLD
		       pnr+=1
	           #self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_N+str(pnr)+" Teilnehmer: "+string.join(self.tmpplayers, " ")+" "+BOLD+addmaster+BOLD+" "+UNDERLINE+GAMEADMIN+UNDERLINE)
	           self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_G+str(pnr)+" Teilnehmer:"+splayers)
	    
	def new_gameadmin(self, gnick):
	    if GAMEADMINNOTIFY > 0:
	        self.nTimerset(GAMEADMINNOTIFY,"notify_gameadmin")
	    self.gameadmin=gnick    
	    self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+"Der neue "+TGAMEADMIN+" ist "+BOLD+gnick+BOLD)
	
	def player_qty(self):
	    plc=len(self.players)
	    if self.gamemaster:
	       plc+=1
	    return plc    
	
	def check_maxplayer(self):
	    if self.player_qty() >= self.maxplayers:
	       self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+"Die Runde ist voll. Maximal "+str(self.maxplayers)+" koennen mitspielen.")
	       if self.dl:
	          print "MaxPlayer "+str(self.maxplayers)
	       return 0
            else:
	       return 1
	#############################################  /NEW	
	def end_of_answertime(self):
		if self.nHack.running:
		   self.nHack.stop() #should be obsolete

		self.phase=QUIZ
		count=1
		qw="Die Frage war: "
		if self.gamemaster:
		   qw=self.gamemaster+" fragte: "
		self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_Q+qw+BOLD+self.question+BOLD, self.bot.getConfig("encoding", "UTF-8"))
		#self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_N+"Die Frage war: "+self.question)
		
		self.nTimerset(QUIZ_TIME, "end_of_quiz") #needs to be here due to timer calculations
		self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_C+UNDERLINE+"Moegliche "+BOLD+"Antworten"+BOLD+" sind:"+UNDERLINE+"  ~"+str(self.timerinfo)+" Sek. Zeit!"+DGREY+"  (nur die Zahl als Antwort)"+NORM, self.bot.getConfig("encoding", "UTF-8"))
		
		users=self.answers.keys()
		random.shuffle(users)
		for user in users:
			self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_C+BOLD+str(count)+BOLD+". "+self.answers[user], self.bot.getConfig("encoding", "UTF-8"))
			self.answeruser[count]=user
			#count=count+1
			count+=1
		#self.timer=self.bot.scheduler.callLater(QUIZ_TIME, self.end_of_quiz)
                #self.nTimerset(QUIZ_TIME, "end_of_quiz")
		
		
		
        def add_allscore(self, player, qty):
	    if self.dl:
	       print "add_allscore qty="+str(qty)
	    #just send negative values for qty if you wanna to "punish" a player
	    # if qty is 0 self.score[user] will be used to calc gameround points
	    if not qty == 0: #todo assert?
	       if str(player) in self.allscore.keys():
	          self.allscore[player]+=qty
	       else:
	          self.allscore[player]=qty
	    else: #round "allscore" calculation was in eoq 
	       if str(player) in self.answeruser.values(): #we are evil at THIS point - no point for no given answer
		  if player in self.allscore.keys():
		     self.allscore[player]+=self.score[player]
		  else:
		     self.allscore[player]=self.score[player]
	    
	def end_of_quiz(self):
		self.phase=GAME_WAITING
		#if self.timer and self.timer.active():
		#	self.timer.cancel()
		#new timer stopps itself
		#show who gave which answer
		snum=0
		firsttext=NIPPREFIX+PRE_C+"" #
		text=""
		#build the output array here for 'from who'
		for num in self.answeruser:
			if self.answeruser[num]==self.gamemaster:
				snum=num #stored for later use 
				#text+="**"+BOLD+str(num)+BOLD+"**"+BOLD+DGREY+"->"+NORM+"("+self.answeruser[num]+")"+", "
				firsttext+="("+self.answeruser[num]+" "+NORM+"**"+BOLD+str(num)+BOLD+"**)"+NORM+", "
				
			else:
				#text+=str(num)+DGREY+"->"+NORM+"("+self.answeruser[num]+")"+", "
				text+=DGREY+"("+self.answeruser[num]+" "+NORM+str(num)+")"+NORM+", "
				
		        text=text[:-2]+" "
			#Points. build msg todo put in function
		fromwho=firsttext+text	
		if len(self.score):
			for player in self.score:
			        pword="Punkte"
			        pscore=self.score[player]
				pscores="" #splittet show only if more than one point
				if pscore >= 9:#
				   pscore+=2 #Extra points for "three in a row"
				   if self.dl:
				      print "NIPdebug: Three in a row for "+player
				   self.score[player]+=2
				   self.scores[player]+=RED+" +2* Bonus"+DGREY
				if pscore==1:
				      pword=MAGENTA+"*"+NORM+"chen" # yet another gimmick
				else: 
				      if self.splitpoints: #show only if wanted scoreS(splitted) not score ;)
				         pscores=DGREY+"("+self.scores[player]+")"+NORM #maybe good to use in add_allscore with eval() - later
				      
				if str(player) in self.answeruser.values(): #we are !evil, no points for no given nip answer but guessing ;)
				   self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_S+player+" bekommt "+BOLD+str(pscore)+BOLD+NORM+" "+pword+" "+pscores, self.bot.getConfig("encoding", "UTF-8"))
				else:
				   self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_P+player+UNDERLINE+" bekaeme "+UNDERLINE+BOLD+str(pscore)+BOLD+NORM+" "+pword+DGREY+" (Keine moegl. Antwort geliefert, keine Puenktchen!)"+NORM, self.bot.getConfig("encoding", "UTF-8")) 
				
			#set in allscore
			for user in self.score:
			        self.add_allscore(user, 0) # works! .... so one function for "player punishment", too)
				#if str(user) in self.answeruser.values():
				#      if user in self.allscore.keys(): #todo use add_points
				#	self.allscore[user]+=self.score[user]
				#      else:
				#	self.allscore[user]=self.score[user]
	        
		#new stuff autoremove, and outputs
		# Throw results
		atext=""
		self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+UNDERLINE+"_-="+BOLD+"Ende der Runde"+BOLD+"=-_"+UNDERLINE)
		if snum > 0: #0=no answer from gamemaster
		   correct=NIPPREFIX+PRE_A+"Richtige Antwort: "+BOLD+str(snum)+BOLD+" ("+DGREY+self.answers[self.gamemaster]
  		   if self.additional_info:
		     correct=correct+NORM+" Tip:"+DGREY+self.additional_info+NORM+")"
		   else:
		     correct=correct+NORM+")"
	           self.bot.sendmsg(self.gamechannel, correct, self.bot.getConfig("encoding", "UTF-8")) 
		   self.bot.sendmsg(self.gamechannel, fromwho, self.bot.getConfig("encoding", "UTF-8")) #From who
		else: #no answ from gamemaster (maybe he has sent in a question)
		   rtext="" #
		   ptext="" #
		   #atext="" #
		   #if self.gamemaster: #not needed?
		   if self.gamemaster==self.gameadmin:
		      if self.autoremove:
			        self.kick_gameadmin() #both ;)
				self.gamemaster="" #not really needed done in kickadmin
				atext=" Zum weiterspielen "+BOLD+cchar+"join"+BOLD
		   else:
		      if self.autoremove:
		                self.gamemasterold=self.gamemaster #for cheatprotection, if player joins again for next round -2 points...
				gmaster=self.gamemaster
				self.del_player(self.gamemaster)
				self.gamemaster="" 
				atext=" Zum weiterspielen "+BOLD+cchar+"join"+BOLD
		   #   if self.autoremove:
		   #        atext=BOLD+cchar+"add"+BOLD+" um weiterzuspielen!"
		   #self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_N+"del?"+ptext+BOLD+gmaster+BOLD+" hatte keine Frage."+rtext, self.bot.getConfig("encoding", "UTF-8")) 
		   gmaster=""
		   if self.gamemasterold:
		       gmaster=" "+self.gamemasterold
		   if self.gamemaster:
		       gmaster=" "+self.gamemaster
		   self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_X+TGAMEMASTER+gmaster+" hatte keine Frage."+atext, self.bot.getConfig("encoding", "UTF-8")) 
		      
		#last but not least
		if GAMEADMINNOTIFY > 0 and self.aborted < 1:
		   self.nTimerset(GAMEADMINNOTIFY, "notify_gameadmin")
		#print "End_of_quiz end"      
	
		
	def init_autocmd(self):
	    #next step, get these from source ...and add from config or similar
	    #knowncommands
	    #you have to make every command used in game an "knowncommand" if you use auto_command.... even those for replace_command
	    self.kcs=["halloffame","hof","splitpoints","abortgame","resetgame","end","add", "remove", "startgame", "restartgame", "kill", "scores", "gamespeed", "autoremove", "stats", "players","rules","rulez","status","niphelp","join","part","help","autostart","testing","allo","cato","netear","wete","p_kater"]
	    #for knowncmd in self.knowncmds:
	    #    self.kc[knowncmd:1
	    
	def auto_command(self, cmd):
	    # not stress-tested so far, and maybe something for the bot itself
	    # extracts given usercmd to a given command, not case-sensitive so far, so user(player) may say !AborT and we'll realise
	    ## Todo: for hundreds of commands i suggest to build another list/hash from first char of given command
	    ## this is quick and dirty just to play around with python 
	    ## Todo try to put the hit on the first unique cmd in kcd
	    i=0
	    a=0
	    it=""
	    if cmd in self.kcs:
	       it=cmd
	    else:
	     while ( a < len(self.kcs)):
	         kc=self.kcs[a]        #would be nice to have a sorted list key first char... later
	         a+=1
		 if kc[:len(cmd)]==string.lower(cmd):
		   hit=kc
		   i+=1
		   if i >=2:
		     break
	    if i == 1:
	     it=hit	 
            return it        		

		
	def suggesst_command(self, cmd):
	    #just an idea, notice user googlelike "Did you mean..."
	    pass
	    	
        def replace_command(self, cmd):	    #maybe useful
	    if cmd=="end":
	       cmd="abortgame"
	    if cmd=="join":
	       cmd="add"
	    if cmd=="hof":
	       cmd="halloffame"  
	    if cmd=="part":
	       cmd="remove"
	    #some temp gimmicks
	    if cmd=="p_kater":
	       cmd="rules"
	    if cmd=="netear":
	       #no channel no output ;) - todo at all
	       try:
	           self.bot.sendmsg(self.gamechannel,NIPPREFIX+PRE_X+"Meinten sie: !rUlEs ?")
	       except:
	           pass
	       cmd="rules"   
	       
	    
	    return cmd	
	
	def check_channel(self, cchannel, ccommand):
	    #how to check another netinstance? so we could "invite" players from other nets
	    if self.dl:
	       print "NIPdebug: check "+cchannel+" vs "+self.gamechannel
	    if cchannel not in self.channels:
	       if self.dl:
	          print "NIPdebug: Not in channellist "+cchannel
	       return 0
	    if ccommand=="halloffame" or ccommand=="scores": #cmd for every channel
	       return 1
	    if not self.gamechannel:
	       return 1
	    elif self.gamechannel==cchannel:
	       return 1
	    elif self.gamechannel!=cchannel:
	       if ccommand=="startgame":
	          self.bot.sendmsg(cchannel, "Es wird bereits gespielt! "+BOLD+"/join "+self.gamechannel+BOLD)
	       return 0

	def command(self, user, channel, command, options):
	        if self.check_channel(channel, command): #try this here (is confed gamechannel or a command for all channels)
		   command=self.auto_command(command) #so the user may cut the commands 
		   command=self.replace_command(command) #so we could use synonyms
		   user=string.lower(user.split("!")[0])
		   if channel!=self.bot.nickname: #no query
		   #if self.check_channel(channel, command):
			if command=="kill":
				if self.gameadmin==user and self.phase!=WAITING_FOR_PLAYERS: 
				        self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Ooops!"+TGAMEADMIN+" "+self.gameadmin+" hat wohl keine Lust mehr...")
					self.del_player(user)
					self.gameadmin=""
				else: 
                                        if self.gameadmin==user:
				                self.bot.sendmsg(channel, NIPPREFIX+PRE_X+TGAMEADMIN+" "+self.gameadmin+" das geht erst nach "+cchar+"startgame oder "+cchar+"abortgame")

                        elif command=="niphelp":
			        self.bot.sendmsg(channel,NIPPREFIX+PRE_H+HELPBUG)
			        if not self.phase==NO_GAME:
			           if options[:3].strip()=="all":
 			              self.bot.sendmsg(channel, NIPPREFIX+PRE_H+HELPUSER)
				      self.bot.sendmsg(channel, NIPPREFIX+PRE_H+HELPADMIN)
				   else:
				      if self.gameadmin==user:
				         self.bot.sendmsg(channel,NIPPREFIX+PRE_H+TGAMEADMIN+" "+HELPADMIN)
                                      else:	
				         self.bot.sendmsg(channel,NIPPREFIX+PRE_H+HELPUSER)
				else:
				   self.bot.sendmsg(channel,NIPPREFIX+PRE_H+cchar+"startgame. Waehrend des Spiels "+cchar+"niphelp <all> oder "+cchar+"rules")
			#######new
			elif command=="autoremove":
                                if user==self.gameadmin:
				   if self.autoremove==0:
				           self.autoremove=1
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autoremove"+BOLD+" ist nun"+BOLD+" aktiv"+BOLD+", NIP-Fragesteller ohne Aktion werden automatisch aus dem Spiel entfernt")
			           else:
				           self.autoremove=0
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autoremove"+BOLD+" ist nun"+BOLD+" inaktiv."+BOLD)
			        else:
				 addword="inaktiv"
				 if self.autoremove==1:
				  addword="aktiv"
				 self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autoremove"+BOLD+" ist "+BOLD+addword+BOLD+". Wechsel nur durch den "+TGAMEADMIN+" moeglich!")
			
			elif command=="autostart":
                                if user==self.gameadmin:
				   if self.autostart==0:
				           self.autostart=1
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autostart"+BOLD+" ist nun"+BOLD+" aktiv"+BOLD+", Ich starte/restarte automatisch neue Runden nach ~"+str(STARTPHASE)+"Sekunden")
			           else:
				           self.autostart=0
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autostart"+BOLD+" ist nun"+BOLD+" inaktiv."+BOLD)
			        else:
				 addword="inaktiv"
				 if self.autostart==1:
				  addword="aktiv"
				 self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"Autostart"+BOLD+" ist "+BOLD+addword+BOLD+". Wechsel nur durch den "+TGAMEADMIN+" moeglich!")
			
			elif command=="splitpoints":
                                if user==self.gameadmin:
				   if self.splitpoints==0:
				           self.splitpoints=1
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"splitpoints"+BOLD+" ist nun"+BOLD+" aktiv"+BOLD+", ich zeige die genaue Punkteverteilung")
			           else:
				           self.splitpoints=0
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"splitpoints"+BOLD+" ist nun"+BOLD+" inaktiv,"+BOLD+" ich zeige nur die Gesamtpunktzahl")
			        else:
				 addword="inaktiv"
				 if self.splitpoints==1:
				  addword="aktiv"
				 self.bot.sendmsg(channel, NIPPREFIX+PRE_X+BOLD+"splitpoints"+BOLD+" ist "+BOLD+addword+BOLD+". Wechsel nur durch den "+TGAMEADMIN+" moeglich!")
			
			elif command=="gamespeed":
                                if user==self.gameadmin:
				   if self.gamespeed==1:
				           self.gamespeed=2
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Spielgeschwindigkeit ist nun "+BOLD+"schnell")
			           else:
				           self.gamespeed=1
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Spielegeschwindigkeit ist nun "+BOLD+"normal")
			        else:
				 actspeed="normal"
				 if self.gamespeed==2:
				  actspeed="schnell"
				 self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Spielgeschwindigkeit ist "+BOLD+actspeed+BOLD+". Wechsel nur durch den "+TGAMEADMIN+" moeglich!")
				 
			elif command=="testing":
				#self.nip_hof_update(self.nipdatadir+self.hofdatafile)
				if user==self.gameadmin:  
				   if self.minplayersold == 0:
				           self.minplayersold=self.minplayers
					   self.maxplayersold=self.maxplayers
				           self.minplayers=3 # default in config will be 5 
					   self.maxplayers=24 #default in config will be 12
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Minimum Spieler="+BOLD+str(self.minplayers)+BOLD+" Maximum Spieler="+BOLD+str(self.maxplayers))
			           else:
				           self.minplayers=self.minplayersold
					   self.maxplayers=self.maxplayersold
					   self.minplayersold=0
					   self.maxplayersold=0
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Minimum Spieler="+BOLD+str(self.minplayers)+BOLD+" Maximum Spieler="+BOLD+str(self.maxplayers))
			        else:
				 self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"You have found a secret :)")
				 
			########/new       
			elif command=="add":
			        if self.dl:
				   print "NIPdebug: Called add in phase "+str(self.phase)
			        if self.phase==NO_GAME or self.phase==GAME_WAITING: #should work now
				#if self.phase==GAME_WAITING:
				
				        if self.gameadmin: #we have one ;)
					   if user==self.gameadmin: #himself
					           if len(options) > 1:
						      player=string.lower(options[:12].strip()) #Todo regexp or validation with channeluserlist
						      # TODO
						      # need channeluserlist here to validate if user exists, 
						      self.add_player(player)
						   else:
						      self.add_player(user) #just add himself
					   else:   
						   self.add_player(user) # just a player 
				        else:
 					    self.add_player(user) # again maybe we have no admin
				else:
				        self.bot.sendmsg(channel, NIPPREFIX+PRE_X+user+": Hinzufuegen geht nur in Rundenpausen oder am Anfang mit \"ich\"")
					
			elif command=="remove":
			        #if self.phase==NO_GAME or self.phase==GAME_WAITING: #Todo removing alltime
				if self.phase!=7: #try if compatible with flow (Todo)
				
				        if self.gameadmin: #we have one ;)
					   if user==self.gameadmin: #himself
					           if len(options) > 1:
						      player=string.lower(options[:24].strip()) #truncated and the trailing spaces eliminated 
						      self.del_player(player) #admin removes player
						   else:
						      self.del_player(user) #just remove himself 
					   else:
						   self.del_player(user) # just a player
					else:
					   self.del_player(user) # again even if there is no admin
				else:
					self.bot.sendmsg(channel, NIPPREFIX+PRE_X+user+": Aussteigen geht nur zwischen den Runden.")
					
							   	      
			elif command=="players":
				#if self.phase==NO_GAME:
                                #self.bot.sendmsg(channel, NIPPREFIX+PRE_N+string.join(self.players, " ")) # trunc this list if sendmsg doesn't
				self.show_players()

			elif command=="restartgame":
			        if self.gameadmin=="" and self.phase==GAME_WAITING:
				        self.new_gameadmin(user)
				        #self.gameadmin=user
					#self.bot.sendmsg(channel, NIPPREFIX+PRE_N+"Der neue "+TGAMEADMIN+" ist "+BOLD+self.gameadmin)
				if self.gameadmin==user and self.phase<2: #test
				   self.stop_timer() #needed here due to kick_gameadmin?
				   #print "restart stopped timer...okay here? perhaps after check of we could start?" #todo
				#if self.phase==NO_GAME and user==self.gameadmin:
				if self.phase==GAME_WAITING and user==self.gameadmin:

				        if self.player_qty() >= self.minplayers:
					
					   #Important todo, trunc list(for irc) AND we need .maxplayers and 
					   tmpplayers=string.join(self.players," ") # trunc this? or predone?
					   if self.gamemaster:
					      tmpplayers=self.gamemaster+" "+tmpplayers
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_G+"Neue Runde mit: "+tmpplayers)
					   self.init_vars_for_restart()
					   self.phase=WAITING_FOR_QUESTION
					   #self.bot.sendmsg(channel, user+": /msg mir die Frage.", self.bot.getConfig("encoding", "UTF-8"))
					   self.nTimerset(TIMEOUT, "end_of_quiz")
					   self.bot.sendmsg(channel, NIPPREFIX+PRE_Q+str(self.gamemaster)+": Schick' mir die "+TNIPQUESTION+"."+"  ~"+str(self.timerinfo)+" Sek. Zeit!"+DGREY+" (/msg "+self.bot.nickname+" die Frage)", self.bot.getConfig("encoding", "UTF-8")) #guess gamemaster might work in all cases instead of user here ;)
					   self.bot.sendmsg(self.gamemaster,"Du kannst im "+self.gamechannel+" !resetgame machen, falls du dich vertippt hast, Und nun die NIP-Frage:")
					   
					else:
					   self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_G+"Zu wenig Spieler. Mindestens "+str(self.minplayers)+" muessen mitspielen! "+BOLD+cchar+"join"+BOLD)

			elif command=="startgame":
			        
			        ##### if not self.gamechannel (see check_channel)means there is no game on network! # did not test behavior on networks!
			        if self.phase==NO_GAME:
					self.init_vars()
					self.gameadmin=user
					if len(self.allscore) > 0:
					     self.allscore={}
					     self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Spielstand geloescht!")
					self.bot.sendmsg(channel, NIPPREFIX+PRE_X+user+": Du bist nun der "+TGAMEADMIN+" - Los geht's mit "+cchar+"startgame." ,self.bot.getConfig("encoding","UTF-8"))
				        self.bot.sendmsg(channel, NIPPREFIX+PRE_X+"Wer moechte an einer Runde "+self.nameofgame+" teilnehmen? (\"\x02ich\x02\" rufen!)",self.bot.getConfig("encoding","UTF-8"))
				
					self.phase=WAITING_FOR_PLAYERS
					
				        self.gamechannel=channel #needed for queries which result in a public answer | we set the .gamechannel on "start" and reset it at abort(end game)
					#self.nTimerset(TIMEOUT, "end_of_quiz") #includes starting timer, we dont need here....
					self.nTimerset(240,"kick_gameadmin") #not the "Bigloop" yet, maybe we just need another long timeout for an "abort_game" function....
					
				elif self.phase==WAITING_FOR_PLAYERS and user==self.gameadmin:
					if self.player_qty() >= self.minplayers:
						self.phase=WAITING_FOR_QUESTION
						random.shuffle(self.players)
						self.gamemaster=random.choice(self.players)
						self.nTimerset(TIMEOUT, "end_of_quiz")
						self.bot.sendmsg(channel, NIPPREFIX+PRE_Q+self.gamemaster+": Schick' mir die "+TNIPQUESTION+"."+" ~"+str(self.timerinfo)+" Sek. Zeit!"+DGREY+" (/msg "+self.bot.nickname+" die Frage)", self.bot.getConfig("encoding", "UTF-8"))
						self.bot.sendmsg(self.gamemaster, "Du kannst im "+self.gamechannel+" !resetgame machen, falls du dich vertippt hast. Und nun die NIP-Frage")
						#self.nTimerset(TIMEOUT, "end_of_quiz") #obsolete
						
					else:
						self.bot.sendmsg(channel, NIPPREFIX+PRE_X+self.gameadmin+": zuwenig Mitspieler! Mindestens "+str(self.minplayers)+" muessen mitspielen. "+BOLD+"\"ich\""+BOLD+" rufen!", self.bot.getConfig("encoding", "UTF-8"))
			        
				elif self.gameadmin=="": #Todo? Does this work? #Looks nice
				     self.new_gameadmin(user)
				             
			elif command=="abortgame": #now "end of game"
			        if self.gameadmin=="" and self.phase!=NO_GAME:
				        self.new_gameadmin(user)
					
			        if self.gameadmin==user and self.phase>0:
				        if self.abortcnt < 1:
				                self.bot.sendmsg(channel,NIPPREFIX+PRE_X+self.gameadmin+": Um das Spiel tatsaechlich zu beenden, bitte noch einmal!")
					        self.abortcnt=1
					else:					       
					        
					        
					        self.stop_timer()
						#self.init_vars_for_restart()
						self.phase=NO_GAME
						self.gameadmin=""
						self.gamemaster=""
						self.aborted=1
						self.gamechannel="" #so we could start in any other channel on network
						self.nip_hof_update(self.nipdatadir+self.hofdatafile) #seems to work, test it
						self.bot.sendmsg(channel, NIPPREFIX+PRE_S+"Hall of Fame ist auf den neusten Stand gebracht.")
						self.bot.sendmsg(self.gamechannel,NIPPREFIX+PRE_X+"Spiel beendet, "+cchar+"startgame startet ein Neues.")
						self.players={} #allscores deletion in init, Todo "Hall of Fame", first store points from game?
						
						self.hookaction="startphase" #will be set for timerhook later, but flag NEEDED from now
			        else:
				        
                                        self.bot.sendmsg(channel,NIPPREFIX+PRE_X+"Abbruch nur durch den "+TGAMEADMIN+" "+self.gameadmin+" moeglich!")
			
			elif command=="resetgame":
			        #print "resetgame "+str(self.phase)
			        if self.phase==WAITING_FOR_QUIZMASTER_ANSWER or self.phase==WAITING_FOR_ANSWERS:
				   if self.gameadmin==user or self.gamemaster==user:
				      self.resetcnt+=1 #todo block more than x resets....
				      ppoints=self.resetcnt * 2
				      if self.resetcnt>1:
                                         self.bot.sendmsg(channel,NIPPREFIX+PRE_H+user+": Auf ein Neues! "+BOLD+"Punktabzug: -"+str(ppoints))
					 self.bot.sendmsg(self.gamemaster,"Deine NIP-Frage:")
					 self.add_allscore(user,int(ppoints*-1))
					 self.reset_game()
				      else:
				         ppoints=1
				         self.bot.sendmsg(channel, NIPPREFIX+PRE_H+user+": Auf ein neues! "+BOLD+"Naechstemal Punktabzug!")
					 self.bot.sendmsg(self.gamemaster,"Deine NIP-Frage:")
					 #self.add_allscore(user, -1)
				         self.reset_game()
				   else:
				      self.bot.sendmsg(channel,NIPPREFIX+PRE_H+"NOP")
				else:
				   self.bot.sendmsg(channel, NIPPREFIX+PRE_H+"NOP")
				
			elif command=="scores":
			        if not self.is_fp:
				   self.set_fp(self.fp_time)
				   pointlen=0
				   if len(self.allscore):
				      pointlen=len(str(max(self.allscore.values())))
				   SCOREHEAD="_-=Punkteverteilung=-"+self.create_ws(pointlen-1)+"_"
				   self.bot.sendmsg(channel, NIPPREFIX+PRE_S+UNDERLINE+SCOREHEAD+UNDERLINE, self.bot.getConfig("encoding", "UTF-8"))
				   if len(self.allscore):	
					points=self.allscore.values()
					print str(pointlen)
					points.sort()
					points.reverse()
					players=self.allscore.keys()
					for point in points:
						for player in players:
							if self.allscore[player]==point:
							        pword="Punkte"
								if point==1:
								   pword="Punkt"
								splayer=player+self.create_ws(12)
								#spoints=str(point)+self.create_ws(12+len(str(point)))[:pointlen]
								spoints=str(point)+self.create_ws(pointlen-len(str(point)))
								self.bot.sendmsg(channel, NIPPREFIX+PRE_S+splayer[:12]+"  "+spoints+ " "+pword, self.bot.getConfig("encoding", "UTF-8"))
								players.remove(player)
								break;
				else:
				   self.nip_fp_msg(channel)
			elif command=="halloffame":
			        
			        if not len(options):
				   pointlen=len(str(self.hof[0][1])) # for building the length in formatted output
				   expand=""
				   if pointlen>3:
				      expand=self.create_ws(pointlen-3) #three is default
				   HOFHEAD="_-= Hall of Fame =-"+expand+"_"
				   self.bot.sendmsg(channel, NIPPREFIX+PRE_Z+UNDERLINE+HOFHEAD+UNDERLINE, self.bot.getConfig("encoding", "UTF-8"))
				   if len(self.hof):	
				      pcnt=0
				      if not self.is_fp:
				          self.set_fp(self.fp_time)
				          for player, allpoints in self.hof:
				              pcnt+=1
				              nick=player+"            " # (max nick length) how to create an own tab oO
				              place=str(pcnt)+".     "   # Puenkti was here! Todo create_ws() for that
				              self.bot.sendmsg(channel, NIPPREFIX+PRE_Z+place[:3]+" "+nick[:12]+" "+str(allpoints), self.bot.getConfig("encoding", "UTF-8"))
                                              if pcnt >= self.hof_show_max_player: 
				                 break
				      else:
				          self.nip_fp_msg(channel)
				else:
				   player=string.lower(options[:12].strip())
				   isinteger=0
				   try: #I am sure there's an "is_int", but I am too lazy to search for at the moment, did not found in builtin-things, anyway... 
				     int(player) #todo assert?
				   except:
				      isinteger=1
				   if isinteger:
				       isin=self.isinhof(player)
				       if not isin:
				          self.bot.sendmsg(channel, NIPPREFIX+PRE_Z+player+" nicht in der "+BOLD+"Hall of Fame"+BOLD+" gefunden! Eine Schande!",self.bot.getConfig("encoding", "UTF-8"))
                                       else:				  
				          place=isin[0]+".    "
				          player=isin[1]+"           " #easier way to create whitespaces (and own tabs)?
				          allpoints=isin[2]
				          self.bot.sendmsg(channel, NIPPREFIX+PRE_Z+place[:3]+player[:12]+" "+str(allpoints),self.bot.getConfig("encoding", "UTF-8"))
			           else: #we got an integer, how plain! hehe
				       hplace=int(player)
				       place=str(hplace)+".            "
				       player=self.hof[hplace-1][0]+"                      "
				       allpoints=self.hof[hplace-1][1]
				       self.bot.sendmsg(channel, NIPPREFIX+PRE_Z+place[:3]+player[:12]+" "+str(allpoints),self.bot.getConfig("encoding", "UTF-8"))


								
			elif command=="rules":
			     self.bot.sendmsg(channel, NIPPREFIX+PRE_H+RULES,self.bot.getConfig("encoding", "UTF-8"))					
			
			     
			elif command=="status":
			     result=self.game_status(None)
			     self.bot.sendmsg(channel, NIPPREFIX+PRE_G+result,self.bot.getConfig("encoding", "UTF-8"))					
			     
	def create_ws(self, qty):
	    if qty<1:
	       return ""
	    ws=[]
	    for i in range(qty):
	        ws.append(' ')
	    return ''.join(ws)
	    # tried to create this in a single line
	    
	def reset_game(self):
	    #set game to status WAITING_FOR_QUESTION #used in "resetgame"
	    if self.dl:
	       print "NIPdebug: reset game in phase="+str(self.phase)
	    self.resetcnt+=1
	    #self.init_vars_for_restart() #due to cheatprotect this will be problematic at this point
	    self.question=""
	    self.answers={}
	    self.answeruser={}
	    self.additional_info=None
	    #self.score={} #not here!
	    #self.scores={} #dto
	    self.guessed=[]
	    self.nTimerset(TIMEOUT, "end_of_quiz")
	    self.phase=WAITING_FOR_QUESTION
	    if self.dl:
	       print "NIPdebug: Game resetted"
	    		     
	def userKicked(self, kickee, channel, kicker, message):
	    player=string.lower(kickee)
	    playerkicker=string.lower(kicker)
	    #remove gamemaster and or gameadmin from game if kicked, well this has to be improved... conditions are to be defined
	    if self.gamechannel==channel:
	       if self.gameadmin==player:
		  self.kick_gameadmin()
		  #player=""
	       if self.gamemaster==player:
		  self.del_player(player)
		  #well to kick the actual! gamemaster while waiting for his input is evil, and will be punished with score -3 ;)
		  if self.phase==WAITING_FOR_QUESTION or self.phase==WAITING_FOR_QUIZMASTER_ANSWER:
		     #print "Evil detected ->"+playerkicker
		     self.bot.sendmsg(channel, NIPPREFIX+PRE_P+kicker+":Den "+TGAMEMASTER+" gerade "+BOLD+"jetzt"+BOLD+" zu kicken ist boese, 3 Punkte Abzug!")
		     self.add_allscore(str(playerkicker),-3)
		  self.phase=GAME_WAITING #todo look if that works| hmm yes ist does | anyone?
	
	def joined(self, channel):
	    if self.dl:
	       print "NIPdebug: We joined channel: "+channel
	    #self.gamechannel=channel 
	    #Todo: unless we are not fit for multichannel, startgame will set/reset the channel we are playing in
	    #so check self.gamechannel on !start
	    #on join will throw this msg any channel
	    if self.check_channel(channel,None):
               self.bot.sendmsg(channel, NIPPREFIX+PRE_H+"Dave, moechtest du mit mir hier im "+channel+" spielen? !startgame")
	    		  
	    
	def userJoined(self, user, channel):
	    welcometo=user.split("!")[0]
	    luser=welcometo.lower() #*g*
	    print "Userjoined "+welcometo
	    if not luser in self.players and luser!=self.gamemaster and channel in self.channels: 
	       statusinfo=self.game_status(string.lower(welcometo))
	       if self.gamechannel==channel:
	          print "gamechannel=channel in user joined"
	          self.bot.notice(welcometo, "Hi, "+BOLD+welcometo+BOLD+"! "+statusinfo)
	       else:
	          if self.gamechannel!="":
	             self.bot.notice(welcometo, "Hi, "+BOLD+welcometo+BOLD+"! /join "+self.gamechannel+" fuer eine Runde NIP!")
	          else:
	             self.bot.notice(welcometo, "Hi, "+BOLD+welcometo+BOLD+"! "+statusinfo)
	    #print "Join Notice to "+playernick+" "+statusinfo
	       
	def game_status(self, playernick):
	    #set and return them to user just on request. notice on join, or command status (translation in mind)
	    ustat=""
	    uadd=""
	    stat=""
	    nt=""
	    ujoin=""
	    status=self.phase
	    if playernick in self.players:
	       uadd=" Du bist noch dabei."
	    if self.gamemaster==playernick:
	       uadd=" Du bist "+TGAMEMASTER
	    if self.gameadmin==playernick:   
	       uadd=" Du bist "+TGAMEADMIN
	    if self.gameadmin==playernick and self.gameadmin==playernick:   
	       uadd=" Du bist "+TGAMEADMIN+" und "+TGAMEMASTER
	    if self.gl_ts >= 1:
	       nt=DGREY+" Noch ~"+str(self.gl_ts)+" Sek."+NORM
	    else:
	       nt=DGREY+" ~~~" #no timeouts running
	    if len(uadd)==0:
	       ujoin=" Am Ende der Runde mitspielen mit "+cchar+"join."       
	    if status==NO_GAME and self.hookaction!="startphase": #Todo Maybe Another game status FIRST_START or this flag
	             stat="Es laeuft kein NIP-Spiel. "+BOLD+cchar+"startgame"+BOLD+" startet eins."
		     ustat=stat
		     stat=stat+nt # only if needed
	    
	    if status==NO_GAME and self.hookaction=="startphase" and self.abortcnt==0: #Todo condition for FIRST_START... later
	             stat="NIP-Runde laueft. Wer teilnehmen moechte einfach "+BOLD+"\"ich\""+BOLD+" rufen!"
		     ustat=stat+uadd
	             stat=stat+nt
	    if status==NO_GAME and self.hookaction=="startphase" and self.abortcnt > 0: #Todo condition for FIRST_START... later
	             stat="Das Spiel wurde beendet. "+BOLD+cchar+"startgame"+BOLD+" startet ein Neues."
		     ustat=stat
	             stat=stat+nt
	    if status==WAITING_FOR_PLAYERS:
	             stat="NIP-Runde laeuft. Wer teilnehmen moechte einfach "+BOLD+"\"ich\""+BOLD+" rufen!"
		     ustat=stat+uadd
		     stat=stat+nt
	    if status==WAITING_FOR_QUESTION or status==WAITING_FOR_QUIZMASTER_ANSWER:
	             gm=""
	             if self.gamemaster:
		        gm=BOLD+self.gamemaster+BOLD
	             stat="NIP-Runde laeuft. Wir warten auf den "+TGAMEMASTER+" "+gm
		     ustat=stat+ujoin+uadd
		     stat=stat+nt
	    if status==WAITING_FOR_ANSWERS:
	             stat="NIP-Runde laeuft. Wir warten auf die \"falschen\" Antworten."
		     ustat=stat+ujoin+uadd
		     stat=stat+nt
	    if status==QUIZ:
	             stat="NIP-Runde laeuft. QUIZ-Time! Warten auf die Punkteverteilung."
		     ustat=stat+ujoin+uadd
		     stat=stat+nt
	    if status==GAME_WAITING:
	             astat=""
	             if self.gameadmin=="":
		        astat=" "+BOLD+cchar+"restartgame sollte helfen."+BOLD
	             stat="NIP pausiert."+astat+" Mitspielen einfach mit "+BOLD+cchar+"join"+BOLD
		     ustat=stat
		     stat=stat+nt
	    rv=""
	    if playernick:
	       rv=ustat
	    else:
	       rv=stat
	    
	    return rv
	       
	
	def msg(self, user, channel, msg):
		user=string.lower(user.split("!")[0])
		if channel == self.bot.nickname:
			if self.phase==WAITING_FOR_QUESTION and user==self.gamemaster:
				#self.timer.cancel() missing Handle was the problem
				self.question=msg
				self.bot.sendmsg(user, "Und jetzt die richtige Antwort")
				self.phase=WAITING_FOR_QUIZMASTER_ANSWER
				self.nTimerset(TIMEOUT, "end_of_quiz")

			elif self.phase==WAITING_FOR_QUIZMASTER_ANSWER and user==self.gamemaster:
				#self.timer.cancel()
				self.answers[user]=msg
				self.nTimerset(ANSWER_TIME, "end_of_answertime")
				self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_Q+TNIPQUESTION+" ist: "+BOLD+self.question, self.bot.getConfig("encoding", "UTF-8"))
				#self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_N+"Die Frage ist: "+BOLD+self.question)
				
				self.bot.sendmsg(self.gamechannel, NIPPREFIX+PRE_A+"Schickt mir eure "+BOLD+"\"falschen\""+BOLD+" Antworten! ~"+str(self.timerinfo)+" Sek. Zeit!"+DGREY+"  (/msg "+self.bot.nickname+" eure Antwort)", self.bot.getConfig("encoding", "UTF-8"))
				self.phase=WAITING_FOR_ANSWERS
				#self.timer=self.bot.scheduler.callLater(ANSWER_TIME, self.end_of_answertime) #TIMEOUT

				#remove gamemaster from game, because he knows the answer
				if self.gamemaster in self.players: #sometimes he is not in before, i'd have a look at assert 
				   self.players.remove(self.gamemaster)
				
				self.bot.sendmsg(self.gamemaster, "Zusatzinformation zur Frage einfach hinterschicken oder weglassen") #does not work in all cases?
				if self.dl:
				   print "NIPdebug: Sent an additional info (tip) request."
				

			elif (self.phase==WAITING_FOR_ANSWERS or self.phase==QUIZ) and user==self.gamemaster and not self.additional_info:
				self.additional_info=msg

			elif self.phase==WAITING_FOR_ANSWERS and not user in self.answers and user in self.players:
				self.answers[user]=msg
				if len(self.answers) == len(self.players)+1: #+gamemaster
					#if self.timer and self.timer.active():
					#	self.timer.cancel()
					self.end_of_answertime()
		else:
			#if string.lower(msg)[:3]=="ich" and self.phase==WAITING_FOR_PLAYERS:
			if self.gamechannel==channel:
			 if (self.phase==WAITING_FOR_PLAYERS or self.phase==GAME_WAITING) and user!=string.lower(self.bot.nickname): #add player with "ich" in first 42characters while startphase, or if game is paused
			        if len(string.lower(msg).split("ich")[:42]) > 1: #
				   if not (user in self.players or user==self.gamemaster):
				        if self.check_maxplayer():
					   self.players.append(user[:12]) #max len of nick maybe dyn in future
					   text=""
					   for item in self.players:
						text=text+item+", "
					   text=text[:-2]+"."
					#self.bot.sendmsg(channel,NIPPREFIX+PRE_N+ str(len(self.players))+" Teilnehmer: "+text, self.bot.getConfig("encoding", "UTF-8"))
					self.show_players() #TODO, let do that in timerhook if new player joined maybe with polling time 4 seconds... for later
			 elif self.phase==QUIZ and user in self.players and not user in self.guessed and user!=self.gamemaster:
				try:
					if(self.answeruser[int(msg)]==self.gamemaster):
						if user in self.score:
							#self.score[user]=self.score[user]+1
							self.score[user]+=1 #shorter ;)
							if self.splitpoints:
							   self.scores[user]=self.scores[user]+(" +1*") #todo handle scores in one array (multi dim dict or somthing), we just need this here and could do calc in add_allscore
						else:
							self.score[user]=1
							if self.splitpoints:
							   self.scores[user]="+1*"
							   
					elif(self.answeruser[int(msg)]==user):
						#to select the own answer gives 0 points
						pass
					else:
						if(self.answeruser[int(msg)] in self.score):
							#self.score[self.answeruser[int(msg)]]=self.score[self.answeruser[int(msg)]]+3
							
							self.score[self.answeruser[int(msg)]]+=3 #shorter oO
							if self.splitpoints:
							   self.scores[self.answeruser[int(msg)]]=self.scores[self.answeruser[int(msg)]]+" 3<-"+user #
							#self.bot.sendmsg(self.gamechannel, self.answeruser[int(msg)]+" bekommt 3 Punkte", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
						else:
							self.score[self.answeruser[int(msg)]]=3
							if self.splitpoints:
							   self.scores[self.answeruser[int(msg)]]=" 3<-"+user
							#self.bot.sendmsg(self.gamechannel, self.answeruser[int(msg)]+" bekommt 3 Punkte", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
					self.guessed.append(user)
				except ValueError:
					pass
				if len(self.guessed) == len(self.players):
					self.end_of_quiz()
                #
        def nip_hof(self,hofdataf,action):
	    #todo truncate file to limit of hof_max_player after sorting....
	    if self.dl:
	           print "NIPdebug: HoF data "+action
	    if action=="read":
	       try:
	          cnt=0
	          hofFile=open(hofdataf, "r")
	          hofData=hofFile.read()
	          hofFile.close()
	          thof={}
		  hof=[]
	          for line in hofData.split("\n"): #todo trunc
	              if len(line) > 1:
		         pair=line.split("=",1)
		         thof[pair[0]]=int(pair[1])
			 hof.append("") #is there a better way to "dim" a list?
		         cnt+=1
		  pairs = sorted((key,value) for (value,key) in thof.iteritems())
		  hcnt=len(pairs)-1 
		  for value, key in pairs:
		      hof[hcnt]=key,value
		      hcnt-=1
		  if self.dl:
		     print "NIPdebug: returning from reading HoF"
	          return hof #better way to sort a list from dict?
	          print "Hof data gelesen"	  
	       
	       except IOError:
	          if self.dl:
	                 print "NIPdebug: Could not open HoF Data "+hofdataf
	          try:
	            print "NIPdebug: Creating "+hofdataf
		    if (not os.path.isdir(os.path.dirname(hofdataf))):
		        os.makedirs(os.path.dirname(hofdataf))
		    hofFile = open(hofdataf, "w")
		    hofFile.close()
		    print "NIPdebug: File created "+hofdataf
	          except IOError:
	              if self.dl:
	                 print "NIPdebug: Could not create "+hofdataf+str(IOError)
	    if self.dl:
	       print "HoF Data ready"
            if action=="write":
	       if self.dl:
	          print "Writing HOF to file "+hofdataf
	       ts=time.strftime('%Y%m%d_%S%M%H')
	       bfile=hofdataf+"."+ts
	       if self.dl:
	          print "Creating HoF backup "+bfile
	       try:
	          shutil.copyfile(hofdataf, bfile)
	       except:
	          if self.dl:
	             print "NIPdebug: Couldn't create "+bfile+" "+str(IOError)
	         
	       
	       try:
	         hofFile=open(hofdataf, "w")
	         cnt=0	  
	         for key, val in self.hof:
		     hofFile.write(str(key)+"="+str(val)+"\n")
		     cnt+=1
		     if cnt > self.hof_max_player:
		        break
			hofFile.close()
		 hofFile.close()
	       except IOerror:
	          if self.dl:
		     print "NIPdebug: could not open or write to "+hofdataf
		  try: 
		    hofFile.close()
		  except:
		    pass
		  
	################################################################
        
	def nip_hof_update(self, hofdataf):
	    if self.dl:
	       print "HoF update!"
	    if len(self.allscore):
	       points=self.allscore.values()
	       players=self.allscore.keys()
               for player in players:
	           point=self.allscore[player]
                   updateplayer=self.isinhof(str(player))
		   if updateplayer:
		      newscore=updateplayer[2]+point
		      self.hof[int(updateplayer[0])-1]=player,newscore
		      print "newscore= "+str(newscore)
		   else:
		      newscore=self.allscore[player]
		      self.hof.append("dim") #did not know how to append str,int
		      self.hof[len(self.hof)-1]=player,newscore
	    
	    #hmm let's write and "reload" HoF here, so we just call nip_hof_update when game ends with aborted, and TODO: termination hook... perhaps
	    self.nip_hof(hofdataf,"write")
	    self.hof=self.nip_hof(hofdataf,"read")
	    if self.dl:
	       print "HoF updated"
	
	def isinhof(self, player):
	    placecnt=0
	    for hplayer, val in self.hof:
	        placecnt+=1
	        if player==hplayer:
		   #return str(placecnt),hplayer, val # later return placecnt-1 
		   if self.dl:
	              print "NIPdebug: isinhof returns"+str(placecnt),player,val
		   return str(placecnt),hplayer, val      
	    return False
	     
		
