from MakeTests import QuestionDissertative

class QuestionTabelaHash(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Explique o que e uma tabela hash (hash table) e como ela permite busca eficiente "
			"de elementos. Descreva tambem o que e uma colisao de hash e cite uma forma de "
			"trata-la."
		)
		self.rubric = (
			"Deve citar: (1) tabela hash usa uma funcao hash para mapear chaves a posicoes "
			"(indices) de um vetor, permitindo busca em tempo medio O(1); (2) definicao correta "
			"de colisao (duas chaves diferentes mapeadas para o mesmo indice); (3) pelo menos "
			"uma tecnica de tratamento de colisao (ex.: encadeamento/listas ligadas, "
			"enderecamento aberto/sondagem linear)."
		)
