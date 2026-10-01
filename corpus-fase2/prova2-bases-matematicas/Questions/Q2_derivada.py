from MakeTests import QuestionDissertative

class QuestionDerivada(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Calcule a derivada da funcao $f(x) = 3x^{3} - 5x^{2} + 2x - 7$ em relacao a $x$. "
			"Apresente o resultado de $f'(x)$ e explique brevemente a regra utilizada em cada "
			"termo."
		)
		self.rubric = (
			"Deve apresentar: (1) derivada correta $f'(x) = 9x^{2} - 10x + 2$; (2) mencao a "
			"regra do tombo/regra da potencia (multiplicar pelo expoente e diminuir o expoente "
			"em 1); (3) mencao de que a derivada de uma constante (aqui, -7) e zero."
		)
