# This file is part of OtfBot.
# -*- coding: utf-8 -*-
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
# (c) 2008 by Alexander Schier
#

"""
    Tic-Tac-Toe (X and O) game.

    The only winning move is not to play.
"""

import random
from otfbot.lib import chatMod
from otfbot.lib.pluginSupport.decorators import callback

class Game:
    """ game implementation """

    def __init__(self):
        self.myStones=[]
        self.yourStones=[]

    def drawField(self):
        """ draw the current field with X and O and numbers """
        ret=""
        for y in range(3):
            for x in range(3):
                pos=y*3 + (x+1)
                if pos in self.myStones:
                    ret+="O "
                elif pos in self.yourStones:
                    ret+="X "
                else:
                    ret+=str(pos) + " "
            ret+="\n"
        return ret

    def move(self, num):
        """
            make a move

            @returns: True if the move is valid, False if not.
        """
        if not num in self.myStones and not num in self.yourStones:
            self.yourStones+=[num]
            return True
        return False

    def neighbours(self, pos):
        """ calculate the neighbour fields """
        return {
            1: [2,4],
            2: [1,3,5,4,6],
            3: [2,5,6],
            4: [1,5,7,2,8],
            5: [1,2,3,4,6,7,8,9],
            6: [5,3,9,8,2],
            7: [4,5,8],
            8: [7,4,5,9,6],
            9: [8,6]}[pos]

    def winningField(self, stone, stone2, fields):
        """ test if a Field wins the game """
        print stone, stone2, fields
        for field in fields:
            stoneset=set([stone, stone2, field])
            for i in [1,4,7]:
                if stoneset == set(range(i, i+3)):
                    return field
            for i in [1,2,3]:
                if stoneset == set(range(i, 10, 3)):
                    return field
            if stoneset == set([1,5,9]):
                return field
            if stoneset == set([3,5,7]):
                return field
        return None

    def kiMove(self):
        """ let the artificial intelligence make a move """
        stones=[1,2,3,4,5,6,7,8,9]
        for s in self.myStones:
            stones.remove(s)
        for s in self.yourStones:
            stones.remove(s)
        #offensive, find wins
        for stone in self.myStones:
            for stone2 in self.myStones:
                if stone2 != stone:
                    winning=self.winningField(stone, stone2, stones)
                    if winning:
                        self.myStones+=[winning]
                        print "set stone %s, because it finishes a line"%winning
                        return winning
        #defensive
        for stone in self.yourStones:
            for stone2 in self.neighbours(stone):
                if stone2 in self.yourStones:
                    winning=self.winningField(stone, stone2, stones)
                    if winning:
                        self.myStones+=[winning]
                        print "set stone %s, because it stops the human from finishing a line with %s,%s,%s"%(winning, stone, stone2, winning)
                        return winning
        #offensive, find good combinations
        for stone in self.myStones:
            stones2=self.myStones#neighbours(stone)
            for stone2 in stones2:
                if stone2 in self.myStones or stone2 in self.yourStones:
                    stones2.remove(stone2)
            #check the stones left
            random.shuffle(stones2)
            for stone2 in stones2:
                stones3=stones #stones - potential stone
                stones3.remove(stone2)
                if self.winningField(stone, stone2, stones3): #if we set stone2, we could get a winning move
                    self.myStones+=[stone2]
                    print "set stone %s, because it could lead to a win"%stone2
                    return stone2
        #just random
        stone=random.choice(stones)
        self.myStones+=[stone]
        print "set stone %s, because i have not other idea what to do"%stone
        return stone
    HUMAN_WIN=1
    COMPUTER_WIN=2
    DRAW_GAME=3
    STILL_PLAYING=4

    def checkWin(self, lastStone):
        """ check if a player has won """
        if lastStone in self.myStones:
            for stone2 in self.neighbours(lastStone):
                if stone2 in self.myStones:
                    stone3=self.winningField(lastStone, stone2, [1,2,3,4,5,6,7,8,9])
                    if stone3 in self.myStones:
                        return self.COMPUTER_WIN
        if lastStone in self.yourStones:
            for stone2 in self.neighbours(lastStone):
                if stone2 in self.yourStones:
                    stone3=self.winningField(lastStone, stone2, [1,2,3,4,5,6,7,8,9])
                    if stone3 in self.yourStones:
                        return self.HUMAN_WIN
        if len(self.myStones + self.yourStones)==9:
            return self.DRAW_GAME
        return self.STILL_PLAYING

    def checkFinished(self, lastStone):
        """ check if the game is still active """
        status=self.checkWin(lastStone)
        return status != self.STILL_PLAYING


class Plugin(chatMod.chatMod):
    def __init__(self, bot):
        self.bot=bot
        self.game=Game()

    @callback
    def command(self, user, channel, command, options):
        """
            react on !tictactoe and !xo
            Syntax: !tictactoe [number]
            number for making a move, no number just
            prints the field
        """
        if command == "tictactoe" or command=="xo":
            if options == "":
                self.bot.sendmsg(channel, self.game.drawField().split("\n")[:3])
            else:
                try:
                    options=int(options)
                    if options in range(1,10):
                        ret=self.game.move(options)
                        if not ret:
                            self.bot.sendmsg(channel, "Ungültiger Zug, Feld besetzt.")
                        else:
                            self.bot.sendmsg(channel, self.game.drawField().split("\n")[:3])
                            if self.game.checkFinished(options):
                                self.bot.sendmsg(channel, "A strange game. The only winning move is not to play.")
                                self.game=Game()
                                return

                            self.bot.sendmsg(channel, "Mein Zug:")
                            kimove=self.game.kiMove()
                            self.bot.sendmsg(channel, self.game.drawField().split("\n")[:3])
                            if self.game.checkFinished(kimove):
                                self.bot.sendmsg(channel, "A strange game. The only winning move is not to play.")
                                self.game=Game()
                                return
                except ValueError:
                    pass
