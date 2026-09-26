from MakeTests import QuestionDissertative

class QuestionBhaskara(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Resolva a equacao do segundo grau $2x^{2} - 3x - 5 = 0$ utilizando a formula de "
			"Bhaskara. Apresente o calculo do discriminante ($\\Delta$) e os valores "
			"encontrados para $x_1$ e $x_2$."
		)
		self.rubric = (
			"Deve apresentar: (1) calculo correto do discriminante $\\Delta = b^2 - 4ac$ "
			"(valor esperado: $\\Delta = 49$); (2) aplicacao correta da formula de Bhaskara "
			"$x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$; (3) valores finais corretos "
			"($x_1 = 2{,}5$ e $x_2 = -1$)."
		)
