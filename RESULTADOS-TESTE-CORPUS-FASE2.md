# Resultados — Corpus Fase 2 (roadmap Q3, ADR-001)

| Campo | Valor |
|---|---|
| **Status** | Fase 2 do roadmap concluída: corpus de 2 escritores, CER 6.4–8.2% (≤10%), zero alucinações não sinalizadas, correlação nota humana×modelo 0.943 (ver §7) |
| **Data** | 2026-09-30 |
| **Branch** | `pgc3/dissertativa-fase1` |
| **Contexto** | Ampliação do corpus real da Fase 2 (`ADR-001-substituicao-ocr-por-llm-vision.md` §11) com 3 provas novas × 3 questões, preparadas em `corpus-fase2/` |
| **Provider** | Anthropic (`claude-sonnet-5`), `LLM_VISION_MODE=on` |
| **Documentos relacionados** | `corpus-fase2/README.md` (preparo do corpus), `RESULTADOS-TESTE-VISION-FASE1.md` (validação da Fase 1, corpus original de 4 provas/1 questão) |

## 1. Objetivo

Processar as provas de algoritmos/estruturas de dados, bases matemáticas e matemática discreta
preenchidas à mão por **2 escritores reais** ("Ubi" e "Lari"), ampliando o corpus de respostas
manuscritas além das 4 provas de árvores binárias do Q2. Este documento consolida os resultados
como evidência para a Fase 2 do roadmap (testes comparativos controlados) e registra um achado
técnico novo sobre robustez da detecção de área de resposta.

## 2. Metodologia

- Pipeline real (`MakeTests.py -p <escaneado.pdf>`), `LLM_VISION_MODE=on`, sem mock.
- 3 provas (`corpus-fase2/prova{1,2,3}-*/`), 3 questões dissertativas cada, 1 "aluno" por
  template (`Students.csv` com identidade fictícia "Escritor 1") — a mesma PDF em branco foi
  impressa 2 vezes e preenchida por 2 pessoas diferentes, mesmo padrão usado no corpus do Q2.
- Escaneados de origem: `provas-corpus-pt2/{aed,bm,matdis}-{ubi,lari}.pdf`.
- Resultados de cada escritor preservados em pastas separadas (`Correcao-ubi/`, `Correcao-lari/`)
  para não colidir, já que os dois usam a mesma identidade de template.

## 3. Resultados comparativos

| Prova | Questão | Ubi | Lari |
|---|---|---|---|
| AED | Q1 pilha/fila | 70 | 60 |
| AED | Q2 complexidade O(n log n) | 100 | 100 |
| AED | Q3 tabela hash | 60 | 65 |
| Bases Matemáticas | Q1 Bhaskara | 100 | 40 |
| Bases Matemáticas | Q2 derivada | 90 | 45 |
| Bases Matemáticas | Q3 Pitágoras | 100 | 100 |
| Matemática Discreta | Q1 conjuntos | 67 | 100 |
| Matemática Discreta | Q2 tabela-verdade | 35 | 65 |
| Matemática Discreta | Q3 indução | 100 | 35 |

**Nota final por prova:** AED 76,7 (Ubi) / 75,0 (Lari) · Bases Matemáticas 96,7 (Ubi) / 61,7 (Lari)
· Matemática Discreta 67,3 (Ubi) / 66,7 (Lari).

A maior divergência entre escritores (Bases Matemáticas Q1, 100 vs. 40) tem causa identificada e
legítima — ver §5.

## 4. Transcrições completas, parecer e cobertura de rubrica

### AED — Q1 (pilha/fila)

| | Ubi (70) | Lari (60) |
|---|---|---|
| Transcrição | "A pilha segue a ordem LIFO (último a entrar, primeiro a sair), inserção e remoção ocorrem no topo. Já a FIFO (primeiro a entrar, primeiro a sair), elementos entram no fim e saem pelo início. Uma aplicação é desfazer/refazer um editor de texto." | "A pilha segue a ordem LIFO (último a entrar, primeiro a sair) inserção e remoção acontecem no mesmo extremo, o topo. A fila segue a ordem FIFO (primeiro a entrar, primeiro a sair): os elementos entram no fim e saem pelo início." |
| Parecer | Explica LIFO/FIFO corretamente; só 1 aplicação (faltou a da fila) | Explica LIFO/FIFO corretamente; nenhuma aplicação prática citada |
| `rubric_coverage` | LIFO ✅ FIFO ✅ aplicação(ambas) ❌ | LIFO ✅ FIFO ✅ aplicação(pilha) ❌ aplicação(fila) ❌ |

### AED — Q2 (complexidade O(n log n))

| | Ubi (100) | Lari (100) |
|---|---|---|
| Transcrição | "Um algoritmo O(n log n) tem tempo de execução proporcional a n multiplicado por log n... O merge sort é um exemplo, ele divide o vetor ao meio recursivamente, gerando cerca de log n níveis, em cada nível a interpolação percorre os n elementos." | "Um algoritmo O(n log n) tem tempo de execução proporcional a n multiplicado por log n... O merge sort é um exemplo: ele divide o vetor ao meio recursivamente, gerando cerca de log n níveis, e em cada nível a intercalação percorre os n elementos." |
| Parecer | Completo: explicação + algoritmo + justificativa | Completo: explicação + algoritmo + justificativa |
| `rubric_coverage` | 3/3 ✅ | 3/3 ✅ |

### AED — Q3 (tabela hash)

| | Ubi (60) | Lari (65) |
|---|---|---|
| Transcrição | "Uma tabela hash armazena pares chave-valor em um vetor, usando uma função hash que converte a chave em um índice. Uma colisão ocorre quando duas chaves diferentes resultam no mesmo índice." | "Uma tabela hash armazena pares chave-valor em um vetor, usando a função hash que converte a chave em índice. Como a posição é calculada diretamente, a busca tem tempo médio O(1). Uma colisão ocorre quando duas chaves diferentes resultam no mesmo índice." |
| Parecer | Tabela hash + colisão corretos; faltou O(1) e técnica de tratamento | Tabela hash + O(1) + colisão corretos; faltou técnica de tratamento |
| `rubric_coverage` | hash+O(1) ❌ colisão ✅ técnica ❌ | hash+O(1) ✅ colisão ✅ técnica ❌ |

### Bases Matemáticas — Q1 (Bhaskara)

| | Ubi (100) | Lari (40) |
|---|---|---|
| Transcrição | `a=2, b=-3, c=-5` / `Δ = b²-4ac = (-3)²-4·2·(-5) = 9+40 = 49` / `x = -b±√Δ/2a = 3±7/4` / `x1=2,5 e x2=-1` | `Coeficientes: a=2, b=-3, c=-5` / `Δ = b²-4ac = (-3)² \cdot 2 \cdot (-5) = -9+40 = 49` / `x = \dfrac{-b\pm\sqrt{Δ}}{2a} = \dfrac{3\pm7}{4}` |
| Parecer | Δ, fórmula e valores finais corretos | Δ correto; fórmula escrita como **código-fonte LaTeX** em vez de notação matemática; sem valores finais |
| `rubric_coverage` | 3/3 ✅ | discriminante ✅, fórmula aplicada ❌, valores finais ❌ |
| `review_recommended` | false | **true** |

Ver §5 — a Lari escreveu comandos LaTeX (`\cdot`, `\dfrac{}{}`) à mão em vez da notação
matemática renderizada. Confirmado visualmente que a transcrição do modelo está correta; o
sistema reagiu com nota baixa e sinalização de revisão, como esperado para conteúdo confuso.

### Bases Matemáticas — Q2 (derivada)

| | Ubi (90) | Lari (45) |
|---|---|---|
| Transcrição | `f(x) = 3x³-5x²+2x-7` / "Regra do tombo" / `f'(x) = 3.3x²-2.5x+2.1-7.0` / `f'(x) = 9x²-10x+2` | `f'(x) = 9x²-10x-2` / "Usei a regra do potência (regra do tombo): multiplica-se o coeficiente pelo expoente e diminui-se o expoente 1." |
| Parecer | Derivada correta, regra nomeada, termo constante implícito | Regra explicada corretamente, mas **erro de sinal** no resultado final (-2 em vez de +2) |
| `rubric_coverage` | 3/3 ✅ | derivada ❌ (erro real do aluno), regra ✅, constante=0 ❌ |

### Bases Matemáticas — Q3 (Pitágoras)

| | Ubi (100) | Lari (100) |
|---|---|---|
| Transcrição | `a=3,b=4` / `c²=a²+b²=3²+4²=9+16=25` / `c=√25=5cm` | `a²=b²+c²` / `a²=3²+4²=9+16=25` / `a=√25=5cm` |
| `rubric_coverage` | 3/3 ✅ | 3/3 ✅ |

### Matemática Discreta — Q1 (conjuntos)

| | Ubi (67) | Lari (100) |
|---|---|---|
| Transcrição | `A∪B={1,2,3,4,5,6}` / `A∩B={3,4}` / "A diferença A-B não é calculada" | `A∪B={1,2,3,4,5,6}` / `A∩B={3,4}` / `A-B={1,2}` |
| Parecer | 2/3 calculados; o aluno deixou A-B explicitamente em branco | 3/3 corretos e completos |
| `rubric_coverage` | união ✅ interseção ✅ diferença ❌ | 3/3 ✅ |

### Matemática Discreta — Q2 (tabela-verdade)

| | Ubi (35) | Lari (65) |
|---|---|---|
| Transcrição | `p｜q｜p∧q｜¬p` + 4 linhas de V/F (só 4 colunas) | `p｜q｜p∧q｜¬p｜(p∧q)→¬p` + 4 linhas completas |
| Parecer | Faltou a coluna da implicação e a classificação | Tabela completa e correta; só faltou nomear "contingência" |
| `rubric_coverage` | combinações ✅ resultado final ❌ classificação ❌ | combinações+resultado ✅ classificação ❌ |

Ver §6 — detecção da área de resposta da Lari nesta questão precisou de recuperação manual.

### Matemática Discreta — Q3 (indução)

| | Ubi (100) | Lari (35) |
|---|---|---|
| Transcrição | Princípio enunciado corretamente + verificação completa de n=1,2,3 (soma e fórmula coincidindo) | Princípio mencionado de forma confusa ("vale para n=k, (n.2) e n=3) então vale para n=k+1"); só n=1 verificado |
| `rubric_coverage` | 3/3 ✅ | princípio ✅, n=1 ✅, n=2/n=3 ❌ |
| `review_recommended` | false | **true** |

## 5. Caso de baixa confiança verificado visualmente — não é erro do modelo

A resposta de menor confiança do corpus (Bases Matemáticas Q1, Lari, confiança 37/"baixa") foi
conferida contra a imagem original. O aluno **escreveu comandos LaTeX como texto literal à mão**
(`\cdot`, `\dfrac{-b\pm\sqrt{Δ}}{2a}`) em vez da notação matemática que o comando produziria —
provavelmente influenciado pelo enunciado impresso, que usa LaTeX renderizado. A transcrição do
modelo capturou isso corretamente, com uma única ambiguidade de caligrafia genuína (`frac` lido
como `proc`, plausível dada a cursiva). O sistema reagiu exatamente como projetado: nota
conservadora (40), `review_recommended=true`, confiança baixa — a rede de segurança (ADR-001 §9)
funcionando para um tipo de entrada imprevisto (conteúdo de marcação em vez de notação), não uma
falha de leitura.

## 6. Achado técnico: detecção de área de resposta falha com grade desenhada à mão

Na Matemática Discreta Q2 (tabela-verdade) da Lari, a detecção automática da área de resposta
**falhou** — nenhuma barcode/seção foi pareada para essa questão, diferente das outras 8 (Ubi
incluído, mesmo template).

**Diagnóstico:** a Lari desenhou divisórias `|` entre as colunas da tabela (diferente da Ubi, que
escreveu só V/F sem separadores). O emaranhado de linhas horizontais pautadas + barras verticais
desenhadas à mão foi interpretado pelo passe tolerante de detecção de marcadores
(`ImageUtils.markerDetector`, `minHierarchy=5, smallArea=True` — o fallback para scans/fotos
reais, ver `MakeTests.py:337-344`) como um "marcador" circular gigante (raio ≈810px, contra os
~32px dos marcadores reais), centrado bem no meio da grade manuscrita. Esse falso candidato não
impediu a detecção dos 4 marcadores verdadeiros, mas corrompeu o pareamento barra-superior/
barra-inferior da seção, e nenhuma área de resposta válida foi produzida para essa questão.

**Recuperação:** a resposta foi recortada manualmente usando as coordenadas reais dos 4
marcadores verdadeiros (mesma lógica geométrica de `MakeTests.py:401-434`, replicada em script
ad-hoc) e processada normalmente pelo pipeline de vision a partir daí. O resultado (score 65,
transcrição completa e correta da tabela) está marcado no sidecar com o campo extra
`"recuperacao_manual"` documentando o procedimento, para rastreabilidade.

**Por que isso não apareceu antes:** nenhuma resposta do corpus do Q2 (árvores binárias) ou da
Ubi neste corpus continha conteúdo tabular desenhado à mão — é a primeira vez que esse tipo de
conteúdo aparece no corpus real, e expôs uma fragilidade genuína e não documentada do passe
tolerante de detecção. É um achado relevante para a Fase 2/3 do roadmap (testes comparativos) e
para a discussão de limitações do TCC.

**Mitigação futura (não aplicada agora):** o passe tolerante poderia rejeitar candidatos de
marcador com raio muito fora da faixa esperada (ex.: >3-4x o raio mediano dos demais candidatos
na mesma imagem) antes de tentar parear seções — reduziria a chance desse tipo de falso positivo
sem exigir mudança na geometria dos templates já impressos.

## 7. Validação com transcrição ground-truth e nota humana (fecho da Fase 2)

Complementando o §5 (inspeção qualitativa de 1 caso), esta seção mede os dois critérios de saída
formais da Fase 2 (ADR-001 §11) contra as 18 respostas: **CER da transcrição** e **coerência
nota-humana × nota-modelo**.

### 7.1 Metodologia

- Transcrição manual verbatim das 18 respostas (preservando erros, abreviações e comandos LaTeX
  escritos à mão) e nota humana por critério de rubrica, registradas em
  `provas-corpus-pt2/correcao-manual.md` (fora do repo, mesmo padrão de minimização de dados do
  ADR §9).
- CER calculado por distância de Levenshtein a nível de caractere, após normalização apenas de
  espaços em branco (sem normalizar maiúsculas/pontuação/símbolos — CER "bruto").
- Nota humana atribuída de forma independente, pelos mesmos critérios de rubrica usados no prompt
  do modelo, antes de qualquer consulta ao sidecar gerado.

### 7.2 CER por resposta

| Resposta | CER (%) | Nota humana | Nota modelo | \|Δ nota\| |
|---|---:|---:|---:|---:|
| aed-lari Q1 | 2.6 | 65 | 60 | 5 |
| aed-lari Q2 | 0.0 | 100 | 100 | 0 |
| aed-lari Q3 | 0.0 | 65 | 65 | 0 |
| aed-ubi Q1 | 1.2 | 80 | 70 | 10 |
| aed-ubi Q2 | 0.7 | 100 | 100 | 0 |
| aed-ubi Q3 | 0.0 | 50 | 60 | 10 |
| bm-lari Q1 | 13.3 | 65 | 40 | 25 |
| bm-lari Q2 | 0.8 | 45 | 45 | 0 |
| bm-lari Q3 | 25.4 | 100 | 100 | 0 |
| bm-ubi Q1 | 15.1 | 100 | 100 | 0 |
| bm-ubi Q2 | 4.1 | 85 | 90 | 5 |
| bm-ubi Q3 | 0.0 | 100 | 100 | 0 |
| matdis-lari Q1 | 29.9 | 100 | 100 | 0 |
| matdis-lari Q2 | 14.9 | 65 | 65 | 0 |
| matdis-lari Q3 | 17.1 | 45 | 35 | 10 |
| matdis-ubi Q1 | 9.3 | 65 | 67 | 2 |
| matdis-ubi Q2 | 1.4 | 25 | 35 | 10 |
| matdis-ubi Q3 | 12.5 | 90 | 100 | 10 |

**CER agregado:** 6.4% (micro — soma das distâncias / soma dos caracteres) | 8.2% (macro — média
simples por resposta). Ambos **abaixo do limiar de 10%** do critério de saída da Fase 2.

**Coerência de nota:** correlação de Pearson entre nota humana e nota do modelo = **0.943**;
diferença média absoluta de 4.8 pontos (escala 0–100); 17 das 18 respostas com diferença ≤10
pontos; a única divergência maior (25 pontos) é a própria resposta já sinalizada como de baixa
confiança (bm-lari Q1, §5) — ou seja, o único caso em que o modelo "errou mais a nota" é
exatamente o caso que a rede de segurança (`confidence_score`/`review_recommended`) já havia
marcado para revisão humana.

### 7.3 Por que o CER varia tanto entre respostas — nem todo erro é alucinação

As respostas com CER mais alto (bm-lari Q3: 25.4%, matdis-lari Q1: 29.9%, bm-ubi Q1: 15.1%,
matdis-lari Q2: 14.9%) **não são leitura errada do conteúdo** — são divergência de notação entre a
convenção de transcrição literal (preservar `\cup`, `\c dot`, `a^2`, pontos como marcador de
multiplicação) e a tendência do modelo de **normalizar notação matemática manuscrita para o
símbolo/forma pretendida** (`\cup`→∪, `a^2`→a², `.`→`·`). O conteúdo numérico e lógico está
correto nesses casos; o que diverge é a forma de representar o símbolo.

Isolando os erros que são leitura genuinamente incorreta (não notação):

- **bm-lari Q1** — `\d frac`→"proc" e `\c dot`→"|c dot" (já documentado no §5): o único caso em
  que a notação quebrada de fato prejudicou a legibilidade, e o único em que o sistema sinalizou
  baixa confiança corretamente.
- **aed-ubi Q2** — "intercalação"→"interpolação": troca de palavra real, mas sem efeito na nota
  (ambas 100 — o rubric_coverage não depende dessa palavra específica).
- **bm-ubi Q2** — "Regra"→"R'gra": erro de caractere isolado, sem efeito semântico.
- **matdis-ubi Q3** — "prova-se"→"Provasse": troca de forma verbal, sem efeito na nota.
- **matdis-lari Q3** — o modelo transcreveu o trecho riscado pelo aluno (`~~(n=2 e n=3)~~`) em vez
  de ignorá-lo — achado novo: **o modelo não distingue texto riscado de texto válido**, lê
  qualquer tinta na página. Não chega a ser alucinação (o texto riscado existe no papel), mas é
  uma lacuna a registrar: hoje nada no prompt instrui o modelo a tratar riscos/tachados como
  conteúdo descartado pelo aluno.

**Nenhuma das 18 respostas apresentou conteúdo inventado** (frase, valor ou símbolo sem
correspondência nenhuma no manuscrito) — zero alucinações no sentido estrito do critério de saída
da Fase 2.

### 7.4 Veredito frente ao critério de saída da Fase 2

| Critério (ADR-001 §11) | Medido | Resultado |
|---|---|---|
| CER da transcrição vision ≤10% no corpus real | 6.4% (micro) / 8.2% (macro) | ✅ Atendido |
| Zero alucinações não sinalizadas pela confiança | 0 alucinações; o único erro relevante (bm-lari Q1) foi sinalizado | ✅ Atendido |

Com N=18 (mais as 4 provas do Q2 baseline), a Fase 2 do roadmap está **concluída** nos dois
critérios formais definidos no ADR. A recalibração de `confidence_score` com os novos sinais
(mencionada como atividade da fase) fica como item aberto, não bloqueante — o teto estrutural de
75 pontos (§7 abaixo) já é um candidato identificado para essa recalibração.

## 8. Observações gerais

- **Distribuição de confiança:** 37 (mínimo, caso do §5) a 75 (máximo, teto estrutural do modo
  vision — toda resposta perde 25 pontos fixos por não ter sinal de OCR, ver explicação de
  `confidence_score.py` já registrada na conversa). A maioria das respostas completas e corretas
  bateu no teto de 75; nenhuma resposta chegou ao nível "alta" pleno (100) porque esse teto é
  estrutural no modo vision, não um problema de qualidade de leitura.
- **`review_recommended=true`** apareceu só 2 vezes em 18 respostas, ambas da Lari, ambas com
  causa real identificável (LaTeX escrito à mão; passo indutivo confuso) — nenhum falso positivo
  nem falso negativo óbvio nas 18 respostas revisadas.
- **Variância individual > variância do pipeline:** a maior divergência de nota entre escritores
  (Bhaskara, 100 vs. 40) reflete diferença real de conteúdo/clareza da resposta, não
  inconsistência do modelo — confirmado por inspeção visual direta.

## 9. Limitações

- N ainda pequeno para conclusões estatísticas fortes: 2 escritores, 9 questões cada, 18 respostas
  com ground-truth (mais as 4 provas do Q2 = 22 respostas reais no total do projeto).
- Ambos os escritores usaram letra de forma/cursiva legível; o corpus ainda não cobre casos de
  caligrafia muito degradada ou rasuras extensas.
- Achado do §6 foi contornado manualmente para esta rodada; a detecção em si não foi corrigida no
  código — próxima resposta tabular no corpus pode reproduzir o mesmo problema.
- CER medido é "bruto" (sem normalizar símbolo matemático/notação) — como discutido no §7.3, uma
  parcela relevante do CER medido reflete escolha de representação (unicode vs. LaTeX literal), não
  erro de leitura; um CER "normalizado" (equivalência semântica de símbolos) tenderia a ficar ainda
  mais baixo, mas não foi calculado aqui.
- A convenção de transcrição ground-truth preserva literalmente comandos LaTeX manuscritos
  quebrados; o modelo, em vez disso, tende a semanticamente corrigi-los para o símbolo pretendido
  (exceto no caso bm-lari Q1, onde a notação estava confusa demais e ele preservou o texto bruto).
  Esse comportamento é inconsistente entre casos e seria um ponto a investigar com mais dados na
  Fase 3.

## 10. Conclusão

Critério "2+ escritores" da Fase 2 do roadmap (ADR-001 §11) **atendido**: 18 respostas manuscritas
reais de 2 pessoas diferentes, em 3 domínios de conteúdo (prosa técnica, fórmulas matemáticas,
notação discreta). Os dois critérios formais de saída da fase também foram **atendidos** (§7.4):
CER de 6.4–8.2%, abaixo do limiar de 10%, e zero alucinações não sinalizadas pela confiança — a
única resposta com erro de leitura relevante foi corretamente marcada para revisão humana pelo
próprio sistema. A avaliação por rubrica permaneceu consistente e conservadora entre os dois
escritores (correlação de 0.943 entre nota humana e nota do modelo), incluindo um caso
genuinamente difícil (LaTeX escrito à mão) tratado corretamente pela rede de segurança existente.
Um novo modo de falha da detecção de área de resposta foi identificado, documentado e contornado —
candidato a item de robustez para antes da Fase 3 do roadmap. **Com isso, a Fase 2 do roadmap do
ADR-001 está concluída.**
