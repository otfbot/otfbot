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
# (c) 2005 - 2010 by Alexander Schier
#

""" a simple eliza ki implementation with regular expressions """

import random
import re


class eliza:
    reflections = {}
    patterns = {}

    def setReflections(self, refl):
        self.reflections = refl

    def setPatterns(self, pat):
        self.patterns = {}
        for key in pat.keys():
            self.patterns[re.compile(key, re.I)] = pat[key]

    def reply(self, input):
        for regex in self.patterns.keys():
            match = regex.match(input)
            if match:
                answer = random.choice(self.patterns[regex])
                if "%s" in answer:
                    answer = answer % match.groups()
                if answer[-2] in '.?!':
                    for refl in self.reflections.keys():
                        answer = answer.replace(refl, self.reflections[refl])
                    answer = answer[:-1]
                return answer
