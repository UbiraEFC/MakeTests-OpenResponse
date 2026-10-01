from MakeTests import QuestionDissertative

class QuestionConjuntos(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Dados os conjuntos $A = \\{1, 2, 3, 4\\}$ e $B = \\{3, 4, 5, 6\\}$, determine os "
			"elementos dos conjuntos $A \\cup B$ (uniao), $A \\cap B$ (intersecao) e "
			"$A - B$ (diferenca)."
		)
		self.rubric = (
			"Deve apresentar corretamente: (1) $A \\cup B = \\{1,2,3,4,5,6\\}$; "
			"(2) $A \\cap B = \\{3,4\\}$; (3) $A - B = \\{1,2\\}$."
		)
