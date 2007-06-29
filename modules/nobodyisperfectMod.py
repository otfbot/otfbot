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

import random, string
import chatMod

ANSWER_TIME=90
QUIZ_TIME=60
TIMEOUT=300 #idle time until game stops

#game phases
NO_GAME=0
WAITING_FOR_PLAYERS=1
WAITING_FOR_QUESTION=2
WAITING_FOR_QUIZMASTER_ANSWER=3
WAITING_FOR_ANSWERS=4
QUIZ=5

def mypass():
	pass

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.init_vars()
		self.timer=self.bot.scheduler.callLater(1, mypass) #XXX: why is this needed?
		self.allscore={}

	def init_vars(self):
		self.phase=NO_GAME
		self.players=[]
		self.gameadmin="" #needed for deciding when to start the game
		self.gamemaster="" #different for each round.
		#self.gamechannel="" #this is not multichannel compatible!
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.guessed=[] #users, which already have guessed
		self.additional_info=None

	def init_vars_for_restart(self):
		self.question=""
		self.answers={}
		self.answeruser={} #usernames(!) for the numbers
		self.score={}
		self.guessed=[] #users, which already have guessed
		self.additional_info=None

		#each player will be gamemaster, in order
		self.players.append(self.gamemaster)
		self.gamemaster=self.players[0]
		self.players=self.players[1:]

	def end_of_answertime(self):
		if self.timer and self.timer.active():
			self.timer.cancel()
		self.phase=QUIZ
		count=1
		self.bot.sendmsg(self.gamechannel, "Die Frage ist: "+self.question, self.bot.getConfig("encoding", "UTF-8"))
		self.bot.sendmsg(self.gamechannel, "Moegliche Antworten (eine waehlen)", self.bot.getConfig("encoding", "UTF-8"))
		users=self.answers.keys()
		random.shuffle(users)
		for user in users:
			self.bot.sendmsg(self.gamechannel, str(count)+". "+self.answers[user], self.bot.getConfig("encoding", "UTF-8"))
			self.answeruser[count]=user
			count=count+1
		self.timer=self.bot.scheduler.callLater(QUIZ_TIME, self.end_of_quiz)

	def end_of_quiz(self):
		self.phase=NO_GAME
		if self.timer and self.timer.active():
			self.timer.cancel()
		self.bot.sendmsg(self.gamechannel, "===Ende der Runde===")
		correct="Die richtige Antwort war: "+self.answers[self.gamemaster]
		if self.additional_info:
			correct=correct+" ("+self.additional_info+")"
		self.bot.sendmsg(self.gamechannel, correct, self.bot.getConfig("encoding", "UTF-8"))
		if len(self.score):
			#show who gave which answer.
			text=""
			for num in self.answeruser:
				if self.answeruser[num]==self.gamemaster:
					text+="**"+str(num)+"** war von "+self.answeruser[num]+", "
				else:
					text+=str(num)+" war von "+self.answeruser[num]+", "
			text=text[:-2]+"."
			self.bot.sendmsg(self.gamechannel, text, self.bot.getConfig("encoding", "UTF-8"))
			#Points.
			#self.bot.sendmsg(self.gamechannel, "=== Punkte ===", self.bot.getConfig("encoding", "UTF-8"))
			for player in self.score:
				self.bot.sendmsg(self.gamechannel, player+": "+str(self.score[player])+ " Punkte", self.bot.getConfig("encoding", "UTF-8"))
			#set in allscore
			for user in self.score:
				if user in self.allscore.keys():
					self.allscore[user]+=self.score[user]
				else:
					self.allscore[user]=self.score[user]


	def command(self, user, channel, command, options):
		user=string.lower(user.split("!")[0])
		if channel!=self.bot.nickname:
			if command=="remove":
				if self.phase==NO_GAME:
					if len(msg)>7 and user==self.gameadmin: #XXX: 7 because command has no trailing whitespace? - 8 because of the whitespace after !remove
						player=string.lower(msg[8:])
					else:
						player=user
					if player in self.players:
						self.players.remove(player)
						self.bot.sendmsg(channel, "Spieler "+player+" aus der Runde entfernt.")
					else:
						self.bot.sendmsg(channel, "Spieler "+player+" spielt nicht mit.")
				else:
					self.bot.sendmsg(channel, "Spieler koennen nur zwischen 2 Runden entfernt werden")

			elif command=="add":
				if self.phase==NO_GAME:
					self.players.append(user)
					self.bot.sendmsg(channel, user+" spielt jetzt mit.")
					#random.shuffle(self.players)
				else:
					self.bot.sendmsg(channel, "Spieler koennen nur zwischen 2 Runden hinzugefuegt werden")

			elif command=="restartgame":
				if self.phase==NO_GAME and user==self.gameadmin:
					self.bot.sendmsg(channel, "Eine neue Runde startet, Spieler bleiben gleich!")
					self.init_vars_for_restart()
					self.phase=WAITING_FOR_QUESTION
					self.bot.sendmsg(channel, user+": /msg mir die Frage.", self.bot.getConfig("encoding", "UTF-8"))
					self.timer=self.bot.scheduler.callLater(TIMEOUT, self.end_of_quiz)
					
			elif command=="startgame":
				if self.phase==NO_GAME:
					self.init_vars()
					self.gameadmin=user
					self.bot.sendmsg(channel, "Wer moechte an einer Runde \"Nobody is Perfect\" teilnehmen?(laut \"ich\" rufen!)")
					self.bot.sendmsg(channel, self.gameadmin+": Zum starten nocheinmal !startgame sagen.", self.bot.getConfig("encoding", "UTF-8"))
					self.phase=WAITING_FOR_PLAYERS
					self.gamechannel=channel #needed for queries which result in a public answer
					self.timer=self.bot.scheduler.callLater(TIMEOUT, self.end_of_quiz)
				elif self.phase==WAITING_FOR_PLAYERS and user==self.gameadmin:
					if self.timer:
						self.timer.cancel()
					if len(self.players) >2:
						self.phase=WAITING_FOR_QUESTION
						random.shuffle(self.players)
						self.gamemaster=random.choice(self.players)
						self.bot.sendmsg(channel, self.gamemaster+": /msg mir die Frage.", self.bot.getConfig("encoding", "UTF-8"))
						self.timer=self.bot.scheduler.callLater(TIMEOUT, self.end_of_quiz)
					else:
						self.bot.sendmsg(channel, self.gameadmin+": zu wenig Spieler!", self.bot.getConfig("encoding", "UTF-8"))
			elif command=="abortgame":
				self.end_of_quiz()

			elif command=="score":
				if len(self.allscore):
					self.bot.sendmsg(channel, "=== Punkte ===", self.bot.getConfig("encoding", "UTF-8"))
					points=self.allscore.values()
					points.sort()
					points.reverse()
					players=self.allscore.keys()
					for point in points:
						for player in players:
							if self.allscore[player]==point:
								self.bot.sendmsg(channel, player+": "+str(point)+ " Punkte", self.bot.getConfig("encoding", "UTF-8"))
								players.remove(player)
								break;


	def msg(self, user, channel, msg):
		user=string.lower(user.split("!")[0])
		if channel == self.bot.nickname:
			if self.phase==WAITING_FOR_QUESTION and user==self.gamemaster:
				self.timer.cancel()
				self.question=msg
				self.bot.sendmsg(user, "Und jetzt die richtige Antwort")
				self.phase=WAITING_FOR_QUIZMASTER_ANSWER
				self.timer=self.bot.scheduler.callLater(TIMEOUT, self.end_of_quiz)

			elif self.phase==WAITING_FOR_QUIZMASTER_ANSWER and user==self.gamemaster:
				self.timer.cancel()
				self.answers[user]=msg
				self.bot.sendmsg(self.gamechannel, "Die Frage ist: "+self.question, self.bot.getConfig("encoding", "UTF-8"))
				self.bot.sendmsg(self.gamechannel, "/msg mir eure Antworten.", self.bot.getConfig("encoding", "UTF-8"))
				self.phase=WAITING_FOR_ANSWERS
				self.timer=self.bot.scheduler.callLater(ANSWER_TIME, self.end_of_answertime) #TIMEOUT

				#remove gamemaster from game, because he knows the answer
				self.players.remove(self.gamemaster)
				self.bot.sendmsg(self.gamemaster, "Zusatzinformation fuer nach dem Quiz(wenn nicht gewuenscht, einfach freilassen):")

			elif (self.phase==WAITING_FOR_ANSWERS or self.phase==QUIZ) and user==self.gamemaster and not self.additional_info:
				self.additional_info=msg

			elif self.phase==WAITING_FOR_ANSWERS and not user in self.answers and user in self.players:
				self.answers[user]=msg
				if len(self.answers) == len(self.players)+1: #+gamemaster
					if self.timer and self.timer.active():
						self.timer.cancel()
					self.end_of_answertime()
		else:
			if string.lower(msg)[:3]=="ich" and self.phase==WAITING_FOR_PLAYERS:
				if not (user in self.players or user==self.gamemaster):
					self.players.append(user)
					text=""
					for item in self.players:
						text=text+item+", "
					text=text[:-2]+"."
					self.bot.sendmsg(channel, str(len(self.players))+" Teilnehmer: "+text, self.bot.getConfig("encoding", "UTF-8"))
			elif self.phase==QUIZ and user in self.players and not user in self.guessed and user!=self.gamemaster:
				try:
					if(self.answeruser[int(msg)]==self.gamemaster):
						if user in self.score:
							self.score[user]=self.score[user]+1
							#self.bot.sendmsg(self.gamechannel, user+" bekommt 1 Punkt", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
						else:
							self.score[user]=1
							#self.bot.sendmsg(self.gamechannel, user+" bekommt 1 Punkt", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
					elif(self.answeruser[int(msg)]==user):
						#to select the own answer gives 0 points
						pass
					else:
						if(self.answeruser[int(msg)] in self.score):
							self.score[self.answeruser[int(msg)]]=self.score[self.answeruser[int(msg)]]+3
							#self.bot.sendmsg(self.gamechannel, self.answeruser[int(msg)]+" bekommt 3 Punkte", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
						else:
							self.score[self.answeruser[int(msg)]]=3
							#self.bot.sendmsg(self.gamechannel, self.answeruser[int(msg)]+" bekommt 3 Punkte", self.bot.getConfig("encoding", "UTF-8")) #DEBUG
					self.guessed.append(user)
				except ValueError:
					pass
				if len(self.guessed) == len(self.players):
					self.end_of_quiz()
