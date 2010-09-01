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
# (c) 2010 by Alexander Schier
#

"""
    Calculate a pronounceable name from a git version
"""

vowels=list("aeiou")
consonants="abcdefghijklmnopqrstuvwxyz" #all chars
hex="0123456789abcdef" #hex alphabeth
consonants=list((set(consonants) - set(vowels)) - set("cqvxy")) #16 consonants
consonants.sort() #make it deterministic
vowels.sort()
#cross product vowels x vowels [('a', 'a'), ('a', 'e'), ...] len(b2)==25
vowels2=[(x,y) for x in vowels for y in vowels]
vowels2.sort()

assert len(consonants)==16, "consonants has len %d instead of 16"%len(consonants) 
assert len(vowels)==5, "vowels has len %d instead of 5"%len(vowels) 
assert len(vowels2)==25, "vowels2 has len %d instead of 25"%len(vowels2)

def ver2name(ver):
    """
        convert a 7-digit hex-number (git commit) to a pronounceable name

        @param ver: version, must have 7 digits
        @type ver: str
    """
    assert type(ver) == str
    assert len(ver) == 7
    name=""
    for i in xrange(3):
        name+=consonants[hex.index(ver[i*2])] #consonant matching the hex digit
        if i==2: #last vowal?
            #use both digits modulo 5, vowel will be ignored for parsing the name
            name+=vowels[( hex.index(ver[i*2]) + hex.index(ver[i*2+1]) )%5] #
        else: #not the last one, encode the 7th digit of ver in the vowel
            name+=vowels2[hex.index(ver[6])][i] #i=0 or i=1
        name+=consonants[hex.index(ver[i*2+1])] #consonant matching the hex digit
    name=name[0].upper()+name[1:]
    return name

def name2ver(name):
    """
        convert a versionname back to a git version

        @param name: must be a 9-digit string as produced by ver2name
        @type name: str
    """
    name=name.lower()
    assert len(name)==9
    ver=""
    for i in xrange(3):
        ver+=hex[consonants.index(name[3*i])]
        ver+=hex[consonants.index(name[3*i+2])]
    ver+=hex[vowels2.index( (name[1], name[4]) )]
    return ver

def validVername(name):
    """
        checks a name, if its a valid version name,
        which can be converted to a 7-digit git revision

        @param name: the name
        @type name: str
    """
    if not len(name)==9:
        return False
    elif not (set([name[i] for i in [1,4,7]])).issubset(set(vowels)):
        return False
    elif not (set([name[i] for i in [0,2,3,5,6,8]])).issubset(
        set(consonants)):
        return False
    elif not (name[1], name[4]) in vowels2:
        return False
    elif not vowels2.index((name[1], name[4])) <16:
        return False
    return True

if __name__ == '__main__':
    import unittest, hashlib, random
    class Ver2NameTestCase(unittest.TestCase):
        def testRandom(self):
            ver=hashlib.md5(str(random.random())).hexdigest()[:7]
            name=ver2name(ver)
            self.assertEquals(ver, name2ver(name))
        def testStatic(self):
            self.assertEquals(ver2name("474c8b9"), "Helhusmur")
            self.assertEquals(name2ver("Helhusmur"), "474c8b9")
            for i in "aeiou":
                #last vowel is not important for parsing
                self.assertEquals(name2ver("Helhusm"+i+"r"), "474c8b9")
    unittest.main()
            
