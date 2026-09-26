from MakeTests import QuestionDissertative

class QuestionComplexidadeOrdenacao(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"O que significa dizer que um algoritmo de ordenacao possui complexidade de "
			"tempo O(n log n)? Cite um algoritmo de ordenacao com essa complexidade e "
			"explique, em linhas gerais, por que ele alcanca esse desempenho."
		)
		self.rubric = (
			"Deve citar: (1) explicacao correta de complexidade O(n log n) (o tempo de "
			"execucao cresce proporcionalmente a n multiplicado pelo logaritmo de n); "
			"(2) um algoritmo correto com essa complexidade (ex.: Merge Sort, Quick Sort no "
			"caso medio, Heap Sort); (3) justificativa coerente com a estrategia do algoritmo "
			"escolhido (ex.: divisao recursiva do problema pela metade)."
		)
