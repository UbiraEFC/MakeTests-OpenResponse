from MakeTests import QuestionMultipleChoice

class CapitalSPQuestion(QuestionMultipleChoice):
    def makeSetup(self):
        import random
        
        # Opções com a resposta correta
        options = [
            ["São Paulo", True],
            ["Campinas", False],
            ["Santos", False],
            ["Ribeirão Preto", False]
        ]
        
        # Embaralhar opções
        random.shuffle(options)
        
        self.questions = [
            {
                "statement": "Qual é a capital do estado de São Paulo?",
                "alternatives": options,
                "itemsPerRow": 2
            }
        ]
        
        self.questionDescription = "Escolha a alternativa correta:"
        self.correctionCriteriaDescription = "1 questão = 100%"

    def calculateScore(self, correct, wrong, blank):
        return 100 if correct > 0 else 0
