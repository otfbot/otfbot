import random
import unittest

CARD_1000="1"
CARD_2000="2"
CARD_5000="5"
CARD_ZERO="Z"
class Messages:
	NEW_GAME="Neues Spiel gestartet. Zum teilnehmen !ich sagen."
	USER_JOINED="%s spielt jetzt mit."
	USER_PARTED="%s spielt jetzt nicht mehr mit."
	CANNOT_START="Mindestens 2 Spieler noetig"
	GAME_STARTED="Spiel gestartet."
	YOUR_TURN="%s ist dran. Ich wuerfle fuer ihn einen Gegner aus ..."
	VICTIM_CHOOSEN="%s zahl deine Schulden!"
	DOES_NOT_HAVE_ENOUGH="Du moechtest %sx %s legen, du hast aber nur %sx %s!"
	PAYED="%s hat %s Karten auf den Tisch gelegt."
	ACCEPT="%s akzeptiert die Zahlung."
	GOT="Du hast %sx 5000, %sx 2000, %sx 1000 und %s Blueten bekommen."
	DOUBT="%s zweifelt dass da genug Geld liegt um deine Schulden zu begleichen."
	DICE="%s wuerfelt, und das Ergebnis ist %s"
	MONEY_CORRECT="Das Geld stimmt genau!"
	MONEY_TOOLITTLE="Das Geld ist zu wenig. Willst du mich verarschen?!"
	MONEY_TOOMUCH="%s000 ist also mehr als genug Geld. Als Strafe fuer sein Misstrauen muss %s den Betrag nocheinmal zurueckzahlen."
	CARLOTTA="Zur Entschaedigung bekommt %s eine Karte aus Tante Carlottas Sparstrumpf. Es ist ein %s."
	CARLOTTA_EMPTY="Der Sparstrumpf ist jetzt leider leer."
	PAYBACK="%s zahlt %s000 an %s."
	LOSE_PAYBACK="%s muesste %s000 zahlen, hat aber nur Karten im Wert von %s000. Seine/Ihre restlichen Karten bekommt %s."
	LOSE="%s hat verloren und scheidet aus dem Spiel aus."
	def get(self, msg_id):
		"""simple dummy function for when the constants contain the final string"""
		return msg_id
class DoesNotHaveException(Exception):
	pass
class User:
	def __init__(self, nick):
		self.nick=nick
		self.cards={'1': 4, '2': 2, '5': 1, 'Z': 2}
	def getCards(self, cards):
		for card in cards.keys():
			self.cards[card]+=cards[card]
	def giveCards(self, cards):
		for card in cards.keys():
			if self.cards[card] < cards[card]:
				#if the exception occurs, no money is given!
				raise DoesNotHaveException(card)
		for card in cards.keys():
			self.cards[card]-=cards[card]
	def __str__(self):
		return self.__unicode__()
	def __unicode__(self):
		return self.nick
	def __eq__(self, other):
		if type(other)==str:
			return self.nick==other
		return self.nick == other.nick

class userTestCase(unittest.TestCase):
	def testGive(self):
		self.user=User("user")
		self.user.giveCards({'1': 1, 'Z': 2})
		self.assertEquals(self.user.cards['1'], 3)
		self.assertEquals(self.user.cards['Z'], 0)
	def testGiveDoesNotHave(self):
		raised_exception=False
		self.user=User("user")
		try:
			self.user.giveCards({'Z': 3, '1': 1})
		except DoesNotHaveException, e:
			self.assertEquals(e.message, 'Z')
			raised_exception=True
		self.assertTrue(raised_exception)
	def testGetCards(self):
		self.user=User("user")
		self.user.getCards({'1': 5})
		self.assertEquals(self.user.cards['1'], 9)
		raised_exception=False
		try:
			self.user.giveCards({'1': 7})
		except DoesNotHaveException, e:
			raised_exception=True
		self.assertTrue(not raised_exception)


def string2cards(input):
	cards={}
	cards['Z']=input.count('Z')
	cards['1']=input.count('1')
	cards['2']=input.count('2')
	cards['5']=input.count('5')
	return cards

def string2worth(input):
	cards=string2cards(input)
	return worth(cards)
def worth(cards):
	return cards['1']+2*cards['2']+5*cards['5']
def string2numCards(input):
	cards=string2cards(input)
	return cards['1']+cards['2']+cards['5']+cards['Z']
def char2word(char):
	if char=="1":
		return "1000er"
	elif char=="2":
		return "2000er"
	elif char=="5":
		return "5000er"
	elif char=="Z":
		return "Zero Mille"

class helpersTestCase(unittest.TestCase):
	def testString2Worth(self):
		self.assertEquals(string2worth("1Z5Z2"),8)
	def testString2Cards(self):
		self.assertEquals(string2cards("1Z5Z2"), {'1': 1, '2': 1, '5': 1, 'Z': 2})
	def testString2Worth(self):
		self.assertEquals(string2worth("1Z5Z2"), 8)

class State:
	def __init__(self, game):
		self.game=game
	def input(self, user, command, options):
		pass

class PaybackState(State):
	def __init__(self, game, debt):
		self.game=game
		self.debt=debt
		self.defect_choice=False
	def input(self, user, command, options):
		if user==self.game.userlist[self.game.current_user] and command == "zahl":
			if self.debt > string2worth(options):
				return ("Du musst Karten im Gesammtwert von %s000 geben."%self.debt, False)
			if self.debt <= string2worth(options):
				try:
					ret=[(self.game.messages.get(Messages.PAYBACK)%(self.game.userlist[self.game.current_user], string2worth(options), self.game.victim), True)]
					self.game.userlist[self.game.current_user].giveCards(string2cards(options))
					if len(self.game.carlotta_cards) > 0:
						carlotta_card=random.choice(self.game.carlotta_cards)
						if self.defect_choice:
							carlotta_card=self.defect_choice
						self.game.userlist[self.game.current_user].getCards({carlotta_card: 1})
						self.game.carlotta_cards.remove(carlotta_card)
						ret+=[(self.game.messages.get(Messages.CARLOTTA)%(self.game.userlist[self.game.current_user], char2word(carlotta_card)), True)]
					if len(self.game.carlotta_cards) == 0:
						ret+=[(self.game.messages.get(Messages.CARLOTTA_EMPTY), True)]
					self.game.execute_next=True
					self.game.setState(SelectPlayerState(self.game))
					return ret
				except DoesNotHaveException, e:
					return ("Du hast versucht eine %s karte zu legen, die du nicht hast."%char2word(e.message), False)


class LostState(State):
	def __init__(self, game, player, last_cards_to):
		self.game=game
		self.player=self.game.userlist[self.game.userlist.index(player)]
		self.last_cards_to=self.game.userlist[self.game.userlist.index(last_cards_to)]
	def input(self, user, command, options):
		self.last_cards_to.getCards(self.player.cards) #give the remaining cards to the victim
		self.game.remove(self.player)
		ret=[(self.game.messages.get(Messages.LOSE)%self.player, True)]
		if len(self.game.userlist)<2:
			self.game.userlist=[]
			self.game.setState(PregameState(self.game))
			ret+=[(self.game.messages.get(Messages.CANNOT_START), True)]
		else:
			self.game.setState(SelectPlayerState(self.game))
			self.game.execute_next=True
		return ret

class LostTestCase(unittest.TestCase):
	def testLastPlayerLose(self):
		self.game=Game()
		self.game.current_user=3 #user4
		self.game.userlist.append(User("user1"))
		self.game.userlist.append(User("user2"))
		self.game.userlist.append(User("user3"))
		self.game.userlist.append(User("user4"))
		self.game.setState(LostState(self.game, "user4", "user1"))
		self.assertEquals(self.game.state.last_cards_to.__class__, User)
		output=self.game.state.input("", "", "")
		self.assertEquals(output, [(self.game.messages.get(Messages.LOSE)%"user4", True)])
		self.assertEquals(self.game.userlist[0].cards['1'], 8) #user1 gets the cards
		self.assertEquals(self.game.current_user, 0) #next user, index 0
	def testFirstPlayerLose(self):
		self.game=Game()
		self.game.current_user=0 #user1
		self.game.userlist.append(User("user1"))
		self.game.userlist.append(User("user2"))
		self.game.userlist.append(User("user3"))
		self.game.userlist.append(User("user4"))
		self.game.setState(LostState(self.game, "user1", "user4"))
		self.assertEquals(self.game.state.last_cards_to.__class__, User)
		output=self.game.state.input("", "", "")
		self.assertEquals(output, [(self.game.messages.get(Messages.LOSE)%"user1", True)])
		self.assertEquals(len(self.game.userlist), 3)
		self.assertEquals([str(user) for user in self.game.userlist], ["user2", "user3", "user4"])
		self.assertEquals(self.game.userlist[2].cards['1'], 8) #user4 at index 3 gets the cards
		self.assertEquals(self.game.current_user, 0) #next user, now the index 0
	def testMiddlePlayerLose(self):
		self.game=Game()
		self.game.current_user=2 #user3 at index 2
		self.game.userlist.append(User("user1"))
		self.game.userlist.append(User("user2"))
		self.game.userlist.append(User("user3"))
		self.game.userlist.append(User("user4"))
		self.game.setState(LostState(self.game, "user2", "user4"))
		self.assertEquals(self.game.state.last_cards_to.__class__, User)
		output=self.game.state.input("", "", "")
		self.assertEquals(output, [(self.game.messages.get(Messages.LOSE)%"user2", True)])
		self.assertEquals(len(self.game.userlist), 3)
		self.assertEquals([str(user) for user in self.game.userlist], ["user1", "user3", "user4"])
		self.assertEquals(self.game.userlist[2].cards['1'], 8) #user4 at index 3 gets the cards
		self.assertEquals(self.game.current_user, 1) #user3 now at index 1

class PayedState(State):
	def __init__(self, game, cards):
		self.game=game
		self.cards=cards
		self.defect_dice=False #fake dice
		self.defect_choice=False
	def input(self, user, command, options):
		if user==self.game.userlist[self.game.current_user]:
			if command=="nimm" or command=="NEXT_COMMAND":
				self.game.userlist[self.game.current_user].getCards(self.cards)
				self.game.setState(SelectPlayerState(self.game))
				self.game.execute_next=True
				return [
					(self.game.messages.get(Messages.ACCEPT)%user, True),
					(self.game.messages.get(Messages.GOT)%(self.cards['5'], self.cards['2'], self.cards['1'], self.cards['Z']), False)
				]
			elif command=="zweifel":
				dice=random.randint(1,6)
				if self.defect_dice:
					dice=self.defect_dice
				money=worth(self.cards)
				ret=[(self.game.messages.get(Messages.DOUBT%user),True)]
				ret+=[(self.game.messages.get(Messages.DICE%(user, dice)),True)]
				if money == dice:
					ret+=[(self.game.messages.get(Messages.MONEY_CORRECT), True)]
					self.game.execute_next=True #execute this state again, with NEXT_COMMAND
				elif money < dice:
					ret+=[(self.game.messages.get(Messages.MONEY_TOOLITTLE), True)]
					ret+=[(self.game.messages.get(Messages.VICTIM_CHOOSEN%self.game.victim), True)]
					self.game.setState(NeedToPayState(self.game, self.cards))
				elif dice < money:
					ret+=[(self.game.messages.get(Messages.MONEY_TOOMUCH)%(money, self.game.userlist[self.game.current_user]), True)]
					if worth(self.game.userlist[self.game.current_user].cards) < worth(self.cards):
						#LOSE
						ret+=[(self.game.messages.get(Messages.LOSE_PAYBACK)%(self.game.userlist[self.game.current_user], worth(self.cards), worth(self.game.userlist[self.game.current_user].cards), self.game.victim), True)]
						self.game.execute_next=True
						self.game.setState(LostState(self.game, self.game.userlist[self.game.current_user], self.game.victim))
						return ret
					self.game.victim.getCards(self.cards)
					self.game.setState(PaybackState(self.game, worth(self.cards)))
				return ret

class NeedToPayState(State):
	def __init__(self, game, already_payed={'1': 0, '2': 0, '5': 0, 'Z': 0}):
		self.game=game
		self.cards=already_payed
	def input(self, user, command, options):
		if self.game.victim==user:
			if command=="zahl":
				try:
					cards2=string2cards(options)
					self.game.victim.giveCards(cards2) #subtract the cards from the victim
					#add to already_payed cards
					cards2['1']+=self.cards['1']
					cards2['2']+=self.cards['2']
					cards2['5']+=self.cards['5']
					cards2['Z']+=self.cards['Z']
					self.game.setState(PayedState(self.game, cards2)) #put them into the state
					return self.game.messages.get(Messages.PAYED%(user, string2numCards(options)))
				except DoesNotHaveException, e:
					which=e.message
					how_many=cards2[e.message]
					return [(self.game.messages.get(Messages.DOES_NOT_HAVE_ENOUGH)%(how_many, which, self.game.victim.cards[which], which), False)]

class SelectPlayerState(State):
	def input(self, user, command, options):
		self.game.current_user=(self.game.current_user+1)%len(self.game.userlist)
		#self.game.execute_next=True
		#self.game.setState(ChooseVictimState(self.game))
		self.game.victim=random.choice(self.game.userlist)
		assert len(self.game.userlist)>=2
		while self.game.userlist[self.game.current_user] == self.game.victim:
			self.game.victim=random.choice(self.game.userlist)
		self.game.setState(NeedToPayState(self.game))
		return [
			(self.game.messages.get(Messages.YOUR_TURN%self.game.userlist[self.game.current_user]), True),
			(self.game.messages.get(Messages.VICTIM_CHOOSEN%self.game.victim), True)
		]

class WaitingForPlayersState(State):
	def input(self, user, command, options):
		if command=="ich":
			self.game.userlist.append(User(user))
			return self.game.messages.get(Messages.USER_JOINED%user)
		elif command=="remove":
			self.game.userlist.remove(User(user))
			return self.game.messages.get(Messages.USER_PARTED%user)
		elif command=="startgame":
			if len(self.game.userlist) >=2:
				self.game.setState(SelectPlayerState(self.game))
				self.game.execute_next=True
				return self.game.messages.get(Messages.GAME_STARTED)
			else:
				return self.game.messages.get(Messages.CANNOT_START)

class PregameState(State):
	def input(self, user, command, options):
		if command=="newgame":
			self.game.setState(WaitingForPlayersState(self.game))
			return self.game.messages.get(Messages.NEW_GAME)
class Game:
	def __init__(self):
		self.state=PregameState(self)
		self.messages=Messages()
		self.userlist=[]
		self.victim=None
		self.state=PregameState(self)
		self.current_user=-1
		self.carlotta_cards=['5', '2', '2', '1', '1', 'Z']
		self.execute_next=False
	def input(self, user, command, options=""):
		message=self.state.input(user, command, options)
		if type(message)==str:
			message=[(message, True)]
		elif message==None:
			message=[]
		if self.execute_next:
			self.execute_next=False
			return message + self.input(user, "NEXT_COMMAND", "NEXT_OPTIONS") #call to the next state
		else:
			return message
	def remove(self, user):
		if self.userlist.index(user) < self.current_user:
			self.current_user-=1 #the index shrinks by one, if the removed user was over the current user
		self.userlist.remove(user)
		self.current_user=self.current_user%len(self.userlist)

	def setState(self, state):
		self.state=state

class gameTestCase(unittest.TestCase):
	def setUp(self):
		self.game=Game()
		#self.game.setState(PregameState(self.game))
		self.messages=Messages()
		self.nick="user1"
		self.nick2="userX"
		self.nick3="userGamma"
	def assertPublicOutput(self, output, correct_output):
		if type(correct_output)!=list:
			correct_output=[(correct_output, True)]
		for index in range(len(correct_output)):
			#print output[index]
			self.assertEquals(output[index], correct_output[index])
	def testNewgame(self):
		self.assertPublicOutput(self.game.input(self.nick, "newgame"), self.messages.get(Messages.NEW_GAME))
		self.assertTrue(len(self.game.userlist)==0, self.game.userlist)
		self.assertEquals(self.game.state.__class__, WaitingForPlayersState)
	def testJoin(self):
		self.testNewgame()
		self.assertPublicOutput(self.game.input(self.nick, "ich"), self.messages.get(Messages.USER_JOINED)%self.nick)
		self.assertPublicOutput(self.game.input(self.nick2, "ich"), self.messages.get(Messages.USER_JOINED)%self.nick2)
	def testPart(self):
		self.testJoin()
		self.assertPublicOutput(self.game.input(self.nick2, "remove"), self.messages.get(Messages.USER_PARTED)%self.nick2)
		self.assertTrue(not self.nick2 in self.game.userlist)
	def testCannotStart(self):
		self.testPart()
		self.assertPublicOutput(self.game.input(self.nick, "startgame"), self.messages.get(Messages.CANNOT_START))
		self.assertEquals(self.game.state.__class__, WaitingForPlayersState)
	def testStart(self):
		self.testJoin()
		self.assertTrue(self.nick in self.game.userlist and self.nick2 in self.game.userlist, self.game.userlist)
		lines=self.game.input(self.nick, "startgame")
		self.assertPublicOutput(lines, 
				[
				(self.messages.get(Messages.GAME_STARTED), True),
				(self.messages.get(Messages.YOUR_TURN%self.nick), True),
				(self.messages.get(Messages.VICTIM_CHOOSEN%self.nick2), True)
				]
		)
		self.assertEquals(self.game.state.__class__, NeedToPayState)
	def testPayment(self):
		self.testStart()
		self.assertEquals(self.game.input(self.nick2, "zahl", "55555"),
				[(self.game.messages.get(Messages.DOES_NOT_HAVE_ENOUGH)%(5, 5, 1, 5), False)]) #private
		self.assertEquals(self.game.state.__class__, NeedToPayState)
		self.assertEquals(worth(self.game.state.cards), 0)

		self.assertPublicOutput(self.game.input(self.nick2, "zahl", "2Z"), self.messages.get(Messages.PAYED%(self.nick2, 2)))
		self.assertEquals(self.game.victim.cards['Z'], 1)
		self.assertEquals(self.game.victim.cards['2'], 1)
		self.assertEquals(self.game.state.__class__, PayedState)
	def testAccept(self):
		self.testPayment()
		self.assertPublicOutput(self.game.input(self.nick, "nimm"), [
			(self.messages.get(Messages.ACCEPT)%self.nick, True),
			(self.game.messages.get(Messages.GOT)%(0, 1, 0, 1), False),

			#next state, just to finish the test
			(self.messages.get(Messages.YOUR_TURN)%self.nick2, True),
			(self.messages.get(Messages.VICTIM_CHOOSEN%self.nick), True)
		])
		self.assertEquals(self.game.userlist[self.game.userlist.index(self.nick)].cards['2'], 3)
		self.assertEquals(self.game.userlist[self.game.userlist.index(self.nick)].cards['Z'], 3)
		self.assertEquals(self.game.state.__class__, NeedToPayState) # Game skipped over SelectPlayerState
	def testDoubt_correct(self):
		self.testPayment()
		self.game.state.defect_dice=2
		self.assertPublicOutput(self.game.input(self.nick, "zweifel"), [
			(self.messages.get(Messages.DOUBT)%self.nick, True),
			(self.messages.get(Messages.DICE)%(self.nick, 2), True),
			(self.messages.get(Messages.MONEY_CORRECT), True),
			(self.messages.get(Messages.ACCEPT)%self.nick, True),
			(self.game.messages.get(Messages.GOT)%(0, 1, 0, 1), False),

			#next state, just to finish the test
			(self.messages.get(Messages.YOUR_TURN)%self.nick2, True),
			(self.messages.get(Messages.VICTIM_CHOOSEN%self.nick), True)
		])
		self.assertEquals(self.game.state.__class__, NeedToPayState) #Game skipped over SelectPlayerState
	def testDoubt_toolittle(self):
		self.testPayment()
		self.game.state.defect_dice=3
		self.assertPublicOutput(self.game.input(self.nick, "zweifel"), [
			(self.messages.get(Messages.DOUBT)%self.nick, True),
			(self.messages.get(Messages.DICE)%(self.nick, 3), True),
			(self.messages.get(Messages.MONEY_TOOLITTLE), True),
			(self.messages.get(Messages.VICTIM_CHOOSEN)%self.nick2, True)
		])
		self.assertEquals(self.game.state.__class__, NeedToPayState) #not skipped, but an additional payment is needed
		self.assertEquals(self.game.state.cards['Z'], 1)
		self.assertEquals(self.game.state.cards['2'], 1)
	def testDoubt_toomuch(self):
		self.testPayment()
		self.game.state.defect_dice=1
		self.assertPublicOutput(self.game.input(self.nick, "zweifel"), [
			(self.messages.get(Messages.DOUBT)%self.nick, True),
			(self.messages.get(Messages.DICE)%(self.nick, 1), True),
			(self.messages.get(Messages.MONEY_TOOMUCH)%(2, self.nick), True),
		])
		self.assertEquals(self.game.state.__class__, PaybackState)
	def testPayback(self):
		self.testDoubt_toomuch()
		self.game.state.defect_choice="Z"
		self.assertPublicOutput(self.game.input(self.nick, "zahl", "5"), [
			(self.messages.get(Messages.PAYBACK)%(self.nick, 5, self.nick2), True),
			(self.messages.get(Messages.CARLOTTA)%(self.nick, char2word('Z')), True),
		])
		self.assertEquals(self.game.carlotta_cards.count('Z'), 0)

		#restore old state
		self.carlotta_cards=['5', '2', '2', '1', '1', 'Z']

	def testPaybackCarlottaEmpty(self):
		self.testDoubt_toomuch()
		self.game.state.defect_choice="Z"
		self.game.carlotta_cards=['Z']
		self.assertPublicOutput(self.game.input(self.nick, "zahl", "5"), [
			(self.messages.get(Messages.PAYBACK)%(self.nick, 5, self.nick2), True),
			(self.messages.get(Messages.CARLOTTA)%(self.nick, char2word('Z')), True),
			(self.messages.get(Messages.CARLOTTA_EMPTY), True),
		])
		self.assertEquals(len(self.game.carlotta_cards), 0)

		#restore old state
		self.carlotta_cards=['5', '2', '2', '1', '1', 'Z']
	def testDoubt_toomuch_lose(self):
		self.testPayment()
		self.game.state.defect_dice=1
		#backup
		cards_backup=self.game.userlist[self.game.current_user].cards

		self.game.userlist[self.game.current_user].cards={'1': 1, '2': 0, '5': 0, 'Z': 0}
		self.game.userlist.append(User(self.nick3))
		self.assertPublicOutput(self.game.input(self.nick, "zweifel"), [
			(self.messages.get(Messages.DOUBT)%self.nick, True),
			(self.messages.get(Messages.DICE)%(self.nick, 1), True),
			(self.messages.get(Messages.MONEY_TOOMUCH)%(2, self.nick), True),
			(self.messages.get(Messages.LOSE_PAYBACK)%(self.nick, 2, 1, self.nick2), True),
			(self.messages.get(Messages.LOSE)%self.nick, True),
			(self.messages.get(Messages.YOUR_TURN%self.nick3), True),
			(self.messages.get(Messages.VICTIM_CHOOSEN%self.nick2), True)
		])
		self.assertEquals(self.game.state.__class__, NeedToPayState)

		#restore
		self.game.userlist[self.game.current_user].cards=cards_backup

if __name__ == '__main__':
	unittest.main()

