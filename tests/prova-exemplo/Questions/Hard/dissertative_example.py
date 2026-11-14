from MakeTests import QuestionDissertative

class MyQuestionDissertative(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Explique, em suas palavras, o que e uma arvore binaria na Ciencia da Computacao, "
			"como seus nos sao organizados e cite uma aplicacao pratica desse tipo de estrutura de dados."
		)
		self.rubric = (
			"Deve citar: (1) estrutura hierarquica composta por nos; "
			"(2) cada no possui no maximo dois filhos (esquerdo e direito); "
			"(3) aplicacao pratica, como arvores de busca binarias, expressoes aritmeticas, "
			"indexacao de dados ou hierarquias."
		)