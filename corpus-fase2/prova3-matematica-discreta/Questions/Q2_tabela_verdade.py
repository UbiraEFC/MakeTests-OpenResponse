from MakeTests import QuestionDissertative

class QuestionTabelaVerdade(QuestionDissertative):
	# Tabela-verdade e conteudo 2D (4 combinacoes de p/q x varias colunas) -
	# linhas pautadas horizontais nao dao estrutura de grade, entao o aluno
	# precisa de espaco extra pra desenhar as divisorias por conta propria,
	# alem da linha de classificacao final. lines=9 (vs. padrao 6) + caixa
	# mais alta (aspectRate 2/1 -> 1.5/1) mantem ~7,64mm/linha, quase igual
	# ao espacamento calibrado no Q2, mesmo com 50% mais linhas.
	lines = 9

	def answerAreaAspectRate(self):
		return 1.5

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
