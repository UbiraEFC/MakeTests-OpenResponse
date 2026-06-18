# Plano de testes e validações — extensão dissertativa (MakeTests)

Cada fase possui **entregável**, **testes**, **critérios de aceite** e **evidência** a registrar. Só avance para a fase seguinte quando a fase atual estiver **verde**.

**Ambiente:** WSL — ver `GUIA-EXECUCAO-WSL.md`  
**Implementação:** `GUIA-IMPLEMENTACAO.md`

---

## Processo: como fechar uma fase

1. Implementar o entregável da fase (ver `GUIA-IMPLEMENTACAO.md`).
2. Abrir `validate-maketests.sh` (dentro de `MakeTests/`) e escrever o corpo de `validate_faseN()` correspondente, substituindo o placeholder "ainda não implementada" pelos testes TN.x reais da fase (tabela de cada fase abaixo).
3. Rodar `bash validate-maketests.sh` e confirmar que **nada falhou** — inclusive as fases anteriores, que devem continuar verdes (é a garantia de não-regressão).
4. Só então preencher a linha da fase na tabela **Registro de progresso** (data, testes OK, evidência).

Ou seja: `validate-maketests.sh` cresce junto com a implementação — é o snapshot vivo de "o que já está garantido funcionar", e o Registro de Progresso é o histórico textual de quando e com que evidência cada fase foi fechada.

---

## Marco do núcleo (entrega Q2)

Ao concluir a **Fase 6**, o núcleo do TCC deve demonstrar:

> **Prova dissertativa manuscrita** → OCR → normalização → LLM (ou mock configurável) → **nota sugerida + confiança + parecer** → persistência → **revisão HITL** → nota consolidada no CSV.

**Teste de integração do núcleo (E2E-Q2):** ver seção [Entrega integrada](#entrega-integrada-e2e-q2) ao final.

---

## Visão geral das fases

| Fase | Entregável principal | Tipo de teste dominante |
|------|----------------------|-------------------------|
| 0 | Ambiente WSL funcional | Smoke / manual |
| 1 | `QuestionDissertative` + PDF com área livre | Unitário + geração PDF |
| 2 | `ocr_extract.py` | Unitário + golden images |
| 3 | `text_normalize.py` | Unitário (pares entrada/saída) |
| 4 | `llm_grader.py` | Contrato JSON + mock/API |
| 5 | `confidence_score.py` | Unitário + cenários sintéticos |
| 6 | HITL + sidecar + template `-e dissertative` | Integração + E2E-Q2 |
| 7 | `experiments/ocr_styles_eval.py` | Benchmark offline |
| 8 | HMER / formativo / validação Q3 | Exploratório / pesquisa |

---

## Fase 0 — Ambiente de desenvolvimento

### Entregável

- WSL configurado; MakeTests **original** gera PDF de prova.
- Documentação: `GUIA-EXECUCAO-WSL.md` seguida com sucesso.

### Testes

| ID | Teste | Como executar | Critério de aceite |
|----|-------|---------------|-------------------|
| T0.1 | Imports Python | `python3 -c "import cv2, pyzbar, pytesseract, qrcode"` | Sem exceção |
| T0.2 | Tesseract PT | `tesseract --list-langs \| grep por` | `por` presente |
| T0.3 | ZBar | `./MakeTests.py -v` (geração) | QR/códigos na prova gerada |
| T0.4 | LaTeX | `./MakeTests.py -v` | `Tests.pdf` criado |
| T0.5 | Correção baseline | `./MakeTests.py -v -p <pdf_objetiva>` | `Correction/_scores.csv` atualizado |

### Evidência

- Log ou screenshot dos comandos T0.1–T0.4.
- Opcional: commit em `pgc/guia-implementacao` com nota “Fase 0 OK” no checklist.

### Bloqueio se falhar

Não iniciar Fase 1 sem T0.1–T0.4 verdes.

---

## Fase 1 — Classe `QuestionDissertative`

### Entregável

- Classe em `MakeTests.py` (ou módulo importado).
- Módulo exemplo `Questions/.../dissertative_example.py`.
- Template `./MakeTests.py -e dissertative`.
- `doCorrection` retorna **tupla de 3 elementos** `(score, img_proc, img_feedback)` — contrato do `CorrectionManager`.

### Testes

| ID | Teste | Tipo | Critério de aceite |
|----|-------|------|-------------------|
| T1.1 | Contrato `Question` | Unitário | Todos os métodos abstratos implementados |
| T1.2 | `answerAreaAspectRate` | Unitário | Valor > 1 (área alta) |
| T1.3 | `drawAnswerArea` | Unitário | Imagem BGR alterada; sem matriz de círculos |
| T1.4 | `getQuestionTex` | Unitário | LaTeX compila (sem erro em geração PDF) |
| T1.5 | Geração PDF | Integração | Prova inclui questão dissertativa com linhas em branco |
| T1.6 | `doCorrection` mock | Unitário | Retorna 3 valores; score numérico 0–100 |
| T1.7 | Regressão tipos existentes | Smoke | `./MakeTests.py -v` com config só objetivas ainda funciona |

### Mock obrigatório nesta fase

`doCorrection` **não** chama OCR/LLM reais — retorna score fixo ou lê flag `MOCK_GRADER=1`.

### Evidência

- PDF gerado com questão dissertativa.
- Saída de teste T1.6 (log).

---

## Fase 2 — Extração OCR/HTR

### Entregável

- Módulo `maketests_ext/ocr_extract.py` (ou equivalente).
- Função `extract_text(image_bgr) -> dict` com campos `text`, `engine`, `confidence_mean` (quando disponível).

### Testes

| ID | Teste | Tipo | Critério de aceite |
|----|-------|------|-------------------|
| T2.1 | Imagem vazia | Unitário | `text` vazio; sem crash |
| T2.2 | Texto impresso sintético | Golden | CER < limiar acordado (ex.: 15%) em amostra controlada |
| T2.3 | Manuscrito letra de forma | Golden | Transcrição parcialmente legível; log de confiança |
| T2.4 | Integração `QuestionDissertative` | Integração | `doCorrection` preenche sidecar com `text` OCR |
| T2.5 | Regressão | Smoke | OCR não quebra fluxo se Tesseract ausente → erro claro |

### Conjunto golden (criar uma vez)

```
tests/fixtures/ocr/
  printed_pt_01.png + printed_pt_01.txt
  forma_pt_01.png   + forma_pt_01.txt
  cursiva_pt_01.png + cursiva_pt_01.txt   # exploratório
```

### Evidência

- Relatório T2.2 (CER) em `experiments/ocr/` ou comentário no PR.

---

## Fase 3 — Normalização textual

### Entregável

- `maketests_ext/text_normalize.py` com `normalize(raw: str) -> str`.

### Testes

| ID | Teste | Entrada → saída esperada | Critério |
|----|-------|--------------------------|----------|
| T3.1 | Espaços duplos | `"foo  bar"` → `"foo bar"` | Igual |
| T3.2 | Hifenização OCR | `"exem-\nplo"` → `"exemplo"` | Igual |
| T3.3 | Unicode | caracteres NFKC | Normalizado |
| T3.4 | Preservação | sidecar guarda `raw` e `normalized` | Ambos persistidos |
| T3.5 | Pipeline | OCR mock → normalize → string estável | Sem exceção |

### Evidência

- Arquivo de testes unitários ou tabela markdown com casos T3.1–T3.3.

---

## Fase 4 — Avaliação semântica (LLM)

### Entregável

- `maketests_ext/llm_grader.py` com `grade(enunciado, rubrica, texto) -> dict`.
- Prompt versionado em `maketests_ext/prompts/somativo_v1.txt`.
- Modo **mock** (`LLM_PROVIDER=mock`) e modo **API**.

### Testes

| ID | Teste | Tipo | Critério de aceite |
|----|-------|------|-------------------|
| T4.1 | Mock determinístico | Unitário | JSON válido; campos obrigatórios presentes |
| T4.2 | Schema saída | Unitário | `suggested_score`, `rationale`, `rubric_coverage`, `review_recommended` |
| T4.3 | Score bounds | Unitário | `suggested_score` ∈ [0, 100] |
| T4.4 | Resposta vazia | Unitário | Score baixo + `review_recommended=true` |
| T4.5 | Gabarito alinhado (mock/API) | Integração | Resposta “modelo” recebe score alto |
| T4.6 | API real (1 chamada) | Manual | Resposta coerente; latência registrada |
| T4.7 | Sem API key | Unitário | Erro claro; não grava nota como definitiva |

### Campos obrigatórios do JSON

```json
{
  "suggested_score": 0,
  "rationale": "",
  "rubric_coverage": {},
  "review_recommended": true
}
```

### Evidência

- Log T4.1 + uma execução T4.6 (redigir dados sensíveis).

---

## Fase 5 — Score de confiança

### Entregável

- `maketests_ext/confidence_score.py` com `compute(signals) -> int` (0–100) e `review_recommended`.

### Testes

| ID | Cenário | Entrada | Critério |
|----|---------|---------|----------|
| T5.1 | OCR ruim | confiança OCR baixa | Score confiança global baixo |
| T5.2 | OCR bom + LLM coerente | sinais altos | Score alto |
| T5.3 | Divergência parecer/nota | inconsistência | `review_recommended=true` |
| T5.4 | Estabilidade (opcional) | 3 runs LLM | Desvio registrado; penaliza se alto |
| T5.5 | Integração | pipeline completo mock | Sidecar contém `confidence` |

### Evidência

- Tabela de cenários T5.1–T5.3 com valores esperado vs obtido.

---

## Fase 6 — HITL e persistência (marco núcleo)

### Entregável

- Sidecar `Correction/<aluno>/q<N>_assist.json`.
- Colunas ou campos opcionais no CSV: `score_sugerido`, `confianca`, `status_hitl`.
- Script `review_hitl.py` (CLI).
- `./MakeTests.py -e dissertative` documentado.
- **E2E-Q2** passando.

### Testes

| ID | Teste | Tipo | Critério de aceite |
|----|-------|------|-------------------|
| T6.1 | Sidecar criado | Integração | JSON com OCR, normalized, suggested_score, confidence, rationale |
| T6.2 | CSV score sugerido | Integração | Coluna preenchida; nota final ainda exige HITL |
| T6.3 | `review_hitl.py list` | CLI | Lista pendentes por confiança |
| T6.4 | `review_hitl.py accept` | CLI | `status_hitl=aceito`; score consolidado |
| T6.5 | `review_hitl.py adjust` | CLI | Nota manual sobrescreve sugestão |
| T6.6 | Regressão objetivas | Smoke | Config mista obj+dissertativa funciona |
| T6.7 | **E2E-Q2** | E2E | Ver abaixo |

### Evidência

- Sidecar de exemplo anonimizado em `tests/fixtures/hitl/`.
- CSV antes/depois de revisão HITL.

---

## Fase 7 — Experimento OCR por estilo (exploratório Q2)

### Entregável

- `experiments/ocr_styles_eval.py` + CSV de resultados (CER/WER por estilo).

### Testes

| ID | Teste | Critério |
|----|-------|----------|
| T7.1 | Corpus mínimo ≥ 9 imagens (3 por estilo) | Executável |
| T7.2 | Métricas por categoria | Tabela CER/WER |
| T7.3 | Correlação qualitativa | Cursiva ≥ forma em CER (hipótese documentada) |

Não bloqueia E2E-Q2; bloqueia apenas conclusões sobre estilo de escrita no TCC.

---

## Fase 8 — Q3 (validação empírica — fora do núcleo Q2)

| ID | Teste | Critério |
|----|-------|----------|
| T8.1 | Concordância sugestão vs humano | κ ou MAE registrados |
| T8.2 | Calibração confiança | Faixas vs taxa de erro |
| T8.3 | Análise qualitativa de erros | Taxonomia preenchida |

Planejamento detalhado alinhado a `tcc-latex/conteudo/5_metodologia.tex` §Validação.

---

## Entrega integrada (E2E-Q2)

**Pré-condição:** Fases 0–6 verdes (Fase 7 paralela).

### Roteiro manual

1. Ambiente WSL ativo (`GUIA-EXECUCAO-WSL.md` §9).
2. Gerar config com **1 questão dissertativa** (`Questions/.../dissertative_example.py`).
3. `./MakeTests.py -v` → imprimir ou simular prova.
4. Preencher **à mão** resposta curta em português (letra de forma).
5. Escanear → PDF; `./MakeTests.py -v -p prova.pdf`.
6. Verificar:
   - `Correction/_scores.csv` tem `score_sugerido` (ou equivalente).
   - Sidecar `q1_assist.json` com texto OCR, parecer, confiança.
7. `./review_hitl.py` → aceitar ou ajustar nota.
8. CSV final com nota consolidada e `status_hitl`.

### Critérios de aceite E2E-Q2

| # | Critério |
|---|----------|
| E1 | PDF gerado sem erro LaTeX |
| E2 | OCR produz texto reconhecível (≥ 50% palavras-chave da resposta) |
| E3 | LLM (ou mock configurado) retorna JSON válido |
| E4 | Confiança calculada e persistida |
| E5 | Professor altera/consolida nota via HITL |
| E6 | Nenhuma regressão em questão objetiva no mesmo config |

### Modo mock para demonstração sem API

```bash
export LLM_PROVIDER=mock
export MOCK_GRADER=1
./MakeTests.py -v -p prova.pdf
./review_hitl.py list
```

E2E-Q2 deve passar em **mock** antes de exigir API paga.

---

## Estrutura de testes automatizados (proposta)

```
MakeTests/
├── tests/
│   ├── unit/
│   │   test_text_normalize.py
│   │   test_confidence_score.py
│   │   test_llm_grader_mock.py
│   │   test_question_dissertative.py
│   ├── integration/
│   │   test_ocr_pipeline.py
│   │   test_correction_sidecar.py
│   └── fixtures/
│       ├── ocr/
│       └── hitl/
├── experiments/
│   └── ocr_styles_eval.py
└── pytest.ini   # opcional
```

**Comando alvo (quando existir):**

```bash
source .venv/bin/activate
pip install pytest   # fase de setup de testes
pytest tests/unit -q
pytest tests/integration -q --run-ocr   # flag para testes lentos
```

Quando `tests/` existir, a função `validate_faseN()` correspondente em `validate-maketests.sh` deve **chamar o pytest da fase** (em vez de duplicar lógica em bash) — `validate-maketests.sh` é o orquestrador único que tanto roda checks de ambiente/E2E em shell quanto invoca os testes unitários/integração em pytest, fase a fase.

---

## Registro de progresso

Copie e preencha ao concluir cada fase:

| Fase | Data | Responsável | Testes OK | Evidência (link/arquivo) |
|------|------|-------------|-----------|--------------------------|
| 0 | 2026-06-17 | Bira | T0.1–T0.5 | `bash validate-maketests.sh` (raiz) — 5/5 OK. Ambiente: Python 3.10.12, Tesseract 4.1.1 (pacote `por` instalado em 2026-06-17, faltava antes), ZBar 0.23.92, pdfTeX (TeX Live 2022), ImageMagick (policy PDF habilitada). Corrigidos no caminho: `tex.preamble` sem `enumitem`/`multicol`/`graphicx`; chave `tex.template` deveria ser `tex.answer_key`; encoding de CSV (`Utils.getEncodeFile` lia só 32 bytes); `Utils.getImagesFromPDF` usava API removida do PyPDF2 (`getData`→`get_data`, `PyPDF2.generic`→`pypdf.generic`); `correction.final_calc` precisa ser lista de linhas com `final_calc = lambda ...` (não string solta); `convertPdfText2PdfImage.sh` tinha CRLF. |
| 1 | 2026-06-17 | Bira | T1.1–T1.7 | `bash validate-maketests.sh` (raiz) — 12/12 OK (T0+T1). Implementado: classe `QuestionDissertative(Question)` em `MakeTests.py` (herança direta de `Question`, não `QuestionMatrix`, conforme decisão arquitetural); `drawAnswerArea` desenha retângulo + linhas pautadas via cv2 (sem matriz de círculos); `doCorrection` mockado (`MOCK_SCORE=50`, sem OCR/LLM real — isso é Fases 2-4); template `-e dissertative` adicionado ao dict `examples`. Fixture `test-quick/` estendida com `Questions/Hard/dissertative_example.py` + segunda entrada em `config.json.questions.select`, provando que objetiva (Q_1) e dissertativa (Q_2) coexistem na mesma prova/correção sem regressão. |
| 2 | | | T2.1–T2.5 | |
| 3 | | | T3.1–T3.5 | |
| 4 | | | T4.1–T4.5 | |
| 5 | | | T5.1–T5.5 | |
| 6 | | | T6.1–T6.7, E2E-Q2 | |
| 7 | | | T7.1–T7.3 | |

---

## Referências

- `GUIA-IMPLEMENTACAO.md` — o que implementar
- `GUIA-EXECUCAO-WSL.md` — como rodar localmente
- `descricoes-parte-escrita/tcc-latex/conteudo/5_metodologia.tex` — validação Q3
- `descricoes-parte-escrita/01-apoio-pgc/checklist-q2.md` — checklist PGC
