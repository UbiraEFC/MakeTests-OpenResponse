from MakeTests import QuestionDissertative

class QuestionPilhaFila(QuestionDissertative):
	def makeSetup(self):
		self.statement = (
			"Explique a diferenca entre as estruturas de dados pilha (stack) e fila (queue) "
			"em relacao a ordem de insercao e remocao de elementos, e cite uma aplicacao "
			"pratica para cada uma."
		)
		self.rubric = (
			"Deve citar: (1) pilha segue a ordem LIFO (ultimo a entrar, primeiro a sair); "
			"(2) fila segue a ordem FIFO (primeiro a entrar, primeiro a sair); "
			"(3) pelo menos uma aplicacao pratica para cada estrutura (ex.: pilha - historico "
			"de navegador, desfazer/refazer; fila - impressao de documentos, atendimento em fila)."
		)
