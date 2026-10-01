from MakeTests import QuestionDissertative

class QuestionPitagoras(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Um triangulo retangulo possui catetos medindo $3\\,cm$ e $4\\,cm$. Calcule a "
			"medida da hipotenusa utilizando o Teorema de Pitagoras, apresentando o "
			"desenvolvimento do calculo."
		)
		self.rubric = (
			"Deve apresentar: (1) formula correta do Teorema de Pitagoras "
			"$a^{2} = b^{2} + c^{2}$ (ou equivalente); (2) substituicao correta dos valores "
			"($3^2 + 4^2 = 9 + 16 = 25$); (3) resultado final correto (hipotenusa $= 5\\,cm$)."
		)
