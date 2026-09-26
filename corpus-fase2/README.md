# Corpus Fase 2 (roadmap Q3, ADR-001)

Três provas novas (3 questões dissertativas cada), preparadas para ampliar o corpus de
respostas manuscritas reais exigido pela Fase 2 do roadmap (`ADR-001-substituicao-ocr-por-llm-vision.md`
§11: "≥20 respostas manuscritas reais, 2+ escritores, ambos os estilos").

| Prova | Foco | Questões |
|---|---|---|
| `prova1-algoritmos-estruturas-dados/` | Transcrição em geral (prosa técnica) | pilha/fila, complexidade O(n log n), tabela hash |
| `prova2-bases-matematicas/` | Leitura de fórmulas matemáticas manuscritas | Bhaskara, derivada, Teorema de Pitágoras |
| `prova3-matematica-discreta/` | Transcrição de notação matemática básica | conjuntos, tabela-verdade, indução matemática |

Cada prova já tem **3 cópias** (`Students.csv` com "Escritor 1/2/3" — identidades fictícias,
mesma convenção de anonimização do corpus do Q2). 3 provas × 3 cópias × 3 questões = até
**27 respostas manuscritas**, folga confortável acima do mínimo de 20 do roadmap — desde que
pelo menos 2 pessoas diferentes preencham cópias distintas (requisito "2+ escritores").

## PDFs gerados (não versionados — regenere se precisar)

```
prova1-algoritmos-estruturas-dados/aed_corpus.pdf              # prova em branco, 3 cópias
prova1-algoritmos-estruturas-dados/aed_corpus_gabarito.pdf     # gabarito (enunciados+rubricas)
prova2-bases-matematicas/matbasica_corpus.pdf
prova2-bases-matematicas/matbasica_corpus_gabarito.pdf
prova3-matematica-discreta/matdiscreta_corpus.pdf
prova3-matematica-discreta/matdiscreta_corpus_gabarito.pdf
```

Para regerar (ex.: depois de editar uma questão em `Questions/`):

```bash
source ../../.venv/bin/activate   # a partir de dentro de cada pasta prova*/
cd corpus-fase2/prova1-algoritmos-estruturas-dados
python ../../../MakeTests.py -v
```

## Próximos passos (fora do escopo automatizável)

1. **Imprimir** os `*_corpus.pdf` (não o gabarito) — cada um tem 3 cópias (uma por "Escritor").
2. **Distribuir** as cópias para pelo menos 2 pessoas diferentes escreverem à mão — idealmente
   variando estilo de letra (forma/cursiva) entre elas, como no corpus do Q2.
3. **Digitalizar** (scanner de celular ou de mesa, ~300dpi, como foi feito para `provas-pdf/`).
4. **Guardar os scans fora do repositório git**, no mesmo padrão de `../provas-pdf/` (dados de
   caligrafia real não são versionados — ver ADR-001 §9, minimização/pseudonimização). Sugestão:
   `../corpus-fase2-scans/prova1.pdf`, `prova2.pdf`, `prova3.pdf` (uma por tema, todas as cópias
   digitalizadas em sequência no mesmo PDF, como já é feito para `provas-pdf/provaN.pdf`).
5. Quando os scans estiverem prontos, a Fase 2 do roadmap consome esse corpus para medir CER da
   transcrição vision e taxa de alucinação (ver `ADR-001` §11, linha "2. Testes comparativos
   controlados").
