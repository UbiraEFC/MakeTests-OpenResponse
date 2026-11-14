from MakeTests import QuestionMultipleChoice

class BinaryTreeQuestion(QuestionMultipleChoice):
    def makeSetup(self):
        import random

        # Opções com a resposta correta
        options = [
            ["Cada no pode possuir no maximo dois filhos.", True],
            ["Cada no deve possuir exatamente tres filhos.", False],
            ["Uma arvore binaria nao possui raiz.", False],
            ["Todos os nos folha obrigatoriamente possuem dois filhos.", False]
        ]

        # Embaralhar opções
        random.shuffle(options)

        self.questions = [
            {
                "statement": "Qual das afirmacoes abaixo descreve corretamente uma arvore binaria?",
                "alternatives": options,
                "itemsPerRow": 2
            }
        ]

        self.questionDescription = "Escolha a alternativa correta:"
        self.correctionCriteriaDescription = "1 questao = 100%"

    def calculateScore(self, correct, wrong, blank):
        return 100 if correct > 0 else 0