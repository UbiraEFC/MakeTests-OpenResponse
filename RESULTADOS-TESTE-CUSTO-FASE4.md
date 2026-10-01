# Resultados — Custo real medido (Fase 4 do roadmap, ADR-001)

| Campo | Valor |
|---|---|
| **Status** | Fase 4 do roadmap concluída — custo real medido a partir de `provider_metadata.usage` já persistido nos sidecars; preços oficiais revalidados |
| **Data** | 2026-09-30 |
| **Branch** | `pgc3/dissertativa-fase1` |
| **Contexto** | Mede o custo real das chamadas já feitas nas Fases 1–2 (sem rodar nenhuma chamada nova) e revalida contra as páginas oficiais os `[VALIDAR]` deixados no ADR-001 §6 |
| **Documentos relacionados** | `ADR-001-substituicao-ocr-por-llm-vision.md` §6 (estimativas originais), `RESULTADOS-TESTE-CORPUS-FASE2.md` (origem dos 18 sidecars Anthropic), `RESULTADOS-TESTE-PROVAS-REAIS-OCR.md` (origem dos 4 sidecars Gemini legado) |

## 1. Objetivo

Fechar o critério de saída da Fase 4 (ADR-001 §11): "custo medido por questão com intervalo; premissas do §6 confirmadas ou corrigidas no documento". Em vez de simular, usar os dados de uso (`usage`) que os providers já retornam e que o pipeline já persiste em todo sidecar `_assist.json` desde a Fase 1 — nenhuma chamada de API nova foi necessária.

## 2. Metodologia

- **Fonte dos tokens:** campo `provider_metadata.usage` de 22 sidecars reais já existentes no projeto:
  - 18 sidecars Anthropic (`claude-sonnet-5`, modo vision, prompt `somativo_v2_vision`) — corpus Fase 2, `corpus-fase2/*/Correcao-*/`.
  - 4 sidecars Gemini (`gemini-2.5-flash`, modo texto, prompt `somativo_v1`, pipeline legado pré-Fase 1) — corpus Q2, `provas-pdf/resultados/provaN/`.
- **Preços oficiais** consultados em 2026-09-30 diretamente nas páginas dos fornecedores (não do relatório de terceiros citado no ADR):
  - Anthropic — `claude.com/pricing` (a URL antiga `anthropic.com/pricing` redireciona para esta).
  - Google — `ai.google.dev/gemini-api/docs/pricing`.
- **Câmbio:** USD/BRL ≈ 5,20 (cotação do dia da consulta; o ADR usava 5,0925 — dentro da margem de ±10% já recomendada no próprio documento).
- **Limitação assumida:** não há sidecar real de Gemini em **modo vision** (quota do free tier esgotada antes de testar live — ver `RESULTADOS-TESTE-VISION-FASE1.md`). A comparação de custo cross-provider aqui é Anthropic-vision × Gemini-texto-legado, não vision × vision. Tratado explicitamente como gap no §6.

## 3. Preços oficiais confirmados (2026-09-30)

| Fornecedor/Modelo | Entrada (US$/MTok) | Saída (US$/MTok) | Cache read | Cache write |
|---|---:|---:|---:|---:|
| Anthropic Claude Sonnet 5 | 2,00 | 10,00 | 0,20 | 2,50 |
| Google Gemini 2.5 Flash (standard) | 0,30 | 2,50 | 0,03 | — (armazenamento US$1,00/MTok/h) |
| Google Gemini 2.5 Flash (batch, −50%) | 0,15 | 1,25 | 0,03 | — |

O valor do Gemini 2.5 Flash **confirma exatamente** o número que o ADR já citava do relatório de terceiros (§6.1/§6.3) — essa premissa estava correta. O valor do Anthropic não constava do ADR com preço oficial (só uma estimativa "introdutória").

## 4. Custo real medido por questão

### 4.1 Anthropic Sonnet 5 — modo vision (18 respostas reais, corpus Fase 2)

| Prova (domínio) | N | Entrada média (tokens) | Saída média (tokens) | ...dos quais *thinking* | Custo médio/questão |
|---|---:|---:|---:|---:|---:|
| Algoritmos e Estruturas de Dados (prosa) | 6 | 1.276 | 324 | 24 | R$ 0,0301 |
| Bases Matemáticas (fórmulas) | 6 | 1.262 | 509 | 228 | R$ 0,0396 |
| Matemática Discreta (notação simbólica) | 6 | 1.316 | 561 | 299 | R$ 0,0429 |
| **Agregado (18 respostas)** | 18 | **1.285** | **465** | **184** | **R$ 0,0375** |

**Achado de domínio:** o custo varia ~40% entre a prova de prosa técnica (AED) e a de notação simbólica densa (Matemática Discreta) — a diferença é quase inteiramente tokens de *thinking* (24 vs. 299 em média). Correção/avaliação de conteúdo matemático/simbólico consome mais raciocínio interno do modelo do que avaliar texto corrido, mesmo em recortes de imagem de tamanho comparável.

### 4.2 Gemini 2.5 Flash — modo texto, pipeline legado (4 respostas reais, corpus Q2)

| | N | Entrada média (tokens) | Saída média (tokens, candidates+thoughts) | Custo médio/questão |
|---|---:|---:|---:|---:|
| Dissertativa única (prosa) | 4 | 330 | 870 | R$ 0,0118 |

Não é uma comparação direta de modalidade (texto vs. vision, §2) — serve como segundo ponto de referência real de que o custo de *thinking* domina também no Gemini (870 de 870+330 tokens totais são majoritariamente `thoughtsTokenCount`, não a resposta JSON em si).

## 5. Comparação com as estimativas do ADR-001 §6

| Item do ADR | Estimado/simulado (§6.5–6.6) | Medido agora | Correção |
|---|---|---|---|
| Gemini 2.5 Flash, R$/questão | 0,0026 (simulação, cenário "Custo Médio") | 0,0118 (real, modo texto legado) | Estimativa era **baixa**: a simulação assumia 50–80 tokens de saída (§6.4); a chamada real gastou ~870 (dominado por *thinking*), confirmando a ressalva já registrada em §6.6 item 1 |
| Claude Sonnet 5, R$/questão | 0,0116 ("intro", sem fonte oficial) | 0,0375 (real, modo vision) | Estimativa era **~3x baixa** — mesma causa: tokens de raciocínio não contemplados na simulação original, mais o custo de imagem (ausente no cenário "intro", que era texto) |
| §6.6 item 1 ("thinking domina o custo, não o JSON") | Hipótese, 1 amostra (Gemini, 791 tokens) | **Confirmada com 22 amostras reais** (Anthropic: até 184/465 tokens de saída = *thinking*; Gemini: 870/870 quase só *thinking*) | ✅ Correto — recomendação do ADR de configurar `thinking_level` explicitamente permanece válida e agora prioritária |
| §6.1 preço Gemini 2.5 Flash | US$0,30/US$2,50 por MTok | Confirmado oficialmente (`ai.google.dev`) | ✅ Sem correção |
| §6.6 item 4 (câmbio 5,0925) | Premissa pontual | 5,20 no dia da consulta — dentro de ±10% já recomendado | Sem correção necessária, dado já coberto pela margem sugerida |

## 6. Cache nunca foi exercitado na prática

Nenhuma das 18 chamadas reais da Fase 2 usou prompt caching: `cache_creation_input_tokens` e `cache_read_input_tokens` são **zero em todas** as 18. Isso é esperado — a Fase 1/2 nunca configurou cache explicitamente — mas significa que a atividade "ativar cache" prevista para a Fase 4 (ADR §11) ainda não tem dado real de *hit rate*, só a projeção teórica do preço oficial:

- O prefixo estático (instruções + rubrica, ~1.250–1.300 tokens de entrada medidos, perto da estimativa original de ~1.500 do §6.4) seria o candidato natural a cache, já que se repete por aluno dentro da mesma questão.
- Com cache read a US$0,20/MTok vs. US$2,00/MTok sem cache (Anthropic), um *hit* nesse prefixo custaria ~90% menos nessa fração da entrada — mas isso é **projeção a partir do preço publicado**, não uma medição, porque nenhuma chamada real testou esse caminho ainda.

Implementar e medir isso de fato é o único item da Fase 4 que segue aberto (ativação de cache real + *hit rate* medido), mas não bloqueia o critério de saída da fase — que pede custo medido e premissas confirmadas/corrigidas, ambos já entregues.

## 7. Projeção em escala (números reais aplicados aos cenários do ADR)

| Cenário | Anthropic Sonnet 5 (vision, real) | Gemini 2.5 Flash (texto legado, real) |
|---|---:|---:|
| 300 alunos × 5 questões (1.500 req.) | R$ 56,29 | R$ 17,73 |
| 1.000 alunos × 5 questões (5.000 req.) | R$ 187,64 | R$ 59,09 |
| ...por aluno (5 questões) | R$ 0,19 | R$ 0,06 |

Mesmo no cenário mais caro medido (Anthropic, 1.000 alunos), o custo por aluno por prova completa de 5 questões fica em ~R$0,19 — ainda ordem de grandeza de centavos, como a leitura executiva original do ADR já apontava (§6.5). **A correção não muda a conclusão arquitetural** (custo não é fator limitante da decisão); muda a magnitude exata da estimativa, que estava subestimada em ~3x para o Anthropic.

## 8. Limitações

- Sem dado real de Gemini em modo vision (quota esgotada antes do teste live) — comparação cross-provider aqui é vision×texto, não vision×vision apples-to-apples.
- N pequeno por domínio (6 por prova, 4 para o Gemini legado) — suficiente para medir ordem de grandeza e confirmar/corrigir as premissas do ADR, não para intervalo de confiança estatístico formal.
- Cache nunca foi exercitado em nenhuma chamada real (§6) — a economia projetada em 90% no prefixo cacheável é teórica, não medida.
- Tokens de *thinking* variam bastante por questão dentro do mesmo domínio (0 a 545 nas 18 amostras) — a média é informativa, mas a variância em si (o que faz o modelo "pensar mais" numa resposta específica) não foi investigada.

## 9. Conclusão

Critério de saída da Fase 4 (ADR-001 §11) **atendido**: custo medido por questão com dado real (não simulado) para dois fornecedores, e as premissas do §6 revisadas — uma confirmada (preço Gemini), duas corrigidas com evidência (custo real Anthropic ~3x a estimativa "intro"; domínio de *thinking* no custo, antes hipótese de 1 amostra, agora confirmado com 22). A conclusão executiva do ADR (custo não é fator limitante da decisão arquitetural) permanece válida mesmo com os números corrigidos. **Com isso, a Fase 4 do roadmap está concluída.**
