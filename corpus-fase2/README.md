# Corpus Fase 2 (roadmap Q3, ADR-001)

Três provas novas (3 questões dissertativas cada), preparadas para ampliar o corpus de
respostas manuscritas reais exigido pela Fase 2 do roadmap (`ADR-001-substituicao-ocr-por-llm-vision.md`
§11: "≥20 respostas manuscritas reais, 2+ escritores, ambos os estilos").

| Prova | Foco | Questões |
|---|---|---|
| `prova1-algoritmos-estruturas-dados/` | Transcrição em geral (prosa técnica) | pilha/fila, complexidade O(n log n), tabela hash |
| `prova2-bases-matematicas/` | Leitura de fórmulas matemáticas manuscritas | Bhaskara, derivada, Teorema de Pitágoras |
| `prova3-matematica-discreta/` | Transcrição de notação matemática básica | conjuntos, tabela-verdade, indução matemática |

Cada prova tem **1 "aluno"** só (`Students.csv` com "Escritor 1" — identidade fictícia, mesma
convenção de anonimização do corpus do Q2). O PDF gerado é um **template de 1 cópia** — o mesmo
padrão usado no corpus do Q2 (`aed.pdf` também era gerado com 1 "aluno" e impresso 4 vezes para
virar `provas-pdf/prova1..4.pdf`). Aqui, imprima cada `*_corpus.pdf` quantas vezes forem
necessárias e distribua os impressos para pessoas diferentes preencherem à mão.

Pra bater o mínimo de "≥20 respostas manuscritas reais, 2+ escritores" do roadmap com 3 questões
por prova, **~3-4 impressões por prova** (≈9-12 impressões no total, entre pelo menos 2 pessoas
diferentes) já dá 27-36 respostas — folga confortável. Ajuste livremente pra mais.

## PDFs gerados (não versionados — regenere se precisar)

```
prova1-algoritmos-estruturas-dados/aed_corpus.pdf              # prova em branco, 1 cópia (template p/ impressão)
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

1. **Imprimir** os `*_corpus.pdf` (não o gabarito) — cada um é 1 template; tire quantas cópias
   físicas quiser (ver recomendação de quantidade acima).
2. **Distribuir** os impressos para pelo menos 2 pessoas diferentes escreverem à mão — idealmente
   variando estilo de letra (forma/cursiva) entre elas, como no corpus do Q2.
3. **Digitalizar** (scanner de celular ou de mesa, ~300dpi, como foi feito para `provas-pdf/`).
4. **Guardar os scans fora do repositório git**, no mesmo padrão de `../provas-pdf/` (dados de
   caligrafia real não são versionados — ver ADR-001 §9, minimização/pseudonimização). Sugestão:
   `../corpus-fase2-scans/prova1.pdf`, `prova2.pdf`, `prova3.pdf` (uma por tema, todas as cópias
   digitalizadas em sequência no mesmo PDF, como já é feito para `provas-pdf/provaN.pdf`).
5. Quando os scans estiverem prontos, a Fase 2 do roadmap consome esse corpus para medir CER da
   transcrição vision e taxa de alucinação (ver `ADR-001` §11, linha "2. Testes comparativos
   controlados").
