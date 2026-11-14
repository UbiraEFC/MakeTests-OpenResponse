# Resultados estatísticos — Fase 5 do roadmap (ADR-001)

| Campo | Valor |
|---|---|
| **Status** | Fase 5 do roadmap concluída — encaminhamento ao HITL cai de 100% (Q2, OCR) para 11% (vision recalibrado), sem perder a única revisão de fato necessária; concordância nota humana × modelo: Pearson 0,943, kappa ponderado 0,879 |
| **Data** | 2026-11-14 |
| **Branch** | `pgc3/dissertativa-fase1` |
| **Reprodução** | `python3 experiments/fase5_resultados.py` (sem chamadas de API; lê os sidecars locais da Fase 2) |
| **Documentos relacionados** | `RESULTADOS-TESTE-CORPUS-FASE2.md` §7 (ground-truth, CER, notas humanas), `RESULTADOS-TESTE-PROVAS-REAIS-OCR.md` §5 (baseline Q2), `ADR-001-substituicao-ocr-por-llm-vision.md` §8.4 e §11 |

## 1. Objetivo

Fechar o critério de saída da Fase 5 (ADR-001 §11): "redução mensurável e estatisticamente descrita do volume de HITL vs. Q2 (baseline: 100%)", cobrindo as três atividades previstas: concordância nota-modelo × nota-humana, distribuição de erro por estilo de escrita e taxa de encaminhamento ao HITL antes/depois da migração.

## 2. Metodologia

- **Corpus:** as 18 respostas manuscritas reais da Fase 2 (3 provas × 3 questões × 2 escritores), com transcrição ground-truth e nota humana por rubrica atribuídas de forma independente (`RESULTADOS-TESTE-CORPUS-FASE2.md` §7.1).
- **Estilos:** escritor "Ubi" = letra de forma; escritora "Lari" = cursiva (com comandos LaTeX escritos à mão nas provas de matemática).
- **Sinais do modelo:** lidos dos sidecars `_assist.json` reais (Anthropic `claude-sonnet-5`, modo vision). A confiança foi **recalculada offline** a partir dos sinais persistidos (`review_recommended` do LLM, `rubric_coverage`, `error`, `used_fallback`) — nenhuma chamada nova de API.
- **Revisão "necessária" (referência para precisão/recall):** nota do modelo diverge da nota humana em mais de 10 pontos (≈ meio critério de rubrica). O limiar é parametrizado no script (`LIMIAR_DIVERGENCIA`).
- **Kappa ponderado:** quadrático, sobre 5 faixas de 20 pontos (0–19, 20–39, …, 80–100).

## 3. Recalibração do score de confiança para o modo vision

O item "recalibrar `confidence_score` com os novos sinais" estava aberto desde a Fase 2 (ADR §8.4). O defeito:

- Em modo vision não existe etapa de OCR, mas `confidence_score.compute()` tratava a **ausência** de sinal de OCR como **incerteza** de leitura e aplicava 25 pontos fixos de penalidade (`ocr_sem_sinal_de_confianca`) em toda resposta.
- Resultado: teto estrutural de 75 pontos, e com o limiar de revisão em 70, qualquer critério de rubrica não atendido já mandava a resposta para o HITL — mesmo com leitura perfeita e o LLM seguro.

**Correção aplicada** (`maketests_ext/confidence_score.py`): novo campo `ConfidenceSignals.modality` (`"ocr"` default / `"vision"`). Em `"vision"`, as penalidades de OCR não se aplicam; todas as outras permanecem (erro do LLM, pedido de revisão do LLM, cobertura de rubrica, fallback). O caminho legado (`LLM_VISION_MODE=off`) é inalterado. `MakeTests.py` passa a informar a modalidade e a persistir no sidecar a decisão final de encaminhamento (`confidence_review_recommended`) — antes só a opinião crua do LLM (`review_recommended`) era gravada. Testes de regressão T5.6/T5.7 adicionados; suíte em 57/57.

## 4. Concordância nota humana × nota do modelo (N=18)

| Métrica | Valor |
|---|---:|
| Pearson r | **0,943** (p = 4,4×10⁻⁹) |
| Spearman ρ | 0,957 (p = 4,9×10⁻¹⁰) |
| Kappa ponderado quadrático (5 faixas) | **0,879** |
| Mesma faixa de 20 pontos | 14/18 |
| MAE | 4,8 pontos (escala 0–100) |
| Mediana de \|Δ\| | 1 ponto |
| \|Δ\| ≤ 10 pontos | 17/18 |
| Maior \|Δ\| | 25 (bm-lari Q1) |
| Viés médio (modelo − humano) | −0,7 ponto |

Kappa ponderado de 0,879 está na faixa usualmente lida como concordância "quase perfeita" (> 0,80, escala de Landis & Koch). O viés médio próximo de zero indica que o modelo não é sistematicamente mais severo nem mais leniente que o corretor humano neste corpus.

## 5. Erro por estilo de escrita

| Estilo | N | CER médio | MAE da nota | Viés da nota (modelo − humano) |
|---|---:|---:|---:|---:|
| Letra de forma (Ubi) | 9 | 4,9% | 5,2 | +3,0 |
| Cursiva (Lari) | 9 | 11,6% | 4,4 | −4,4 |

**Leitura:** o estilo afeta a **transcrição literal**, mas não a **nota**. A cursiva tem o dobro do CER, mas o erro de nota é equivalente (até um pouco menor). Duas ressalvas importantes:

- O CER da cursiva está inflado por divergência de **notação**, não de leitura: a escritora cursiva escreveu comandos LaTeX à mão, que a transcrição ground-truth preserva literalmente e o modelo normaliza para o símbolo (`\cup` → ∪) — ver `RESULTADOS-TESTE-CORPUS-FASE2.md` §7.3. Estilo de letra e escolha de notação estão **confundidos** neste corpus (cada escritor tem um só estilo).
- O viés tem sinais opostos (+3,0 forma / −4,4 cursiva): o modelo tende levemente a pontuar menos a cursiva. A magnitude é pequena e N=9 por grupo não permite afirmar diferença estatística — fica como hipótese para corpus maior.

## 6. Encaminhamento ao HITL — antes × depois

Revisões de fato necessárias (\|Δ\| > 10): **1 de 18** (bm-lari Q1 — LaTeX manuscrito confuso, transcrição degradada; já analisado no `RESULTADOS-TESTE-CORPUS-FASE2.md` §5).

| Configuração | Encaminhadas ao HITL | Precisão | Recall |
|---|---:|---:|---:|
| Q2 — OCR (Tesseract) + LLM texto | 4/4 = **100%** | — | — |
| Vision — fórmula antiga (teto 75) | 10/18 = 56% | 0,10 | 1,00 |
| Vision — **recalibrada** | 2/18 = **11%** | **0,50** | **1,00** |

Confiança média: 66,8 (máx. 75) com a fórmula antiga → 91,8 (máx. 100) recalibrada.

As duas respostas encaminhadas pela versão recalibrada são exatamente as duas em que o próprio LLM pediu revisão: bm-lari Q1 (a necessária, \|Δ\| = 25) e matdis-lari Q3 (\|Δ\| = 10, no limite — passo indutivo confuso e texto riscado lido como válido). Nenhuma resposta com divergência relevante escapou do HITL.

**Redução do volume de HITL: de 100% (Q2) para 11%**, mantendo recall de 1,00 sobre as revisões necessárias.

## 7. Limitações

- **Recall sustentado por um único caso.** Só 1 das 18 respostas exigia revisão; recall 1,00 = 1/1. O número mostra que o mecanismo funcionou no caso real que apareceu, não que o recall seja estatisticamente alto. Corpus com mais respostas problemáticas (rasura extensa, caligrafia degradada) é necessário para estimá-lo com intervalo.
- **No modo vision recalibrado, o encaminhamento depende de fato do auto-relato do LLM.** A penalidade máxima de cobertura de rubrica (20) não derruba sozinha a confiança abaixo do limiar de 70 — o que é coerente (resposta incompleta é problema de **conteúdo**, não de **leitura**), mas significa que um erro de transcrição que o LLM não perceba não seria sinalizado por nenhum outro sinal. Mitigações já existentes: imagem original e transcrição sempre no sidecar (auditoria), e o professor continua vendo todas as respostas pendentes no `review_hitl.py list`, ordenadas por confiança. Candidatos futuros a sinal independente: autoavaliação de legibilidade em campo próprio no JSON, estabilidade entre execuções (`score_stability_std`, hook já reservado).
- **Baselines não pareados.** O Q2 (100%) foi medido em 4 respostas de outra prova (árvores binárias); o vision em 18 respostas das provas da Fase 2. A Fase 1 já mostrou o vision nas mesmas 4 provas do Q2, mas sem nota humana por critério nelas, então não entram no cálculo de precisão/recall.
- **N pequeno e 2 escritores**, cada um com um só estilo — estilo e escritor estão confundidos.
- Recalibração avaliada **no mesmo corpus** que motivou a correção (sem conjunto de validação separado). A mudança é estrutural (remover penalidade de um sinal que não existe), não um ajuste fino de pesos, o que reduz — mas não elimina — o risco de sobreajuste.

## 8. Conclusão

Critério de saída da Fase 5 (ADR-001 §11) **atendido**: redução mensurável e estatisticamente descrita do volume de HITL — de 100% no Q2 (OCR) para 11% com LLM Vision recalibrado, sem perder a única revisão necessária do corpus —, com concordância alta entre nota do modelo e nota humana (Pearson 0,943, kappa ponderado 0,879, MAE 4,8 pontos) e sem diferença relevante de erro de nota entre letra de forma e cursiva. A recalibração do score de confiança, pendente desde a Fase 2, foi implementada e coberta por testes. **Com isso, o roadmap do ADR-001 está concluído** (Fases 1, 2, 4 e 5 entregues; Fase 3 não realizada por decisão justificada).
