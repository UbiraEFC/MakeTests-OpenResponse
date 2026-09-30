# Resultados — Corpus Fase 2 (roadmap Q3, ADR-001)

| Campo | Valor |
|---|---|
| **Status** | Corpus de 2 escritores processado; critério "2+ escritores" do roadmap atendido |
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

## 7. Observações gerais

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

## 8. Limitações

- N ainda pequeno para conclusões estatísticas: 2 escritores, 9 questões cada, 18 respostas totais
  (mais as 4 provas do Q2 = 22 respostas reais no total do projeto).
- Ambos os escritores usaram letra de forma/cursiva legível; o corpus ainda não cobre casos de
  caligrafia muito degradada ou rasuras extensas.
- Achado do §6 foi contornado manualmente para esta rodada; a detecção em si não foi corrigida no
  código — próxima resposta tabular no corpus pode reproduzir o mesmo problema.

## 9. Conclusão

Critério "2+ escritores" da Fase 2 do roadmap (ADR-001 §11) **atendido**: 18 respostas manuscritas
reais de 2 pessoas diferentes, em 3 domínios de conteúdo (prosa técnica, fórmulas matemáticas,
notação discreta). A avaliação por rubrica permaneceu consistente e conservadora entre os dois
escritores, incluindo um caso genuinamente difícil (LaTeX escrito à mão) tratado corretamente pela
rede de segurança existente. Um novo modo de falha da detecção de área de resposta foi identificado,
documentado e contornado — candidato a item de robustez para antes da Fase 3 do roadmap.
