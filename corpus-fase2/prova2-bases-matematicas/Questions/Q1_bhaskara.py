from MakeTests import QuestionDissertative

class QuestionBhaskara(QuestionDissertative):
	# Resposta tem 3 passos matematicos (Delta, formula, x1/x2) - 1 linha a
	# mais que o padrao (6->7) para dar folga sem comprimir o espacamento
	# (~7,17mm/linha, ainda dentro da faixa calibrada no Q2).
	lines = 7

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
