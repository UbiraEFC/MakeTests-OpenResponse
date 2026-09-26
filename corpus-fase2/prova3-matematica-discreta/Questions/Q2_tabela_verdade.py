from MakeTests import QuestionDissertative

class QuestionTabelaVerdade(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Construa a tabela-verdade da proposicao $(p \\land q) \\rightarrow \\lnot p$ e "
			"indique se ela e uma tautologia, uma contradicao ou uma contingencia."
		)
		self.rubric = (
			"Deve apresentar: (1) tabela-verdade com as 4 combinacoes de $p$ e $q$ "
			"(V/V, V/F, F/V, F/F) calculadas corretamente; (2) resultado final correto: a "
			"proposicao e falsa apenas quando $p$ e $q$ sao ambos verdadeiros, e verdadeira "
			"nos demais 3 casos; (3) classificacao correta como contingencia (nao e sempre "
			"verdadeira nem sempre falsa)."
		)
