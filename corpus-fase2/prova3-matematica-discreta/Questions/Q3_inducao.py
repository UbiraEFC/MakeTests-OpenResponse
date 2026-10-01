from MakeTests import QuestionDissertative

class QuestionInducao(QuestionDissertative):
	# Enunciado do principio + 3 casos de verificacao (n=1,2,3): 2 linhas a
	# mais que o padrao (6->8), ainda a ~6,37mm/linha (dentro da margem de
	# seguranca sobre o x-height tipico de 3-5mm registrada no Q2).
	lines = 8

	def makeSetup(self):
		self.statement = (
			"Enuncie, de forma geral, o Principio da Inducao Matematica. Em seguida, verifique "
			"que a formula $\\dfrac{n(n+1)}{2}$ fornece corretamente a soma dos numeros "
			"naturais de $1$ ate $n$ para os casos $n=1$, $n=2$ e $n=3$."
		)
		self.rubric = (
			"Deve apresentar: (1) ideia geral correta do principio (provar um caso base e "
			"mostrar que, se a afirmacao vale para um caso, vale tambem para o proximo); "
			"(2) verificacao correta para $n=1$ (soma $=1$, formula $=1$); (3) verificacao "
			"correta para $n=2$ e $n=3$ (soma $=3$, formula $=3$; soma $=6$, formula $=6$)."
		)
