# This file is part of OtfBot.
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
#/*
#Thanks to "Wete" "p_kater" and "stetie" for the very good ideas and testing this game, and of course 
#"allo" and "cato" (for the nice basement at least)
#Let's make this game famous :)
#Note: Still under construction
#*/
#actual Gameflow -> !startgame > join|add with "ich" > !startgame > Round1 > !restart >Roundbar |>!end/abort <>!vote end[e]/abort
#Everything should work automatically except !restartgame, well after the gameadmin has been "removed", if he does not restart the game,
#the game will pause as long as another player will do ![re]startgame(or !end/abort). The removed gameadmin might !join/add immediately without being the new gameadmin.
#game modified and "prettyfied" by neTear 12/2007 01/2008 with Midnight Commander/Kate, just because python 'sucks'...
#Addition: saving the scoretable when game "ends" - for better HoF statistics in future
#Addition: Timeout Warnings to players without action during QUIZ and WAITING_FOR_ANSWERS "Schnarchnasenorden" - this one is configurable, too ;)
#Addition: Class Favorits will give sorted list (by points) for output
#Bugfix and Addition: Max. Nick Len. Players nickname longer than maxnicklen cannot (be) join(ed)/add(ed)
#Todos: track .task errors, maybe the pointer gets lost when stopping timer?
# -*- coding: utf-8 -*- 
import shutil, time, random, string, os
import chatMod
import twisted.internet.task as timehook
import math #just used for voting, needed for "rounding", try another solution...
import pickle
import atexit
import operator as favop
HELPUSER="#CCHAR#join #CCHAR#part (mitspielen/aussteigen) #CCHAR#score #CCHAR#rules #CCHAR#+players"
HELPADMIN="#CCHAR#abortgame #CCHAR#restartgame #CCHAR#add/remove Mitspieler #CCHAR#gamespeed #CCHAR#autoremove #CCHAR#kill "
HELPBUG="Genervte #BOLD#irssi#BOLD#-Anwender moegen ein \"/set mirc_blink_fix on\" machen, oder x-chat,chatzilla,mIRC oder Telnet... benutzen ;)"

#game phases
NO_GAME=0
WAITING_FOR_PLAYERS=1
WAITING_FOR_QUESTION=2
WAITING_FOR_QUIZMASTER_ANSWER=3
WAITING_FOR_ANSWERS=4
QUIZ=5
GAME_WAITING=6

class chatMod(chatMod.chatMod):
	
	def __init__(self, bot):
		self.bot=bot
		atexit.register(self.nipexithook)
		self.kcs_=self.fp_handler()
		self.fav=self.favorits()
		self.NIPbuffer=self.NIPqb()
		self.default_nip()
		self.nip_init()
		self.init_vars()
		self.fav.load(self.nipdatadir+self.favfile)
		self.fav.sort() #sorting all entries

	class fp_handler():#
		def __init__(self):
			self.name = []
			self.fp_time = [] #default/config
			self.user = [] #list in list ....
			#self.channel = [] #
			self.fp_ts = []
			
		def cmd_index(self, cmd):
			if cmd in self.name:
				for i in range(len(self.name)):
					if self.name[i]==cmd:
						return i
			else:
				return False
		def delUser(self, cmd, user=None):
			if not type(cmd)==int:
				i=self.cmd_index(cmd)
			else:
				i=int(cmd)
			if user==None:
				self.user[i]=[]
			else:
				if user in self.user[cmd]:
					self.user[i].remove(user)
				else:
					if user in self.user[i]:
						self.user[i].remove(user)
		def addUser(self, cmd, user):
			if type(cmd)==int: #different kind of overloading oO
				if not user in self.user[cmd]:
					self.user[int(cmd)].append(user)
			else:
				i=self.cmd_index(cmd)
				if not user in self.user[i]:
					self.user[i].append(user)
		def release(self,cmd):#for special purposes
			self.fp_ts[self.cmd_index(cmd)]=int(time.time())


	class favorits():
		def __init__(self):
			self.player = {}
		def findex(self, oldlist, favoritee):
			for i in range(len(oldlist)):
				if oldlist[i][0]==favoritee:
					return i
			return -1
		def add(self, player, favoritee):
			if player==favoritee:
				return False
			if self.player.has_key(player):
				favoritees=self.player.get(player,"[]")
				findex=self.findex(favoritees, favoritee)
				if findex > -1:
					favoritees[findex][1]+=1
					self.player[player]=favoritees
				else:
					self.player[player]=[[favoritee,1],]
					favoritees.append([favoritee, 1])
					self.player[player]=favoritees
			else: #first add player to list
				self.player[player]=[[favoritee,1],]
		def getlist(self, player):
			if self.player.has_key(player):
				return self.player.get(player,"[]")
			else:
				return False
		def save(self, favfile):
				try:
					sfile=open(favfile, "w")
					pickle.dump(self.player,sfile)
					sfile.close()
				except IOError:
					print "Error writing to file "+favfile
				finally:
					sfile.close()
		def load(self, favfile):
				try:
					lfile=open(favfile, "r")
					self.player=pickle.load(lfile)
					lfile.close()
				except IOError:
					print "Error reading file "+favfile
				finally:
					pass
		def sort(self, player=None):
				try:
					if not player:
						for player in self.player.keys():
							self.player[player]=sorted(self.getlist(player), key=favop.itemgetter(1), reverse=True)
					else:
						self.player[player]=sorted(self.getlist(player), key=favop.itemgetter(1), reverse=True)
				except:
					print "Error while sorting Favorites"
					pass

	class NIPqb():
		def __init__(self):
			self.question = {}
			self.answer = {}
			self.tip = {}
		def get(self, user):
			rv=[(self.question.get(user,"")), (self.answer.get(user,"")),(self.tip.get(user,""))]
			return rv
		def put(self, user, cmd, options):
			options.replace("#","")
			if cmd=="q":
				self.question[user]=options
			elif cmd=="a":
				self.answer[user]=options
			elif cmd=="t":
				self.tip[user]=options
		def clean(self, user):
			self.question[user]=""
			self.answer[user]=""
			self.tip[user]=""
		def save(self, nipbufferfile): #pickle is broken with unicode (since 2000???)
			try:
				sfile=open(nipbufferfile+".dat", "w")
				for player in self.question:
					player=str(player)
					if self.question.has_key(player) and self.answer.has_key(player):
						tip=""
						if self.tip.has_key(player):
							tip=self.tip[player]
						sfile.write(player+"#"+str(self.question[player])+"#"+str(self.answer[player])+"#"+tip+"\n")
				sfile.close()
			except:
				self.bot.logger.error("while saving NIPbuffer")
			finally:
				sfile.close()
		def load(self, nipbufferfile):
			try:
				lfile=open(nipbufferfile+".dat", "r")
				qbdata=lfile.read()
				lfile.close()
				for line in qbdata.split("\n"):
					if len(line)>1:
						ls=line.split("#")
						self.question[ls[0]]=ls[1]
						self.answer[ls[0]]=ls[2]
						self.tip[ls[0]]=ls[3]
			except:
				pass


	def nipexithook(self):
		self.NIPbuffer.save(self.nipdatadir+"NIPbuffer")
		if not self.phase==NO_GAME:
			self.nip_hof_update(self.nipdatadir+self.hofdatafile)
		self.save_score(True)
		self.fav.save(self.nipdatadir+self.favfile)
		pass
	
	
	def nip_init(self):
		self.gamechannel="" #this is not multichannel compatible! # now it is (more|less) ;)
		self.data_update_needed=False
		self.init_autocmd()
		self.kcs_update(self.kcs_config)
		self.allscore={}
		self.load_score()
		self.nT_init() #init the looptimer with polltime (used for different timeout)
		self.polltime=2    #timer poll in seconds
		self.gl_ts=0       #timestamp for timeouts, needs to be initialised - <=0 is the hook for an action
		self.gamespeed=1 #default gamespeed=1 normal 2= faster timeouts/2
		self.minplayersold=0 #toogle cmd "testing"
		self.autoremove=1 #"!autoremove" toggles 0|1, if set to 1 - players will be removed from list when they do not send in question/answer 
		self.splitpoints=1 #!splitpoints" toggles between 0|1, used to show splittet points. if true returns details in scoring 
		self.hookaction="None" #which function to call on timerhook
		self.hof_show_max_player=8  #max player from HoF to send in channel #
		self.hof_max_player=999 #max players in hof-file
		self.nameofgame="\x038,1\x02|_\x02-\x037~\x034N\x035\x02o\x02 \x034B\x037o\x038\x02d\x02y \x037i\x034s \x035\x02p\x02\x034e\x037r\x038f\x02e\x02c\x037t\x034~\x035\x02-\x02\x034_\x038|\x0F" #"colors are fun when not abused
		#todo make const and or config ^^^ (xml sucks for config?)
		self.uservoted_end=[]
		self.votedEnd=0
		self.newplayers=[] #used as buffer for joining during game round 
		self.hof=[]
		self.hof=self.nip_hof(self.nipdatadir+self.hofdatafile,"read") #
		self.NIPbuffer.load(self.nipdatadir+"NIPbuffer")
		#################
		
	def default_nip(self):
		#first using global vars, try to make them local when everything works
		#the best would be to make a function for all outputs.... nip_sendmsg,- guess, this game as being opensource will become famous
		self.NIPencoding=self.bot.getConfig("encoding","UTF-8")
		self.cchar=self.bot.getConfig("cchar", "!", "NIP")
		self.nipdatadir=self.bot.getConfig("datadir", "modules/nip-data/", "NIP") #Need to get os? Not for scrappy windows anymore
		self.hofdatafile=self.bot.getConfig("HoFdata", "niphof.txt", "NIP")
		self.favfile=str(self.bot.getConfig("FavoritData", "fav.data", "NIP")) #todo better parsing		
		self.channels=self.bot.getConfig("channels", "#otf-quiz  #nobody-is-perfect", "NIP").split() #all channels where NIPmod will throw messages from and allow to start a game
		self.minplayers=int(self.bot.getConfig("minPlayer", "5", "NIP"))
		self.maxplayers=int(self.bot.getConfig("maxPlayer", "12", "NIP"))
		self.fp_time=int(self.bot.getConfig("FPTime", "5", "NIP")) #default time for floodprotection
		
		self.kcs_config=str(self.bot.getConfig("FPSpecialCommands", "favorits 0,place 0,savegame 52,halloffame 12,place 0,vote 0,scores 12,abortgame 0,add 0,remove 0", "NIP")) #overwrite default fp_time, note: no whitespace after ",".
		
		self.maxnicklen=int(self.bot.getConfig("maxNickLength", "14", "NIP"))
		self.userWarnMax=(int(self.bot.getConfig("AutoremovepPlayerKickAfterRounds", "2", "NIP"))) #better name?
		self.init_timeouts(int(self.bot.getConfig("TimeOutBase", "60", "NIP"))) #see function
		self.TGAMEADMIN=str(self.bot.getConfig("NameGameAdmin", "#BOLD#NIP-Admin#BOLD#", "NIP"))
		self.TGAMEMASTER=str(self.bot.getConfig("NameGameMaster", "#BOLD#QUIZ-Meister#BOLD#", "NIP"))
		self.TNIPQUESTION=str(self.bot.getConfig("NameNipQuestion", "#BOLD##DBLUE#NIP-Frage#NORM#" ,"NIP"))
		self.TNIPWARNINGS=str(self.bot.getConfig("NameNipWarnings", "Verteilung der#BOLD# #DRED#Schnarchnasenorden#NORM#:" ,"NIP"))
		self.NIPRULES=str(self.bot.getConfig("RULES","http://otf-chat.xenim.de/wiki/bot:nobody-is-perfect" ,"NIP"))
		self.mirc_stuff_init()
	
	def kcs_update(self, cmdlist=None): #used to assign longer fp protection (or disable each) from config- update val in .kcs_
		if cmdlist!=None:
			for scmd in cmdlist.split(","):
				scmds=scmd.split(" ",24)
				try:
					cmd=scmds[0]
					val=int(scmds[1])
					#assert type(val)==IntType or int?
					cmdi=self.kcs_.cmd_index(cmd)
					if cmdi:
						self.kcs_.fp_time[cmdi]=val
				except:
					self.bot.logger.error("Config Error with FPSpecialCommands ")

	def init_autocmd(self):
		#knowncommands
		#you have to make every command used in game a "knowncommand" while using "auto_command or Floodprotection".... even those for replace_command
		self.kcs=["vote","halloffame","hof","place","splitpoints","abortgame","resetgame","end","add", "remove", "startgame", "restartgame", "kill", "scores", "ranking", "gamespeed", "autoremove", "stats","favorits","groupies","continue", "players","rules","status","niphelp","join","part","help","testing","netear","p_kater"]
		self.kcs.sort()
		i=0
		for cmd in self.kcs: #Todo: use_ this in autocommand
			self.kcs_.name.append(cmd)
			self.kcs_.fp_time.append(int(self.fp_time))
			self.kcs_.user.append([''])
			self.kcs_.fp_ts.append(0)


	def init_timeouts(self, timeOutBase):
		TimeBase=60
		if type(timeOutBase)==int:
			if timeOutBase>30 and timeOutBase<420:
				TimeBase=timeOutBase
			else:
				self.bot.logger.error("TimeOutBase Config must not be smaller 30 or greater 420")
				TimeBase=60
		else:
			self.bot.logger.error("TimeOutBase Config has to be an integer")
			TimeBase=60
		self.timeouts={}#used in nTimerset
		self.timeouts['ANSWER_TIME']=2*TimeBase
		self.timeouts['QUIZ_TIME']=TimeBase-10   #60 time waiting for quiz answers, nTimerset will add foo seconds for each player
		self.timeouts['QUIZ_TIME_ADD']=9 #add seconds to QUIZ_TIME(out) for each player (used for ircd)
		self.timeouts['TIMEOUT']=2*TimeBase #300 idle time until game stops to "game_waiting", "waiting_for_gamemaster" NIP-Question
		self.timeouts['STARTPHASE']=TimeBase*8 #Timeout after first !startgame - will call end_of_game (not end_of_quiz)
		#we now use them as default base values, - !gamespeed will half all times
		self.timeouts['GAMEADMINNOTIFY']=TimeBase #sends a "highlight" to a sleeping "gameadmin"
		self.timeouts['GAMEADMINKICK']=TimeBase #kick the lazy gameadmin after notify, [re]starter|aborter will be the new one automatically
		for name in self.timeouts.keys():
			self.bot.logger.info(str(name)+" "+str(self.timeouts.get(name,""))+" sec")


	def mirc_stuff_init(self):
		self.NIPPREFIX="|\x0316,14NIP\x033\x0F" #nip gameplay pre output this - may be set to =""
		#some (m)IRCstuff... I LOVE eyecandy! (but it must not disturb)
		self.colors={}
		self.colors["#BOLD#"]="\x02" #tooglelike 
		self.colors["#NORM#"]="\x0F" #resetallMIRColorslike
		self.colors["#UNDERLINE#"]="\x1F" # tooglelike 
		self.colors["#DBLUE#"]="\x032"
		self.colors["#DGREEN#"]="\x033"
		self.colors["#LRED#"]="\x034"
		self.colors["#DRED#"]="\x035"
		self.colors["#LCYAN#"]="\x0311"
		self.colors["#DCYAN#"]="\x0310"
		self.colors["#LBLUE#"]="\x0312"
		self.colors["#LGREY#"]="\x0315"
		self.colors["#DGREY#"]="\x0314"
		self.colors["#WHITE#"]="\x0316"
		self.colors["#LMAGENTA#"]="\x0313"
		self.colors["#DMAGENTA#"]="\x036"
		#These are $category depending colored "2nd Pre-things"
		pchar="_" #fix for none monospace clients
		self.pres={}
		self.pres["PRE_N"]="\x031,1"+pchar+"\x0F "		#Black after Standard Prefix as default nr 2, and special ones for special conditions
		self.pres["PRE_Q"]="\x034,4"+pchar+"\x0F "		#Red - Send me the Question /The question is/was
		self.pres["PRE_A"]="\x033,3"+pchar+"\x0F "		#Dark Green right Answer
		self.pres["PRE_C"]="\x039,9"+pchar+"\x0F "		#Light Green for possible answers are (c like conjuntive)
		self.pres["PRE_S"]="\x037,7"+pchar+"\x0F "		#dark yellow for scoring
		self.pres["PRE_H"]="\x0311,11"+pchar+"\x0F "	#cyan for help messages
		self.pres["PRE_X"]="\x036,6"+pchar+"\x0F "		#magenta for messages to gameadmin
		self.pres["PRE_G"]="\x035,5"+pchar+"\x0F "		#dark red for game status things....
		self.pres["PRE_P"]="\x0312,12"+pchar+"\x0F "	#Light blue for Punishments
		self.pres["PRE_Z"]="\x035,5"+pchar+"\x0F "		#Dark Red also for Hall of fame? 
		self.pres["PRE_V"]="\x0310,10"+pchar+"\x0F "	#dark cyan for VOTES
		self.pres["PRE_D"]="\x0314,14"+pchar+"\x0F "	#dark Grey for misc
 
	def init_vars(self):
		self.phase=NO_GAME
		self.players=[]
		self.gameadmin="" #needed for deciding when to start the game/and other things 
		self.gamemaster="" #different for each round.
		self.gamemasterold="" #used to catch lazy user, who wants to cheat by removing and adding himself as gamemaster!
		
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.scores={} #Splitted scores
		self.guessed=[] #users, which already have guessed 
		self.additional_info=None
		self.abortcnt=0
		self.resetcnt=0 #used to punish a gamemaster who resets game to WAITING_FOR_QUESTION, and to control how often he could do that
		self.starttime=time.strftime("%Y/%m/%d %H:%M:%S") #used for scoring table data on disc when game ends
		self.roundofgame=1 #counter, used in game as info, maybe good for new statistic
		self.eoq_cnt=0 #see end_of_quiz ~used for debugging #obsolete when everything works
		self.votedEnd=0 #important to reset here...
		self.userWarnCnt={} #used for autoremoving player after foo times giving no "quiz-answer"


	def init_vars_for_restart(self):
		self.abortcnt=0 #used for Mfoo-style like Are you really sure...
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.scores={}
		self.guessed=[] #users, which already have guessed
		self.additional_info=None
		self.roundofgame+=1
		self.uservoted_end=[]
		self.new_gamemaster()

	def new_gamemaster(self):
		#each player will be gamemaster, in order ## now cheat protected :) because remove does work everytime ("add" now too, via "buffer")
		#cheatprotection	
		self.bot.logger.debug("Try to catch a cheater while restarting game")
		if len(self.gamemasterold) > 0: #we have a cheat candidate
			if str(self.gamemasterold) in self.players: # and the cheater is back in next round, so 
				self.nipmsg("PRE_P"+self.gamemasterold+" Du versuchst zu #BOLD#mogeln#BOLD#? 2 Punkte Abzug und gleich nochmal der "+self.TGAMEMASTER) 
				self.add_allscore(str(self.gamemasterold),-2)
				self.gamemaster=self.gamemasterold
				if self.gamemaster in self.players: # todo set_gamemaster()
					self.players.remove(self.gamemaster)
			else:
				self.gamemasterold="" #did not rejoin the game okay
		if len(self.gamemasterold) == 0:
			#changing gamemaster if no cheater
			if len(self.gamemaster) > 0 and not self.gamemaster in self.players:
				self.bot.logger.debug("Pushing gamemaster back to players -"+str(self.gamemaster))
				self.players.append(self.gamemaster) #puts him back to the end	
			self.gamemaster=self.players[0] #sets the next
			self.players=self.players[1:]   #
			self.gamemasterold=""
			self.resetcnt=0
			self.bot.logger.debug("Setting new Gamemaster to: "+self.gamemaster)
		self.gamemasterold=="" #just to be sure
		
	############################################# 
	
	def nipmsg(self, cmsg, ochannel=None):
		#if ochannel==None and self.phase==NO_GAME:
		if ochannel==None and not self.gamechannel:
			self.bot.logger.debug("No nipmsg - "+cmsg)
		else:
			if ochannel==None:
				cchannel=self.gamechannel
			else:
				cchannel=ochannel
			for color in self.colors.keys():
				if cmsg.count(color):
					val=self.colors.get(color, "")
					cmsg = cmsg.replace(color,val)
			for pre in self.pres.keys():
				if cmsg.count(pre):
					val=self.pres.get(pre, "")
					cmsg = cmsg.replace(pre, val)
			if cmsg.count("#CCHAR#"):
				cmsg = cmsg.replace("#CCHAR#",str(self.cchar))
			#self.bot.logger.debug("nipmsg to:"+str(cchannel)+"|"+cmsg)
			self.bot.sendmsg(cchannel, str(self.NIPPREFIX)+cmsg, self.NIPencoding)
	
	
        def nTimerhook(self):
		self.gl_ts-=self.polltime
		if self.gl_ts <= 0:
			if self.nTimer.running:
				self.nTimer.stop() #stops twisted.internet.task.LoopingCall...., lost pointer?
				self.bot.logger.debug("Timer stopped gl_ts="+str(self.gl_ts))
			else: #stopped before, should fix runtime-race condition when game ends
				self.bot.logger.debug("Timer stopped before. No hookaction in Phase="+str(self.phase)+" action="+self.hookaction)
				return 0
			if self.hookaction=="end_of_quiz":
				self.bot.logger.debug("hookaction->"+str(self.hookaction)+" Phase:"+str(self.phase))
				self.hookaction="None"
				self.end_of_quiz()
		 
			elif self.hookaction=="end_of_answertime":
				self.bot.logger.debug("hookaction->"+str(self.hookaction)+" Phase:"+str(self.phase))
				self.hookaction="None"
				self.end_of_answertime()

			elif self.hookaction=="notify_gameadmin":
				self.bot.logger.debug("hookaction->"+str(self.hookaction)+" Phase:"+str(self.phase))
				self.hookaction="None"
				self.notify_gameadmin()
		
			elif self.hookaction=="kick_gameadmin":
				self.bot.logger.debug("hookaction->"+str(self.hookaction)+" Phase:"+str(self.phase))
				self.hookaction="None"
				self.kick_gameadmin()
				if self.phase==WAITING_FOR_PLAYERS:
					self.end_of_game()


		if (self.phase==QUIZ or self.phase==WAITING_FOR_ANSWERS or self.phase==WAITING_FOR_QUESTION) and not self.playerwarned:
			if self.gl_ts <= self.warn_ts:
				self.warn_players()
				self.playerwarned=1
		#Good place for debugging stuff at this point, but vvvverbose
		#tstatus=str(self.nTimer.running)
		#print "NIPdebug: Timer running:"+tstatus+" gl_ts=" +str(self.gl_ts)+"  Gamephase="+str(self.phase)+" hookaction="+str(self.hookaction)+" [NIL]"
		
	def nT_init(self):
		self.nTimer=timehook.LoopingCall(self.nTimerhook) #this is the workaround for callLater
		self.bot.logger.debug("nTimer initialised")	

	def nTimerset(self, REQ_TIME, REQ_ACTION):
		#try:
		if self.nTimer.running:
			self.nTimer.stop()
		#dynamically longer timeouts for some conditions (ircd thwarts game when playing with more players )
		if type(REQ_TIME)==str:
			REQ_TIME=int(self.timeouts.get(REQ_TIME, 60))
		addtime=2
		if self.phase==QUIZ: # maybe we don't need that with less than 5 players ... 
			addtime=self.player_qty()*int(self.timeouts.get('QUIZ_TIME_ADD',5))
			self.bot.logger.debug("Expanding Timeout"+str(addtime))
		self.hookaction=REQ_ACTION
		self.gl_ts=(REQ_TIME+addtime)/self.gamespeed
		self.warn_ts=self.gl_ts / 3 #used for warning players for timeout "Schnarnasenorden" oO
		self.playerwarned=0 #bool to avoid multiple "Schnarchnasenorden"
		
		self.nTimer.start(self.polltime)
		self.bot.logger.debug("Starting Timer: polltime=" +str(self.polltime)+" REQ_ACTION:"+str(self.hookaction)+" REQTIME:"+str(self.gl_ts)+" warn_ts:"+str(self.warn_ts))


	#Floodprotection
	def cmd_is_fp(self, cmd, user): #FP for each cmd with different protect times
		#releasing protection without a loopingCall
		cmdi=self.kcs_.cmd_index(cmd)
		if cmdi:
			act_ts=int(time.time())
			c_ts=self.kcs_.fp_ts[cmdi]
			if c_ts < act_ts:
				self.kcs_.delUser(cmdi)
				self.kcs_.fp_ts[cmdi]=0
			c_ts=self.kcs_.fp_ts[cmdi]
			if c_ts!=0: #release and warn
				if c_ts < act_ts: #release
					self.kcs_.fp_ts[cmdi]=0
					self.kcs_.delUser(cmdi, user)
					return False
				else: #return time left to wait or -1 if user has been informed once
					c_ts-=act_ts
					if not user in self.kcs_.user[cmdi]:
						#self.kcs_.user.insert(cmdi, user)
						self.kcs_.addUser(cmd, user)
						return c_ts
					else:
						return -1 #user got notice once
				
			else: #protect the cmd
				if c_ts==0: #.-1 
					self.kcs_.fp_ts[cmdi]=self.kcs_.fp_time[cmdi]+act_ts
					return False


##########################################################

	def notify_gameadmin(self):
		if self.gameadmin!="":
			self.nTimerset('GAMEADMINKICK', "kick_gameadmin")
			taction="restartgame"
			if self.phase==WAITING_FOR_PLAYERS:
				taction="startgame"
			self.nipmsg("PRE_X"+self.TGAMEADMIN+" "+str(self.gameadmin)+" #CCHAR#"+taction)
		else:
			if not self.phase==WAITING_FOR_PLAYERS and not self.phase==NO_GAME:
				self.show_players()
				self.nipmsg("PRE_XWeiter geht's mit #BOLD##CCHAR#restartgame ")
				self.phase=GAME_WAITING

	def kick_gameadmin(self, refby=None):
		self.bot.logger.debug("kick_gameadmin refby "+str(refby))
		if self.gameadmin!="":
			gameadmin=self.gameadmin
			self.nipmsg("PRE_X"+self.TGAMEADMIN+" #UNDERLINE#"+gameadmin+"#UNDERLINE# hat wohl keine Lust mehr. Pause?")
			self.gameadmin=""
		else:
			self.show_players()
			self.nipmsg("PRE_XWeiter geht's mit #BOLD##CCHAR#restartgame ")
			
		if not self.phase==WAITING_FOR_PLAYERS and not self.phase==NO_GAME: #
			self.phase=GAME_WAITING #set only when not in "startphase"
		else:
			self.nipmsg("PRE_XWeiter geht's mit #BOLD##CCHAR#startgame ")


	def stop_timer(self):
		if self.nTimer.running:
			self.nTimer.stop()
		self.gl_ts=0 #


	def add_player(self, addnick):
		if self.phase==NO_GAME:
			return 0
		if len(addnick) > self.maxnicklen:
			self.nipmsg("PRE_X"+addnick+": Dein Nickname ist zu lang fuer das Spiel, maximal "+str(self.maxnicklen)+" Zeichen.")
		else:
			addnick=addnick[:self.maxnicklen] #
			if addnick in self.players:
				return 0
			else:
				if self.check_maxplayer():
					if addnick!=self.gamemaster:
						if not self.phase==WAITING_FOR_PLAYERS: #not when waiting for "ich" in startphase
							self.nipmsg("PRE_X"+addnick+" spielt jetzt mit.")
						self.bot.logger.debug("add_player: Appending player:"+addnick)
						self.players.append(addnick)
					return 1

	
	def del_player(self, delnick, refby=None): #refby=call other subroutines or not - q&d
		self.bot.logger.debug("del_player refby:"+str(refby))
		#cheatprotection
		#if self.phase==WAITING_FOR_QUESTION or self.phase==WAITING_FOR_QUIZMASTER_ANSWER:
		if delnick==str(self.gamemaster) and self.gamemasterold=="":
			self.gamemasterold=delnick
			self.bot.logger.debug("set Gamemasterold="+self.gamemasterold)

		#del_player rest
		if not self.votedEnd:
			#once voted the game_end, do NOT remove players (missing self.end_of_game() for some conditions) 
			#(even though it's possible to !remove when a vote has been initiated - note: remove/part will remove a vote, too)
			c=0
			if delnick in self.players:
				c=1
				self.players.remove(delnick)
			if self.gameadmin==delnick:
				self.gameadmin=""
			if self.gamemaster==delnick:
				c=1
				self.gamemaster=""
				if not refby=="end_of_quiz": #avoids double msg while autoremove gamemaster as gameadmin
					if not self.answers.has_key(delnick): #avoids eog while gamemaster had sent in question AND answer
						self.end_of_quiz() #rather redundant but sexy

			if c: #changed
				if delnick: #
					if refby=="autoremoving":
						self.nipmsg("PRE_X"+delnick+" mangels Lebenszeichen automatisch aus dem Spiel entfernt.")
					else:
						self.nipmsg("PRE_X"+delnick+" spielt nicht mehr mit.")
					
				if delnick in self.uservoted_end:
					self.uservoted_end.remove(delnick)
				#remove from join buffer
				if delnick in self.newplayers:
					self.newplayers.remove(delnick)
					if not delnick in self.players:
						self.nipmsg("PRE_X"+delnick+" hat wohl doch keine Lust.")
		else:
			if not self.phase==NO_GAME and not self.phase==GAME_WAITING:
				self.nipmsg("PRE_V"+delnick+": Nach der Runde ist ohnehin Spielende.")


	def show_players(self):
		pnr=len(self.players)
		pnr=0
		splayers=""
		for tplayer in self.players:
			if tplayer==self.gameadmin:
				tplayer="#UNDERLINE##BOLD#"+tplayer+"#BOLD##UNDERLINE#"
			if tplayer!=self.gamemaster:
				splayers=splayers+" "+tplayer
			pnr+=1
		if self.gamemaster:
			splayers=splayers+" #BOLD#"+self.gamemaster+"#BOLD#"
			pnr+=1
		self.nipmsg("PRE_G"+str(pnr)+" Teilnehmer:"+splayers)
	
	
	def warn_players(self):
		wplayers=""
		if self.phase==QUIZ:
			for player in self.players:
				if not player in self.guessed:
					wplayers=wplayers+" "+player
		#if not self.gamemaster in self.guessed:
		#   wplayers=wplayers+" "+self.gamemaster
		if self.phase==WAITING_FOR_ANSWERS:
			for player in self.players:
				if not player in self.answers.keys():
					wplayers=wplayers+" "+player
		if self.phase==WAITING_FOR_QUESTION:  # or self.phase==WAITING_FOR_QUIZMASTER_ANSWER:
			wplayers=str(self.gamemaster)
		if len(wplayers) > 1:
			self.nipmsg("PRE_H"+self.TNIPWARNINGS+" "+wplayers+"#DGREY#  Noch ~"+str(self.gl_ts)+" Sek.")
	

	def new_gameadmin(self, gnick):
		self.bot.logger.debug("new_gameadmin <"+gnick+"> phase:"+str(self.phase))
		if self.phase==GAME_WAITING: #not for no_game
			self.nTimerset('GAMEADMINNOTIFY',"notify_gameadmin")
		if len(gnick) <= self.maxnicklen:
			self.gameadmin=gnick
			if not gnick in self.players: #"if" should be obsolete due to add_player()
				self.add_player(gnick)
			self.nipmsg("PRE_XDer neue "+self.TGAMEADMIN+" ist #BOLD#"+gnick)
		else:
			self.nipmsg("PRE_X"+gnick+": Dein Nick ist leider zu lang!")
	
	def player_qty(self):
		plc=len(self.players)
		if self.gamemaster:
			plc+=1
		return plc
	
	def check_maxplayer(self):
		if self.player_qty() >= self.maxplayers:
			self.nipmsg("PRE_XDie Runde ist voll. Maximal "+str(self.maxplayers)+" koennen mitspielen.")
			self.bot.logger.debug("MaxPlayer "+str(self.maxplayers))
			return 0
		else:
			return 1
	########################### a hoockaction
	def end_of_answertime(self):
		self.phase=QUIZ
		self.nTimerset('QUIZ_TIME', "end_of_quiz") #needs to be here 
		count=1
		qw="Die Frage war: "
		if self.gamemaster:
			qw=self.gamemaster+" fragte: "
		self.nipmsg("PRE_Q"+qw+"#BOLD#"+self.question)

		self.nipmsg("PRE_C#UNDERLINE#Moegliche #BOLD#Antworten#BOLD# sind:#UNDERLINE#  ~"+str(self.gl_ts)+" Sek. Zeit!#DGREY#  (Aufforderung abwarten!)")
		
		users=self.answers.keys()
		random.shuffle(users)
		for user in users:
			self.nipmsg("PRE_C#BOLD#"+str(count)+"#BOLD#. "+self.answers[user])
			self.answeruser[count]=user
			count+=1
		self.nipmsg("PRE_C#DGREY##UNDERLINE#_-=Und nun nur die Zahl als Antwort=-_")

	#### functions below belong to end_of_quiz
	def add_allscore(self, player, qty=None):
		self.bot.logger.debug("add_allscore:"+player+" "+str(qty))
		#just send negative values for qty if you want to "punish" a player
		# if qty is 0 self.score[user] will be used to calc gameround points
		if  qty!=None:
			if str(player) in self.allscore.keys():
				self.allscore[player]+=qty
			else:
				self.allscore[player]=qty
		else: #round "allscore" calculation
			if str(player) in self.answeruser.values(): #we are evil at that point - no point for no given answer
				if player in self.allscore.keys():
					self.allscore[player]+=self.score[player]
				else:
					self.allscore[player]=self.score[player]
		if not self.data_update_needed:
				self.data_update_needed=True
				self.bot.logger.debug("Setting data update is needed")

	def answer_from_who(self):
		#show who gave which answer, return right answer at first
		snum=0
		firsttext="PRE_C"+"" #
		text=""
		#build the output array here for 'from who'
		for num in self.answeruser:
			if self.answeruser[num]==self.gamemaster or self.answeruser[num]==self.gamemasterold:
				snum=num #stored for later use 
				firsttext+="("+self.answeruser[num]+" #NORM#**#BOLD#"+str(num)+"#BOLD#**)#NORM# "
			else:
				text+="#DGREY#("+self.answeruser[num]+" #NORM#"+str(num)+"#DGREY#)"
		fromwho=firsttext+text	
		return fromwho,snum
	
	def quiz_scoring(self):
		if len(self.score):
			for player in self.score:
				pword="Punkte"
				pscore=self.score[player]
				pscores="" #show splitted only when more than one point
				if pscore >= 9:#
					pscore+=2 #Extra points for "three in a row"
					self.bot.logger.debug("Three in a row for "+player)
					self.score[player]+=2
					self.scores[player]+="#LRED# +2* Bonus#DGREY#"
				if pscore==1:
					pword="#LMAGENTA#*#NORM#chen" # yet another gimmick
				else:
					if self.splitpoints: #show only if wanted scoreS(splitted) not score ;)
						pscores="#DGREY#("+self.scores[player]+")#NORM#" #maybe good to use in add_allscore with eval() - later
				
				if str(player) in self.answeruser.values(): #we are !evil, no points for no given nip answer but guessing ;)
					self.nipmsg("PRE_S"+player+" bekommt #BOLD#"+str(pscore)+"#BOLD##NORM# "+pword+" "+pscores)
				else:
					self.nipmsg("PRE_P"+player+" #UNDERLINE#bekaeme#UNDERLINE##BOLD# "+str(pscore)+"#BOLD##NORM# "+pword+"#DGREY# (Keine moegl. Antwort geliefert, keine Puenktchen!)")
					
				
			#set in allscore
			for user in self.score:
				self.add_allscore(user)


	def check_for_answer(self):
		for player in self.players:
			if not player in self.answeruser.values():
				if self.userWarnCnt.has_key(player):
					self.userWarnCnt[player]+=1
				else:
					self.userWarnCnt[player]=1
			else:
				if self.userWarnCnt.has_key(player):
					self.userWarnCnt[player]=0

	
	def autoremoving(self, justplayer=None):
		if not justplayer:
			atext="" #
			if self.gamemaster==self.gameadmin:
				if self.autoremove and not self.votedEnd:
					self.kick_gameadmin("end_of_quiz")
			else:
				if self.autoremove and not self.votedEnd:
					self.del_player(self.gamemaster, "end_of_quiz")
		else:
			self.bot.logger.debug("autoremoving player")	
			for player in self.players:
				if player in self.userWarnCnt.keys():
					if int(self.userWarnCnt.get(player,0))>=self.userWarnMax:
						self.del_player(player,"autoremoving")


	def correct_answer(self, snum):
		gm=self.gamemaster
		if gm=="":
			gm=self.gamemasterold
		correct="PRE_ARichtige Antwort: #BOLD#"+str(snum)+"#BOLD# (#DGREY#"+self.answers[gm]
		if self.additional_info:
			correct=correct+"#NORM# Tip:#DGREY#"+self.additional_info+"#NORM#)"
		else:
			correct=correct+"#NORM#)"
		return correct
	
	def no_nip_question(self):
		gmaster=""
		if self.gamemasterold!="":
			gmaster=self.gamemasterold #maybe he has "removed"
		if self.gamemaster!="":
			gmaster=self.gamemaster
		if not self.answers.has_key(gmaster):
			return "PRE_X"+self.TGAMEMASTER+gmaster+" hatte keine "+self.TNIPQUESTION

	def add_new_players(self):
		if len(self.newplayers) > 0:
			for newplayer in self.newplayers:
				if not newplayer in self.players:
					self.add_player(newplayer)
					self.bot.logger.debug("Adding player from newplayers buffer"+newplayer)
			self.newplayers=[]
		
	##################### a hookaction	
	def end_of_quiz(self):
		self.bot.logger.debug("end_of_quiz:"+str(self.roundofgame)+"-"+str(self.eoq_cnt))
		
		if not self.votedEnd: #votedEnd also means gameadmin did !abortgame
		   self.phase=GAME_WAITING
		#show who gave which answer
		if self.eoq_cnt==self.roundofgame: #avoids double scoring, at least for debugging
			self.bot.logger.error("EndOfQuiz called more than once!")
		else:
			fromwho, snum=self.answer_from_who() #builds the string for output and gives no. of right answer
			self.quiz_scoring() #throws score results and does calculalations
		
		self.nipmsg("PRE_X#UNDERLINE#_-=#BOLD#Ende der Runde#BOLD#=-_#UNDERLINE# #DGREY#"+str(self.roundofgame))
		if snum > 0: # 0= at least no answer from gamemaster
			self.nipmsg(self.correct_answer(snum))
			self.nipmsg(fromwho)
			self.gamemasterold="" #reset cheatprotection Nipquestion was given
		else: #no answ 
			if self.eoq_cnt==self.roundofgame:
				self.bot.logger.error("EndOfQuiz called more than once!")
			else:
				self.autoremoving() #
				self.nipmsg(self.no_nip_question())
		if self.votedEnd:
			self.end_of_game()
		#last but not least co
		else:
			if self.autoremove:
				self.check_for_answer()
				self.autoremoving(True)# check for lazy player
			self.add_new_players() #tadd hose joined during quiztime
			if self.eoq_cnt < self.roundofgame:
				self.eoq_cnt=self.roundofgame #
			self.eoq_cnt=self.roundofgame
			self.nTimerset('GAMEADMINNOTIFY', "notify_gameadmin")


	def end_of_game(self):
		self.stop_timer()
		self.nipmsg("PRE_XSpiel beendet, #CCHAR#startgame startet ein Neues")
		self.phase=NO_GAME
		self.gameadmin=""
		self.gamemaster=""
		self.gameChannel=""
		self.bot.logger.info("Gamechannel disangeged")
		self.nip_hof_update(self.nipdatadir+self.hofdatafile)
		self.save_score()
		self.fav.save(self.nipdatadir+self.favfile)
		self.players=[]
		self.uservoted_end=[]


	def auto_command(self, cmd, uuser, cchannel):
		# not stress-tested so far, and maybe something for the bot itself
		# extracts given usercmd to a given command, not case-sensitive, so user(player) may say !AborT and we'll realise
		## Todo: for hundreds of commands i suggest to build another list/hash from first char of given command
		## this is quick and dirty just to play around with python 
		## Todo try to put the hit on the first unique cmd in kcd
		if cmd=="":
			return cmd
		i=0
		a=0
		it=""
		if cmd in self.kcs:
			it=cmd
			return it
		else:
			while ( a < len(self.kcs)):
				kc=self.kcs[a]        #would be nice to have a sorted haash #kcs_ Todo
				a+=1
				if kc[:len(cmd)]==string.lower(cmd):
					hit=kc
					i+=1
					if i >=2: #not unique
						if cchannel==self.gamechannel: #avoid cmd conflicts oO
							self.nipmsg("PRE_H"+uuser+": Meintest du:#BOLD#"+self.suggest_command(cmd)+"#BOLD#?")
						break
			if i == 1:
				it=hit
			else:
				if i == 0:
				#too long?
					if cchannel==self.gamechannel:
						suggest=self.suggest_command(cmd[:1])
						if suggest:
							self.nipmsg("PRE_H"+uuser+": Meintest du:#BOLD#"+suggest+"#BOLD#?")
			return it

		
	def suggest_command(self, cmd):
		suggest=""
		for suggests in self.kcs: #todo use kcs_
			if cmd==suggests[:len(cmd)]:
				suggest=suggest+" \"#CCHAR#"+suggests+"\""
		return suggest


	def replace_command(self, cmd):    #maybe useful
		if cmd=="end":
			cmd="abortgame"
		if cmd=="join":
			cmd="add"
		if cmd=="hof":
			cmd="halloffame"  
		if cmd=="part":
			cmd="remove"
		if cmd=="ranking":
			cmd="halloffame"
		if cmd=="groupies":
			cmd="favorits"
		if cmd=="continue":
			cmd="restartgame"
		if cmd=="p_kater":
			cmd="rules"
		if cmd=="help":
			cmd="niphelp"
		return cmd
	
	def check_channel(self, cchannel, ccommand):
		if ccommand=="status": #ccmd allowed in any channel
			return 1
		if cchannel not in self.channels:
			return 0
		if not self.gamechannel:
			return 1
		elif self.gamechannel==cchannel:
			return 1
		elif self.gamechannel!=cchannel:
			if ccommand=="startgame":
				self.nipmsg("PRE_XEs wird bereits gespielt! #BOLD#/join "+self.gamechannel, cchannel)
			return 0
	
	def vote_for_end(self, vuser, adminVote=None):
		self.bot.logger.debug("AdminVote:"+str(adminVote))
		#how many players are needed to end game without gameadmin,  let's try ~30%
		if self.player_qty() >= self.minplayers or adminVote:
			vote_min_player=int(round(self.player_qty() * 0.4)+0.49) #
			if not vuser in self.uservoted_end and (vuser in self.players or vuser==self.gamemaster): #
				self.uservoted_end.append(vuser)
			veq=str(len(self.uservoted_end))
			if vote_min_player < 2:
				vote_min_player=2
			self.bot.logger.debug("Vote End:"+str(veq)+"/"+str(vote_min_player))
			if int(veq) >= vote_min_player:
				if self.phase==WAITING_FOR_PLAYERS or self.phase==GAME_WAITING:
					if not adminVote:
						self.nipmsg("PRE_VAbstimmung: #BOLD#Spielende!")
					self.end_of_game()
				else:
					if not adminVote:
						self.nipmsg("PRE_VAbstimmung:#BOLD#Spielende#BOLD# am Ende der Runde!")
					else:
						self.nipmsg("PRE_V#BOLD#Spielende#BOLD# am Ende der Runde!")
					self.votedEnd=1 #actual round will continue...
			else:
				self.nipmsg("PRE_VAbstimmung Spielende:"+veq+" von benoetigten "+str(vote_min_player)+" Teilnehmern")
		else:
			self.bot.logger.debug("No vote...")
	
	def check_nip_buffer(self, user): #in game
		uservals=self.NIPbuffer.get(user)
		if uservals[0]!="" and uservals[1]!="":
			self.question=uservals[0]
			self.answers[user]=uservals[1]
			self.additional_info=uservals[2]
			self.NIPbuffer.clean(user)
			self.nipmsg("PRE_Q"+self.TNIPQUESTION+" von "+user+": #BOLD#"+self.question)
			self.nipmsg("PRE_ASchickt mir eure #BOLD#\"falschen\"#BOLD# Antworten! ~"+str(self.gl_ts)+" Sek. Zeit! #DGREY#  (/msg "+self.bot.nickname+" eure Antwort)")
			self.phase=WAITING_FOR_ANSWERS
			self.nTimerset('ANSWER_TIME', "end_of_answertime")
			return True
		else:
			return False
	
	def nip_buffer(self, user, channel, command, options):
		bmsg=""
		cmd=command[0]
		if cmd=="h":
			bmsg="!q[uestion] !a[nswer] !t[ip] NIP-Frage vorab einstellen, !n[ip] zeigt die Daten. Ueberschreiben ist moeglich."
		elif cmd=="q" or cmd=="a" or cmd=="t" or cmd=="n":
			if options:
				self.NIPbuffer.put(user, cmd, options)
			rv=self.NIPbuffer.get(user)
			bmsg="Frage: "+rv[0]+" Antwort: "+rv[1]+" Tip: "+rv[2]
		if bmsg:
			self.bot.sendmsg(user, "NIPbuffer: "+bmsg,self.NIPencoding)
		self.bot.logger.debug("NIPbuffer: "+user+" cmd="+cmd)


	def command(self, user, channel, command, options):
			user=user.split("!")[0]
			if channel==self.bot.nickname and user!=self.gamemaster:
				self.nip_buffer(user, channel, command, options) # we check for cmd 
			if not self.check_channel(channel, command): #try this here (is confed gamechannel or a command for all channels)
				return 0
			command=self.auto_command(command, user, channel) #abbreviated commands
			command=self.replace_command(command) #for synonyms
			check_fp=self.cmd_is_fp(command, user) #floodprotection
			if check_fp:
				if check_fp >-1:
					self.nipmsg("PRE_D"+user+":Warte "+str(check_fp)+" Sek. fuer !"+command, channel)
			else:
				self.bot.logger.info("Allowed cmd "+command)
				if channel!=self.bot.nickname: #no query
					if command=="kill":
						if self.gameadmin==user and self.phase!=WAITING_FOR_PLAYERS: 
							self.nipmsg("PRE_XOoops!"+self.TGAMEADMIN+" "+self.gameadmin+" hat wohl keine Lust mehr...")
							self.del_player(user)
							self.gameadmin=""
						else: 
							if self.gameadmin==user:
								self.nipmsg("PRE_X"+self.TGAMEADMIN+" "+self.gameadmin+" das geht erst nach #CCHAR#startgame oder #CCHAR#abortgame")

					elif command=="niphelp":
						self.nipmsg("PRE_H"+HELPBUG)
						if not self.phase==NO_GAME:
							if options[:3].strip()=="all":
 								self.nipmsg("PRE_H"+HELPUSER)
								self.nipmsg("PRE_H"+HELPADMIN)
							else:
								if self.gameadmin==user:
									self.nipmsg("PRE_H"+self.TGAMEADMIN+" "+HELPADMIN)
								else:
									self.nipmsg("PRE_H"+HELPUSER)
						else:
							self.nipmsg("PRE_H#CCHAR#startgame. Waehrend des Spiels #CCHAR#niphelp <all> oder #CCHAR#rules", channel)
			
					elif command=="vote":
						if not self.phase==NO_GAME:
							if string.lower(options[:3].strip())=="end" or string.lower(options[:5].strip())=="abort":
								self.vote_for_end(user)
				
					elif command=="autoremove":
						if user==self.gameadmin:
							if self.autoremove==0:
								self.autoremove=1
								self.nipmsg("PRE_X#BOLD#Autoremove#BOLD# ist nun #BOLD#aktiv#BOLD#, NIP-Fragesteller ohne Aktion werden automatisch aus dem Spiel entfernt")
							else:
								self.autoremove=0
								self.nipmsg("PRE_X#BOLD#Autoremove#BOLD# ist nun #BOLD#inaktiv#BOLD#.")
						else:
							addword="inaktiv"
							if self.autoremove==1:
								addword="aktiv"
							if not self.phase==NO_GAME:
								self.nipmsg("PRE_X#BOLD#Autoremove#BOLD# ist #BOLD#"+addword+"#BOLD#. Wechsel nur durch den "+self.TGAMEADMIN+" moeglich!")

					elif command=="splitpoints":
						if user==self.gameadmin:
							if self.splitpoints==0:
								self.splitpoints=1
								self.nipmsg("PRE_X#BOLD#Splitpoints#BOLD# ist nun #BOLD#aktiv#BOLD#, ich zeige die genaue Punkteverteilung")
							else:
								self.splitpoints=0
								self.nipmsg("PRE_X#BOLD#Splitpoints#BOLD# ist nun #BOLD#inaktiv#BOLD#, ich zeige nur die Gesamtpunktzahl")
						else:
							addword="inaktiv"
							if self.splitpoints==1:
								addword="aktiv"
							if not self.phase==NO_GAME:
								self.nipmsg("PRE_X#BOLD#Splitpoints#BOLD# ist #BOLD#"+addword+"#BOLD#. Wechsel nur durch den "+self.TGAMEADMIN+" moeglich!")

					elif command=="gamespeed":
						if user==self.gameadmin:
							if self.gamespeed==1:
								self.gamespeed=2
								self.nipmsg("PRE_XSpielgeschwindigkeit ist nun #BOLD#schnell.")
							else:
								self.gamespeed=1
								self.nipmsg("PRE_XSpielegeschwindigkeit ist nun #BOLD#normal.")
						else:
							actspeed="normal"
							if self.gamespeed==2:
								actspeed="schnell"
							if not self.phase==NO_GAME:
								self.nipmsg("PRE_XSpielgeschwindigkeit ist #BOLD#"+actspeed+"#BOLD#. Wechsel nur durch den "+self.TGAMEADMIN+" moeglich!")

					elif command=="testing":
						if user==self.gameadmin:
							if self.minplayersold == 0:
								self.minplayersold=self.minplayers
								self.maxplayersold=self.maxplayers
								self.minplayers=3 # default in config will be 5 
								self.maxplayers=24 #default in config will be 12
								self.nipmsg("PRE_XMinimum Spieler=#BOLD#"+str(self.minplayers)+"#BOLD# Maximum Spieler=#BOLD#"+str(self.maxplayers))
							else:
								self.minplayers=self.minplayersold
								self.maxplayers=self.maxplayersold
								self.minplayersold=0
								self.maxplayersold=0
								self.nipmsg("PRE_XMinimum Spieler=#BOLD#"+str(self.minplayers)+"#BOLD# Maximum Spieler=#BOLD#"+str(self.maxplayers))
						else:
							self.nipmsg("PRE_XYou have found a secret :)")

					elif command=="add":
						self.bot.logger.debug("Adding player in phase "+str(self.phase))
						if self.phase==NO_GAME or self.phase==GAME_WAITING: #should work now
						#if self.phase==GAME_WAITING:
							if self.gameadmin: #we have one ;)
								if user==self.gameadmin: #himself
									if len(options) > 1:
										player=options.strip() #Todo channeluserlist	
										# need channeluserlist
										self.add_player(player)
									else:
										self.add_player(user) #just add himself
								else:
									self.add_player(user) # just a player 
							else:
								self.add_player(user) # again maybe we have no admin
						else:
							if self.phase==WAITING_FOR_PLAYERS:
								self.nipmsg("PRE_X"+user+": Einfach \"ich\" rufen!")
							else: #only users join thereself
								if not user in self.players and not user in self.newplayers and self.gameadmin!=user:
									self.nipmsg("PRE_X"+user+" spielt ab der naechsten Runde mit")
									self.newplayers.append(user)
								elif user==self.gameadmin:
									self.nipmsg("PRE_X"+user+": "+self.TGAMEADMIN+" kann nur zwischen den Runden einsteigen")

					elif command=="remove":
						#if self.phase==NO_GAME or self.phase==GAME_WAITING: #Todo removing alltime
						if self.phase!=7: #try if compatible with flow (Todo)
							if self.gameadmin: #we may have one ;)
								if user==self.gameadmin: #himself
									if len(options) > 1:
									#player=string.lower(options[:24].strip()) #truncated and the trailing spaces eliminated 
										player=options[:24].strip() #truncated and the trailing spaces eliminated 
										self.del_player(player) #admin removes player
									else:
										self.del_player(user) #just remove himself 
								else:
									if len(options) == 0: #
										self.del_player(user) # a player
									else:
										self.nipmsg("PRE_X"+user+": Das darf nur der "+self.TGAMEADMIN+" "+str(self.gameadmin))
							else:
								self.del_player(user) # again even if there is no admin
						else:
							self.nipmsg("PRE_X"+user+": Aussteigen geht nur zwischen den Runden.") #obsolete

					elif command=="players":
						#if self.phase==NO_GAME:
						self.show_players()

					elif command=="restartgame":
						if self.gameadmin=="" and self.phase==GAME_WAITING:
							self.new_gameadmin(user)
				
						if self.gameadmin==user and self.phase<2: #test
							self.stop_timer() #needed here due to kick_gameadmin?
	
						if self.phase==GAME_WAITING and user==self.gameadmin:
							if self.player_qty() >= self.minplayers:

								tmpplayers=string.join(self.players," ") # trunc this? or predone?
								if self.gamemaster:
									tmpplayers=self.gamemaster+" "+tmpplayers
								self.init_vars_for_restart()
								self.nipmsg("PRE_GRunde (#BOLD#"+str(self.roundofgame)+"#BOLD#) mit: "+tmpplayers)
								self.phase=WAITING_FOR_QUESTION
								self.nTimerset('TIMEOUT', "end_of_quiz")
								
								if not self.check_nip_buffer(self.gamemaster):
									self.nipmsg("PRE_Q"+str(self.gamemaster)+": Schick' mir die "+self.TNIPQUESTION+"."+"  ~"+str(self.gl_ts)+" Sek. Zeit!#DGREY# (/msg "+self.bot.nickname+" die Frage)") #guess gamemaster might work in all cases instead of user here ;)
									self.bot.sendmsg(self.gamemaster,"Du kannst im "+self.gamechannel+" !resetgame machen, falls du dich vertippt hast. Und nun die NIP-Frage:",self.NIPencoding)
							else:
								self.nipmsg("PRE_GZu wenig Spieler. Mindestens "+str(self.minplayers)+" muessen mitspielen! #BOLD##CCHAR#join")

					elif command=="startgame":
						##### if not self.gamechannel (see check_channel)means there is no game on network!
						if self.phase==NO_GAME:
							if len(user) < self.maxnicklen:
								self.gamechannel=channel #needed for queries which result in a public answer # settint the . gamechannel also means there is a game running in this channel
								self.bot.logger.info("Setting Gamechannel to "+channel)
								self.init_vars()
								self.allscore={}
								self.save_score(True)
								self.nipmsg("PRE_XSpielstand archiviert und geloescht!")
								self.phase=WAITING_FOR_PLAYERS
								
								self.gameadmin=user

								self.nipmsg("PRE_X"+user+": Du bist nun der "+self.TGAMEADMIN+" - Los geht's mit #CCHAR#startgame.")
								self.nipmsg("PRE_XWer moechte an einer Runde "+self.nameofgame+" teilnehmen? (\"\x02ich\x02\" rufen!)")

								self.nTimerset('STARTPHASE',"kick_gameadmin") #in this phase we well do end_of_game after timeout
							else:
								self.nipmsg("PRE_X"+user+": Dein nickname ist zu lang. Maximal "+str(self.maxnicklen)+" Zeichen.")
					
						elif self.phase==WAITING_FOR_PLAYERS and user==self.gameadmin:
							if self.player_qty() >= self.minplayers:
								self.phase=WAITING_FOR_QUESTION
								random.shuffle(self.players)
								self.gamemaster=random.choice(self.players)
								if self.gamemaster in self.players:
									self.players.remove(self.gamemaster) # due to new flow at this point needed, too (because he knows the answer)
								self.bot.logger.debug("Random choice setting gamemaster:"+self.gamemaster)
								self.nTimerset('TIMEOUT', "end_of_quiz")
								if not self.check_nip_buffer(self.gamemaster):
									self.nipmsg("PRE_Q"+self.gamemaster+": Schick' mir die "+self.TNIPQUESTION+". ~"+str(self.gl_ts)+" Sek. Zeit! #DGREY# (/msg "+self.bot.nickname+" die Frage)")
									self.bot.sendmsg(self.gamemaster, "Du kannst im "+self.gamechannel+" !resetgame machen, falls du dich vertippt hast. Und nun die NIP-Frage:",self.bot.getConfig("enncoding","UTF-8"))
						
							else:
								self.nipmsg("PRE_X"+self.gameadmin+": Zuwenig Mitspieler! Mindestens "+str(self.minplayers)+" muessen mitspielen. #BOLD#\"ich\" rufen!")
			
						elif self.gameadmin=="": #Auto_new_gameadmin
							self.new_gameadmin(user)

					elif command=="abortgame": #now "end of game"
						if self.gameadmin=="" and self.phase!=NO_GAME:
							self.new_gameadmin(user)
	
						if self.gameadmin==user and self.phase > 0:
						#if len(self.uservoted_end)< 1:
							if self.abortcnt < 1:
								self.nipmsg("PRE_X"+self.gameadmin+": Um das Spiel tatsaechlich zu beenden, bitte noch einmal!")
								self.abortcnt=1
							else: # end the game
								for player in self.players:
									self.uservoted_end.append(player)
								self.votedEnd=1
								adminVote=True #
								self.vote_for_end(user,adminVote)
						else:
							if not self.phase==NO_GAME:
								self.nipmsg("PRE_XAbbruch nur durch den "+self.TGAMEADMIN+" "+self.gameadmin+" moeglich, versuche #CCHAR#vote", channel)
			
					elif command=="resetgame":
						if self.phase==WAITING_FOR_QUIZMASTER_ANSWER or self.phase==WAITING_FOR_ANSWERS:
							if self.gameadmin==user or self.gamemaster==user:
								self.resetcnt+=1 #todo block more than x resets....
								ppoints=self.resetcnt * 2
								if self.resetcnt>1:
									self.nipmsg("PRE_H"+user+": Auf ein Neues! #BOLD#Punktabzug: -"+str(ppoints))
									self.bot.sendmsg(self.gamemaster,"Deine NIP-Frage:")
									self.add_allscore(user,int(ppoints*-1))
									self.reset_game()
								else:
									ppoints=1
									self.nipmsg("PRE_H"+user+": Auf ein neues! #BOLD#Naechstemal Punktabzug!")
									self.bot.sendmsg(self.gamemaster,"Deine NIP-Frage:")
									#self.add_allscore(user, -1)
									self.reset_game()
							else:
								self.nipmsg("PRE_H NOP")
						else:
							self.nipmsg("PRE_H NOP")

					elif command=="scores":
						pointlen=0
						if len(self.allscore):
							pointlen=len(str(max(self.allscore.values())))
						SCOREHEAD="#UNDERLINE#_-=Punkteverteilung=-"+self.create_ws(pointlen-1+self.maxnicklen-12)+"_#UNDERLINE##DGREY#"+" Runde:"+str(self.roundofgame)
						self.nipmsg("PRE_S"+SCOREHEAD, channel)
						if len(self.allscore):	
							points=self.allscore.values()
							points.sort()
							points.reverse()
							players=self.allscore.keys()
							for point in points:
								for player in players:
									if self.allscore[player]==point:
										pword="Punkte"
										if point==1:
											pword="Punkt"
										splayer=player+self.create_ws(self.maxnicklen)
										#spoints=str(point)+self.create_ws(12+len(str(point)))[:pointlen]
										spoints=str(point)+self.create_ws(pointlen-len(str(point)))
										self.nipmsg("PRE_S"+splayer[:self.maxnicklen]+"  "+spoints+ " "+pword, channel)
										players.remove(player)
										break; #

					elif command=="rules":
					     self.nipmsg("PRE_H"+self.NIPRULES, channel)

					elif command=="status":
						result=self.game_status(channel)
						if self.gamechannel!=channel and self.gamechannel!="":
							self.nipmsg("PRE_GEs wird bereits gespielt! #BOLD#/join "+self.gamechannel, channel)
						if self.gamechannel==channel or self.gamechannel=="":
							self.nipmsg("PRE_G"+result, channel)

					elif command=="place":
						self.show_user_in_halloffame(channel,user,options)

					elif command=="halloffame":
						if self.hof==None:
							self.bot.logger.error("HoF empty, file permissions? Maybe it is just new.")
						else:
							loption=options.split(" ")[0]
							try:
								loption=int(loption)
							except:
								if loption=="":
									loption=0
							if type (loption)==int:
								self.show_halloffame(channel,user,int(loption))
							else:
								self.nipmsg("PRE_Z Versuche #BOLD##CCHAR#place#BOLD# oder gib die Seitenzahl an.",channel)
					
					elif command=="favorits":
						if len(self.fav.player)>0:
								loption=options.split(" ")[0]
								if loption:
									user=loption
								favOut=user+"#BOLD# <-#BOLD#"
								favlist=self.fav.getlist(user)
								if favlist:
									for player,val in self.fav.getlist(user):
										favOut+="#DGREY#("+player+":#NORM#"+str(val*3)+"#DGREY#)" #
									self.nipmsg("PRE_Z"+favOut,channel)
								else:
									self.nipmsg("PRE_ZNOP",channel)


	def show_halloffame(self, channel, user, pagekey=None):
		pointlen=len(str(self.hof[0][1])) # for building the length in formatted output
		expand=""
		if pointlen>3:
			expand=self.create_ws(pointlen-3) #three is (min) default
		expand=expand+self.create_ws(self.maxnicklen-12) #well maxnicklen=12 IS default
		HOFHEAD="_-= Hall of Fame =-"+expand+"_"
		self.nipmsg("PRE_Z#UNDERLINE#"+HOFHEAD+"#UNDERLINE#", channel)
		if len(self.hof):
			first=self.hof_show_max_player*pagekey+1
			pcnt=0
			for i in range(self.hof_show_max_player):
				iplace=i+first-1 #index 0 base
				if iplace >= len(self.hof):
					break
				place=str(iplace+1)+".     " #we do not have placement on zeros....
				nick=self.hof[iplace][0]+self.create_ws(self.maxnicklen)
				allpoints=str(self.hof[iplace][1])+"         " 
				self.nipmsg("PRE_Z"+place[:3]+" "+nick[:self.maxnicklen]+" "+str(allpoints), channel)


	def show_user_in_halloffame(self, channel, user, options):
		player=options[:self.maxnicklen].strip()
		try:
			player=int(player)
		except:
			pass
		if not player:
			player=user
		if not type(player)==int:
			isin=self.isinhof(player,"nocases")#just a bool
			if not isin:
				self.nipmsg("PRE_Z"+player+" nicht in der #BOLD#Hall of Fame#BOLD# gefunden! Eine Schande!", channel)
			else:
				place=isin[0]+".    "
				player=isin[1]+self.create_ws(self.maxnicklen) #easier way to create whitespaces (and own tabs)?
				allpoints=isin[2]
				self.nipmsg("PRE_Z"+place[:3]+player[:self.maxnicklen]+" "+str(allpoints), channel)
		else: #we got just an integer, how plain!
			hplace=int(player)
			place=str(hplace)+".            " #could be depending on len(max_hof_players)...
			player=self.hof[hplace-1][0]+self.create_ws(self.maxnicklen)
			allpoints=self.hof[hplace-1][1]
			self.nipmsg("PRE_Z"+place[:3]+player[:self.maxnicklen]+" "+str(allpoints), channel)


	def create_ws(self, qty):
		if qty<1:
			return ""
		ws=[]
		for i in range(qty):
			ws.append(' ')
		return ''.join(ws)
	    # one line? anyone

	def reset_game(self):
		self.bot.logger.debug("Reset game in phase="+str(self.phase))
		self.resetcnt+=1
		#self.init_vars_for_restart() #due to cheatprotect this will be problematic at this point
		self.question=""
		self.answers={}
		self.answeruser={}
		self.additional_info=None
		#self.score={} #not here!
		#self.scores={} #dto
		self.guessed=[]
		self.nTimerset('TIMEOUT', "end_of_quiz")
		self.phase=WAITING_FOR_QUESTION
		self.bot.logger.debug("Game resetted")


	def userKicked(self, kickee, channel, kicker, message):
		player=kickee
		playerkicker=kicker
		#remove gamemaster and or gameadmin from game if kicked
		if self.gamechannel==channel:
			if self.gameadmin==player:
				self.kick_gameadmin()
		if self.gamemaster==player:
			self.del_player(player)
			#well to kick the actual! gamemaster while waiting for his input is evil, and will be punished with score -3 ;)
			if self.phase==WAITING_FOR_QUESTION or self.phase==WAITING_FOR_QUIZMASTER_ANSWER:
				self.nipmsg("PRE_P"+kicker+":Den "+self.TGAMEMASTER+" gerade #BOLD#jetzt#BOLD# zu kicken ist boese, 3 Punkte Abzug!")
				self.add_allscore(str(playerkicker),-3)
			self.phase=GAME_WAITING #
	
	def joined(self, channel):
		#so check self.gamechannel on !start
		#on join will throw this msg all confed channels
		if self.check_channel(channel,None):
			self.nipmsg("PRE_HDave, moechtest du mit mir hier im "+channel+" spielen? #CCHAR#startgame",channel)


	def userJoined(self, user, channel):
		user=user.split("!")[0]
		if not user in self.players and user!=self.gamemaster:
			statusinfo=self.game_status(channel, user)
			if self.gamechannel==channel:
				self.bot.notice(user, "Hi,"+user+"! "+statusinfo)
			else:
				if self.gamechannel!="":
					self.bot.notice(user, "Hi,"+user+"! /join "+self.gamechannel+" fuer eine Runde NIP!")
				else:
					self.bot.notice(user, "Hi,"+user+"! "+statusinfo)

	def game_status(self, channel=None, player=None):
		#set and return them to user just on request. notice on join, or command status (translation in mind)
		ustat=""
		uadd=""
		stat=""
		nt=""
		ujoin=""
		status=self.phase
		if player in self.players:
			uadd=" Du bist noch dabei."
		if self.gamemaster==player:
			uadd=" Du bist "+self.TGAMEMASTER
		if self.gameadmin==player:
			uadd=" Du bist "+self.TGAMEADMIN
		if self.gameadmin==player and self.gameadmin==player:
			uadd=" Du bist "+self.TGAMEADMIN+" und "+self.TGAMEMASTER
		if self.gl_ts >= 1:
			nt="#DGREY# Noch ~"+str(self.gl_ts)+" Sek."
		else:
			nt="#DGREY# ~~~" #no timeouts running
		if len(uadd)==0:
			ujoin="Zum Mitspielen #CCHAR#join."
		if status==NO_GAME and not channel in self.channels:
				c=""
				for c in self.channels:
					c=c+" "
				stat="Es laeuft kein NIP.#CCHAR#startgame in "+str(c)+" moeglich"
				ustat=stat
		elif status==NO_GAME:
			stat="Es laeuft kein NIP. #BOLD##CCHAR#startgame#BOLD# startet ein Neues."
			ustat=stat
			stat=stat+nt
		elif status==WAITING_FOR_PLAYERS:
			stat="NIP-Runde laeuft. Wer teilnehmen moechte einfach #BOLD#\"ich\"#BOLD# rufen!"
			ustat=stat+uadd
			stat=stat+nt
		elif status==WAITING_FOR_QUESTION or status==WAITING_FOR_QUIZMASTER_ANSWER:
			gm=""
			if self.gamemaster:
				gm="#BOLD#"+self.gamemaster+"#BOLD#"
			stat="NIP-Runde laeuft. Wir warten auf den "+self.TGAMEMASTER+" "+gm
			ustat=stat+ujoin+uadd
			stat=stat+nt
		elif status==WAITING_FOR_ANSWERS:
			stat="NIP-Runde laeuft. Wir warten auf die \"falschen\" Antworten."
			ustat=stat+ujoin+uadd
			stat=stat+nt
		elif status==QUIZ:
			stat="NIP-Runde laeuft. QUIZ-Time! Warten auf die Punkteverteilung."
			ustat=stat+ujoin+uadd
			stat=stat+nt
		elif status==GAME_WAITING:
			astat=""
			if self.gameadmin=="":
				astat=" #BOLD##CCHAR#restartgame sollte helfen.#BOLD#"
			stat="NIP pausiert."+astat+" Mitspielen einfach mit #BOLD##CCHAR#join#BOLD#"
			ustat=stat
			stat=stat+nt
		rv=""
		if player:
			if ustat.count("#CCHAR#"):
				ustat=ustat.replace("#CCHAR#","!") # todo self.cchar (unicode? (notice...))
			for color in self.colors:
				if ustat.count(color):
					val=self.colors.get(color,"")
					ustat=ustat.replace(color, val)
			rv=ustat
		else:
			rv=stat
	
		return rv
	
	
	def msg(self, user, channel, msg):
		msg=msg.replace("%","")
		user=user.split("!")[0]
		if channel == self.bot.nickname:
			if self.phase==WAITING_FOR_QUESTION and user==self.gamemaster:
				self.question=msg
				self.bot.sendmsg(user, "Und jetzt die richtige Antwort")
				self.phase=WAITING_FOR_QUIZMASTER_ANSWER
				self.nTimerset(self.gl_ts+24, "end_of_quiz") # we got the question, so the player is alive - give him again a little bit more time

			elif self.phase==WAITING_FOR_QUIZMASTER_ANSWER and user==self.gamemaster:
				self.answers[user]=msg
				self.nTimerset('ANSWER_TIME', "end_of_answertime")
				self.nipmsg("PRE_Q"+self.TNIPQUESTION+" ist: #BOLD#"+self.question)
				self.nipmsg("PRE_ASchickt mir eure #BOLD#\"falschen\"#BOLD# Antworten! ~"+str(self.gl_ts)+" Sek. Zeit! #DGREY#  (/msg "+self.bot.nickname+" eure Antwort)")
				self.phase=WAITING_FOR_ANSWERS

				#remove gamemaster from game, because he knows the answer
				if self.gamemaster in self.players: #sometimes he is not in before 
				   self.players.remove(self.gamemaster)
				
				self.bot.sendmsg(self.gamemaster, "Zusatzinformation zur Frage einfach hinterschicken oder weglassen") #
				self.bot.logger.debug("Sent an additional info (tip) request.")
				

			elif (self.phase==WAITING_FOR_ANSWERS or self.phase==QUIZ) and user==self.gamemaster and not self.additional_info:
				self.additional_info=msg

			elif self.phase==WAITING_FOR_ANSWERS and not user in self.answers and user in self.players:
				if msg[0]!="!": # we understand some commands in query now oO
					self.answers[user]=msg
					if len(self.answers) == len(self.players)+1: #+gamemaster
						self.end_of_answertime()
		else:
			#if string.lower(msg)[:3]=="ich" and self.phase==WAITING_FOR_PLAYERS:
			if self.gamechannel==channel:
				if self.phase==WAITING_FOR_PLAYERS and user!=self.bot.nickname: #add player with "ich" in first 42characters while startphase
					if len(string.lower(msg).split("ich")[:42]) > 1: # parses *ich* just do that on WAITING_FOR_PLAYERS (startphase)
						if len(string.lower(msg).split("nicht")[:24]) > 1: #yag
							if not user in self.players:
								self.nipmsg("PRE_H/kick "+user)
							else:
								self.nipmsg("PRE_H"+user+": Wer nicht will hat schon ;-)")
								self.players.remove(user)
						else:
							#if string.lower(msg)[:3]=="ich": 
							if not (user in self.players or user==self.gamemaster):
								if self.check_maxplayer():
								#self.players.append(user[:12]) #max len of nick maybe dyn in future
									self.add_player(user)
									text=""
									for item in self.players:
										text=text+item+", "
									text=text[:-2]+"."
								self.show_players()
				elif self.phase==QUIZ and user in self.players and not user in self.guessed and user!=self.gamemaster and user!=self.gamemasterold:
					try:
						gmaster=self.gamemaster
						if gmaster=="":
							gmaster=self.gamemasterold
						if(self.answeruser[int(msg)]==gmaster):
							if user in self.score:
								#self.score[user]=self.score[user]+1
								self.score[user]+=1 #shorter ;)
								if self.splitpoints:
									self.scores[user]=self.scores[user]+(" +1*") #
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
								#Favorits
								player=self.answeruser[int(msg)]#put that in .add oO
								self.fav.add(player, user)
								self.fav.sort(player)
								
								if self.splitpoints:
									self.scores[self.answeruser[int(msg)]]=self.scores[self.answeruser[int(msg)]]+" 3<-"+user #
							else:
								self.score[self.answeruser[int(msg)]]=3
								#Favorits
								player=self.answeruser[int(msg)]
								self.fav.add(player, user)
								self.fav.sort(player)
								
								if self.splitpoints:
									self.scores[self.answeruser[int(msg)]]=" 3<-"+user
						self.guessed.append(user)
					#except ValueError:
					except: #trying to catch all
						pass
					if len(self.guessed) == len(self.players):
						self.end_of_quiz()

	def nip_hof(self,hofdataf,action):
		self.bot.logger.debug("HoF data "+action)
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
				self.bot.logger.debug("HoF filled")
				return hof #better way to sort a list from dict?
	
			except IOError:
				self.bot.logger.error("Could not open HoF Data "+hofdataf)
				try:
					self.bot.logger.debug("Creating "+hofdataf)
					if (not os.path.isdir(os.path.dirname(hofdataf))):
						os.makedirs(os.path.dirname(hofdataf))
					hofFile = open(hofdataf, "w")
					hofFile.close()
					self.bot.logger.debug("File created "+hofdataf)
				except IOError:
					self.bot.logger.error("Could not create "+hofdataf+str(IOError))
	
		self.bot.logger.debug("HoF Data ready to use")
		if action=="write":
			self.bot.logger.debug("Writing HOF to file "+hofdataf)
			#ts=time.strftime('%Y%m%d_%S%M%H')
			ts=time.strftime('%Y%m%d_%H%M%S')
			bfile=hofdataf+"."+ts
			self.bot.logger.info("Creating HoF backup "+bfile)
			try:
				shutil.copyfile(hofdataf, bfile)
			except:
				self.bot.logger.error("Couldn't create "+bfile+" "+str(IOError))	
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
				self.bot.logger.debug("Could not open or write to "+hofdataf)

	################################################################
	
	def nip_hof_update(self, hofdataf):
		if len(self.allscore):
			points=self.allscore.values()
			players=self.allscore.keys()
			for player in players:
				point=self.allscore[player]
				updateplayer=self.isinhof(str(player))
				if updateplayer:
					newscore=updateplayer[2]+point
					self.hof[int(updateplayer[0])-1]=player,newscore
				else:
					newscore=self.allscore[player]
					self.hof.append("dim") #d
					self.hof[len(self.hof)-1]=player,newscore
	 
		#hmm let's write and "reload" HoF here, so we just call nip_hof_update when game ends with "aborted" and TODO: termination hook... perhaps
		if self.data_update_needed:
			self.nip_hof(hofdataf,"write")
			self.hof=self.nip_hof(hofdataf,"read")
			self.bot.logger.debug("HoF updated")
		else:
			self.bot.logger.debug("HoF no updated needed")
	
	def isinhof(self, player, nocases=None):
		placecnt=0
		if self.hof==None:
			return False
		for hplayer, val in self.hof:
			placecnt+=1
			
			if nocases==None:
				if player==hplayer:
					return str(placecnt),hplayer, val# return breaks
			else:
				if player.lower()==hplayer.lower():
					return str(placecnt),hplayer, val# return breaks
		return False
	

	def save_score(self,force=None):#todo see exithook
		#saving game scoring table for another HoF statistics, and actScoreTable to be restored after bot restart
		if len(self.allscore.values()) > 0: #no need to save empty scoretable
			self.bot.logger.debug("Saving score table")
			ts=time.strftime('%Y%m%d_%H%M%S')
			scorefile=self.nipdatadir+"NIPScore."+ts
			try:
				sf=open(scorefile, "w")
				sf.write("GameStartTime="+str(self.starttime)+"\nGameStopTime="+str(time.strftime('%Y/%m/%d %H:%M:%S'))+"\nNo. of Rounds="+str(self.roundofgame)+"\n")
				for key, value in self.allscore.items():
					sf.write(str(key)+"="+str(value)+"\n")
				sf.close()
			except IOError:
				self.bot.logger.error("IOError on "+scorefile)
			finally:
				sf.close()
		else:
			self.bot.logger.debug("Did not store empty scoretable")
		if self.data_update_needed or force:
				scorefile=self.nipdatadir+"NIPactScoreTable"
				self.bot.logger.debug("Saving "+scorefile+" update_need:"+str(self.data_update_needed)+" Force:"+str(force))
				try:
					sf=open(scorefile, "w")
					pickle.dump(self.allscore, sf)
					sf.close()
				except IOError:
					self.bot.logger.error("IOError on "+scorefile)
				finally:
					sf.close()
		else:
			self.bot.logger.debug("No need to update ActScoreTable")


	def load_score(self):
		scorefile=self.nipdatadir+"NIPactScoreTable"
		try:
			sf=open(scorefile, "r")
			self.allscore=pickle.load(sf)
			sf.close()
		except IOError:
			self.bot.logger.error("IOError on "+scorefile)