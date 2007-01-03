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

import random
import chatMod

class chatMod(chatMod.chatMod):
	def __init__(self, bot):
		self.bot=bot
		self.answers=[
		"Signs point to yes (Zeichen deuten auf ja)",
		"Yes (Ja)",
		"Without a doubt (Ohne einen Zweifel)",
		"As I see it yes (Wie ich es sehe ja)",
		"Most likely (Hoechstwahrscheinlich)",
		"You may rely on it (Darauf kannst du dich verlassen)",
		"Yes definitely (Definitiv ja)",
		"It is decidedly so (Es ist entschieden so)",
		"Outlook good (Gute Aussichten)",
		"It is certain (Es ist sicher)",
		"My sources say no (Meine Quellen sagen nein)",
		"Very doubtful (Sehr zweifelhaft)",
		"Don't count on it (Zaehl nicht drauf)",
		"Outlook not so good (Nicht so gute Aussichten)",
		"My reply is no (Meine Antwort ist nein)",
		"Reply hazy, try again (Antwort unklar, versuchs nochmal)",
		"Concentrate and ask again (Konzentriere dich und frag nochmal)",
		"Better not tell you now (Ich sags dir jetzt lieber nicht)",
		"Cannot predict now (Kann es jetzt nicht vorhersagen)",
		"Ask again later (Frag später nochmal)"
		]

	def msg(self, user, channel, msg):
		#if channel == self.bot.nickname:
		if len(msg) > 7 and msg[:7] == "!8ball ": #>7 = only if the user asked something.
			self.bot.sendme(channel, random.choice(self.answers))
