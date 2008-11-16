import random, re
class eliza:
	reflections={}
	patterns={}
	def setReflections(self, refl):
		self.reflections=refl
	def setPatterns(self, pat):
		self.patterns={}
		for key in pat.keys():
			self.patterns[re.compile(key, re.I)]=pat[key]
	def reply(self, input):
		for regex in self.patterns.keys():
			match=regex.match(input)
			if match:
				answer=random.choice(self.patterns[regex])
				if "%s" in answer:
					answer=answer%match.groups()
				if answer[-2] in '.?!':
					for refl in self.reflections.keys():
						answer=answer.replace(refl, self.reflections[refl])
					answer=answer[:-1]
				return answer

