# Guia de implementação — extensão dissertativa assistida (MakeTests)

**Branch:** `pgc/guia-implementacao` (organização e planejamento; `master` permanece intacta até iniciar código)  
**Base acadêmica:** `descricoes-parte-escrita/tcc-latex/` (PGC1 entregue)  
**Status:** plano — **nenhuma implementação nesta fase**

**Documentos complementares:**

| Arquivo | Conteúdo |
|---------|----------|
| `GUIA-EXECUCAO-WSL.md` | Setup e execução local no WSL (Fase 0) |
| `PLANO-TESTES-VALIDACAO.md` | Testes, critérios de aceite e marco E2E-Q2 por fase |

---

## 1. Objetivo da extensão

Integrar ao MakeTests um tipo de questão em que o aluno **escreve à mão** na área de resposta e o sistema:

1. Extrai texto da imagem (OCR/HTR)
2. Normaliza o texto transcrito
3. Avalia semanticamente via LLM (rubrica / gabarito discursivo)
4. Emite **recomendação de nota**, **parecer** e **score de confiança**
5. Mantém **human-in-the-loop (HITL)**: o professor consolida a nota final

**Fora do escopo inicial (extensão exploratória):** HMER (matemática manuscrita), modo formativo direto ao aluno, automação integral da nota.

---

## 2. Estado atual do MakeTests (`master`)

### 2.1 O que já existe e será reutilizado

| Componente | Local | Papel na extensão |
|------------|-------|-------------------|
| Hierarquia `Question` | `MakeTests.py` ~L797 | Contrato base (`makeVariables`, `getQuestionTex`, `drawAnswerArea`, `doCorrection`, `getAnswerText`) |
| `QuestionOCR` | ~L1362 | Referência de pré-processamento + Tesseract; **não** estender para dissertativa longa |
| `QuestionEssay` | ~L1006 | Rubrica por faixas (círculos); **permanece** — não confundir com dissertativa escrita |
| `QuestionsDB` | ~L1383 | Carregamento dinâmico de módulos em `Questions/` |
| `CorrectionManager.doCorrection` | ~L1911 | Fluxo: QR → área de resposta → `question.doCorrection` → CSV |
| OpenCV, pyzbar, pytesseract | `requirements.txt` | Visão, códigos, OCR base |
| LaTeX / PDF | fluxo existente | Geração de prova com área de escrita livre |

### 2.2 Lacunas a endereçar na implementação

- Não há classe para texto livre manuscrito com avaliação semântica
- `QuestionOCR.getScore(text)` compara string **literal**
- `QuestionOCR.doCorrection` retorna **2 valores**; `CorrectionManager` espera **3** `(score, img_processada, img_feedback)` — a nova classe deve normalizar o contrato
- `MakeTests.py` encerra em Windows (`sys.exit("Windows has not yet been tested.")`) — ambiente de dev precisa ser Linux/macOS ou WSL
- Não há persistência de parecer textual / confiança além do score numérico no CSV

### 2.3 Decisão arquitetural recomendada

Adotar **Opção B + C** (ver `descricoes-parte-escrita/02-engenharia/analise-maketests-dissertativas.md` §2.2):

- **Nova classe** `QuestionDissertative` herdando de `Question` (não de `QuestionMatrix`)
- **Pipeline interno:** OCR → normalização → LLM → score + confiança + parecer
- **Correção assistida (Opção D):** score sugerido; professor valida via HITL

---

## 3. Mapa de implementações planejadas

Cada bloco lista **o que implementar**, **ferramentas**, **pré-requisitos** e **fase** (Q2 = 2º quadrimestre PGC).

### Fase 0 — Ambiente de desenvolvimento

| Item | Descrição |
|------|-----------|
| **O quê** | Ambiente reproduzível para gerar provas e testar correção |
| **Ferramentas** | Python ≥3.8, `venv`, Git, LaTeX (`pdflatex`), ZBar, Tesseract |
| **Pré-requisitos** | |

**Python e dependências**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS/WSL
pip install -r requirements.txt
# Dependências adicionais previstas (Q2):
# pip install python-dotenv jiwer
# + SDK do provedor LLM ativo (Fase 4) - ex.: google-genai para o adapter Gemini inicial
```

| Pré-requisito | Linux (Debian/Ubuntu) | macOS | Windows |
|---------------|----------------------|-------|---------|
| ZBar | `sudo apt install libzbar-dev libzbar0` | `brew install zbar` | WSL recomendado; ZBar nativo é mais trabalhoso |
| Tesseract | `sudo apt install tesseract-ocr tesseract-ocr-por` | `brew install tesseract tesseract-lang` | Instalar Tesseract + pacote `por` via installer; usar **WSL** para MakeTests |
| LaTeX | `texlive-full` ou subset mínimo | MacTeX | MiKTeX / TeX Live + WSL para execução |

**Observação:** até remover ou contornar o bloqueio `win32`, desenvolvimento e correção devem ocorrer em **Linux ou WSL**. Passo a passo: **`GUIA-EXECUCAO-WSL.md`**. Critérios de pronto: **`PLANO-TESTES-VALIDACAO.md`** (Fase 0, T0.1–T0.4).

---

### Fase 1 — Classe `QuestionDissertative` (núcleo Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | Nova especialização de `Question` com área de escrita livre (linhas ou retângulo), sem matriz de círculos |
| **Onde** | `MakeTests.py` (classe base) + módulo exemplo `Questions/.../dissertative.py` |
| **Ferramentas** | Python, OpenCV (`cv2`), LaTeX (tabulary/tabela de linhas, como no template `essay`) |
| **Pré-requisitos** | Fase 0; leitura de `Question`, `QuestionOCR`, template `-e essay` |

**Métodos a implementar**

| Método | Comportamento planejado |
|--------|-------------------------|
| `makeVariables()` | Enunciado, rubrica/gabarito discursivo, parâmetros de LLM (modelo, temperatura) |
| `getQuestionTex()` | Enunciado + área com linhas em branco (≥8–12 linhas) |
| `answerAreaAspectRate()` | Proporção alta (ex.: 10:1), similar a `QuestionEssay` |
| `drawAnswerArea()` | Retângulo ou linhas guia (OpenCV) |
| `doCorrection(img)` | Orquestra Fases 2–5; retorna `(score_sugerido, img_debug, img_feedback)` |
| `getAnswerText()` | Gabarito discursivo / rubrica resumida para `Template.pdf` |

**Entregável:** questão exemplo corrigível end-to-end com OCR+LLM mock (antes da API real).

**Validação:** testes T1.1–T1.7 em `PLANO-TESTES-VALIDACAO.md`.

---

### Fase 2 — Extração OCR/HTR (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | Módulo `ocr_extract.py` (ou pacote `maketests_ext/`) que recebe recorte BGR e devolve texto + metadados de confiança |
| **Ferramentas (camada 1 — obrigatória)** | **Tesseract** + **pytesseract** (já no projeto) |
| **Ferramentas (camada 2 — avaliar no Q2)** | **TrOCR** (Hugging Face `transformers`) para manuscrito; ou API **Google Cloud Vision** / **Azure Read** |
| **Pré-requisitos** | |

**Tesseract (baseline)**

| Pré-requisito | Detalhe |
|---------------|---------|
| Binário `tesseract` no PATH | `tesseract --version` |
| Idioma português | Pacote `por` ou `por+eng` |
| Config OCR | `--psm 6` ou `7` para bloco/linha; testar `--oem 3` |
| Pré-processamento | Reutilizar pipeline de `QuestionOCR.doCorrection` (blur, adaptive threshold, morphology) |

**TrOCR (opcional Q2)**

| Pré-requisito | Detalhe |
|---------------|---------|
| `torch`, `transformers`, `Pillow` | GPU recomendada; CPU possível para amostras pequenas |
| Modelo | Ex.: `microsoft/trocr-base-handwritten` (inglês) — validar qualidade em PT |
| Custo | Open source; custo de hardware/tempo |

**API cloud (opcional, se Tesseract/TrOCR insuficientes)**

| Serviço | Pré-requisitos |
|---------|----------------|
| Google Cloud Vision | Conta GCP, API habilitada, credenciais JSON, billing |
| Azure AI Vision | Resource no Azure, endpoint + key |

**Saída esperada do módulo OCR**

```python
{
  "text": "...",
  "engine": "tesseract",
  "confidence_mean": 0.72,      # quando disponível
  "char_doubt_ratio": 0.05,   # heurística
  "writing_style_hint": "mixed" # exploratório: cursiva|forma|misto
}
```

---

### Fase 3 — Normalização textual (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | `text_normalize.py`: limpeza pós-OCR antes do LLM |
| **Ferramentas** | Python stdlib (`re`, `unicodedata`), opcional `ftfy` |
| **Pré-requisitos** | Saída da Fase 2 |

**Operações planejadas**

- Remover quebras espúrias e espaços duplicados
- Normalizar unicode (NFKC)
- Corrigir hifenização de fim de linha
- Preservar texto original em arquivo sidecar para auditoria

**Não incluir na v1:** correção gramatical agressiva (risco de alterar sentido do aluno).

**Integração com a Fase 4:** a saída desta fase alimenta diretamente o campo `normalized_text` do `GradingPayload` (ver Fase 4) — nenhuma outra limpeza de texto ocorre depois disso.

---

### Fase 4 — Avaliação semântica via LLM, provider-agnostic (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | Avaliação semântica via LLM, acessada **sempre** através de uma camada de abstração de provedor — nenhuma fase posterior (Fase 5, Fase 6, `QuestionDissertative`) importa um SDK de LLM diretamente |
| **Ferramentas** | Pacote novo `maketests_ext/llm/` (ver §Organização dos módulos); SDK do provedor ativo isolado dentro do respectivo `*_provider.py` |
| **Provedor inicial** | **Gemini** (Google AI Studio / Gemini API) — ver §Implementação inicial: Gemini |
| **Pré-requisitos** | Fase 3 (texto normalizado disponível no payload) |

**Por que uma camada de abstração**

A escolha de provedor de LLM muda com o tempo (preço, qualidade em PT-BR, política de dados, crédito disponível) — isso não deve ditar a arquitetura interna do MakeTests. A abstração existe para:

- **reduzir lock-in tecnológico** — trocar de provedor não deve tocar em `QuestionDissertative`, Fase 5 ou Fase 6;
- **permitir comparação entre provedores** — rodar o mesmo conjunto de respostas por dois adapters e comparar `suggested_score`/`rationale`;
- **facilitar testes A/B de qualidade de correção** — relevante para o capítulo de validação do TCC (Fase 8);
- **suportar critérios institucionais futuros** — custo, privacidade/LGPD, retenção/treinamento de dados, aderência ao português — trocando só o adapter ativo, sem reescrever a integração;
- **preservar o contrato interno do MakeTests** mesmo que o provedor mude ou deixe de existir.

**Gemini é o provedor inicial só por pragmatismo de prototipação** — a decisão institucional sobre qual provedor usar em produção é orientada por essa abstração, não pelo contrário.

**Contrato do provedor (LLM Provider Adapter)**

Toda avaliação semântica passa por uma função única, implementada por cada adapter:

```python
def grade_answer(payload: GradingPayload) -> GradingResult:
    ...
```

Entrada (`GradingPayload`) — mínimo:

| Campo | Descrição |
|-------|-----------|
| `statement` | Enunciado da questão |
| `rubric` | Rubrica / critérios de correção |
| `expected_topics` | Gabarito discursivo ou tópicos esperados |
| `normalized_text` | Texto OCR normalizado (saída da Fase 3) |
| `context_metadata` | Opcional: id da questão, disciplina, nível, etc. |
| `run_params` | Opcional: `model`, `temperature`, `timeout` — overrides por chamada |

Saída (`GradingResult`) — mínimo:

| Campo | Descrição |
|-------|-----------|
| `suggested_score` | Nota sugerida (0–100) |
| `rationale` | Parecer textual |
| `rubric_coverage` | Dict `{critério: bool}` |
| `review_recommended` | Bool — sinaliza revisão HITL prioritária |
| `provider_metadata` | Provedor, modelo, tokens, latência, request id — para auditoria (Fase 6) |
| `error` | Preenchido (demais campos `None`/conservadores) se a chamada falhar — o adapter nunca deixa a exceção do SDK escapar para fora dele |

Esse contrato é o que `llm_grader.py` (fachada, ver §Organização dos módulos) expõe para o resto do sistema. Nenhuma outra parte do código deve conhecer o formato de request/response específico de um provedor.

**Saída estruturada: nativa quando possível, fallback sempre validado**

- Quando o provedor suportar **structured output nativo** (JSON Schema / function calling — Gemini, OpenAI e Anthropic atualmente suportam), o adapter deve usá-lo para reduzir erro de parsing.
- Quando não suportar, o adapter usa um prompt que pede JSON e faz parsing manual (fallback).
- **Em ambos os casos**, o objeto retornado passa por `response_validator.py` antes de virar um `GradingResult` — a validação final do schema nunca depende de o provedor "ter prometido" JSON válido. Isso isola o resto do sistema de um provedor que alucine um campo faltante ou um tipo errado.

**Organização dos módulos**

`llm_grader.py` passa a ser a **fachada/orquestrador**: é o único ponto que `QuestionDissertative.doCorrection` chama. Internamente, ele delega para o adapter ativo via `provider_factory.py`. A lógica específica de cada provedor migra para um subpacote dedicado:

```
maketests_ext/
├── llm_grader.py            # fachada: grade(payload) -> GradingResult, escolhe o adapter via provider_factory
└── llm/
    ├── __init__.py
    ├── base.py               # classe abstrata/Protocol LLMProvider.grade_answer(payload)
    ├── schemas.py            # GradingPayload, GradingResult (dataclasses ou pydantic)
    ├── provider_factory.py   # lê LLM_PROVIDER e instancia o adapter correspondente
    ├── prompt_builder.py     # monta o prompt a partir do payload (versionado em prompts/)
    ├── response_validator.py # valida/normaliza a resposta do provedor contra schemas.py
    ├── gemini_provider.py    # implementação concreta inicial
    ├── openai_provider.py    # stub documental — implementar quando for adicionar o provedor
    ├── anthropic_provider.py # stub documental
    └── maritaca_provider.py  # stub documental (ver nota de crédito em §Provedores: hoje e depois)
```

**Por que essa organização e não um módulo único:** um `llm_grader.py` sozinho cresceria para conter prompt, parsing e chamada de SDK de N provedores no mesmo arquivo — exatamente o acoplamento que esta fase quer evitar. Separar por arquivo deixa cada adapter substituível e testável isoladamente (a Fase 5/6 pode mockar `LLMProvider` nos testes, sem precisar de API key real).

**Configuração**

A configuração é desacoplada do provedor — trocar de provedor é trocar variáveis de ambiente, não código:

```bash
LLM_PROVIDER=gemini          # seleciona o adapter via provider_factory.py
LLM_MODEL=gemini-flash-latest
LLM_API_KEY=...
LLM_BASE_URL=...             # quando aplicável (ex.: endpoint custom/proxy)
LLM_TIMEOUT=30
LLM_TEMPERATURE=0.2
```

| Item | Detalhe |
|------|---------|
| Secrets (`LLM_API_KEY`) | Sempre em `.env`, nunca versionados — `.gitignore` já cobre `.env` |
| Prompts e rubricas | Versionados em `maketests_ext/prompts/` (ex.: `somativo_v1.txt`), **sem** secrets |
| `.env.example` | Atualizado com as 6 variáveis acima, com valores de exemplo |

**Implementação inicial: Gemini**

- **Google AI Studio** é usado só para **prototipar** prompt e schema manualmente antes de codificar o adapter.
- A implementação produtiva (`gemini_provider.py`) chama a **Gemini API** diretamente (não a UI do AI Studio).
- Validado nesta sessão: a API key fornecida autenticou e respondeu (`gemini-flash-latest` → resolvido para `gemini-3.5-flash`), HTTP 200 — viável para prototipagem.
- **Escolher o Gemini agora não compromete a troca futura** — é exatamente o que o contrato desta fase existe para garantir.

**Persistência e auditoria (ponte com a Fase 6)**

O sidecar da Fase 6 (`Correction/<aluno>/q<N>_assist.json`) deve registrar, além do `GradingResult`:

| Campo adicional | Por quê |
|------------------|---------|
| `provider` | Qual adapter gerou a sugestão (`gemini`, `openai`, ...) |
| `model` | Modelo exato usado (varia mesmo dentro do mesmo provedor) |
| `prompt_version` | Versão do template em `prompts/` — necessário se o prompt mudar entre execuções |
| `raw_response` | Resposta crua do provedor, sanitizada — opcional, útil para depurar discordâncias |
| `structured_result` | O `GradingResult` já validado |
| `inference_timestamp` | Quando a chamada foi feita |
| `run_params` | Parâmetros usados (modelo, temperatura, timeout) |

Isso permite comparar provedores e versões de prompt retroativamente sem precisar re-rodar a correção.

**Provedores: hoje e depois**

| Provedor | Status nesta fase | Observação |
|----------|--------------------|------------|
| **Gemini** | Implementação inicial (`gemini_provider.py`) | Escolhido por pragmatismo de prototipação — free tier do Google AI Studio acessível, structured output nativo |
| **OpenAI** | Stub documental | Bom suporte a structured output/function calling; custo por token a avaliar |
| **Anthropic** | Stub documental | Bom suporte a structured output; avaliar custo/disponibilidade de crédito |
| **Maritaca (Sabiá)** | Stub documental | Alinhado a PT-BR; **testado nesta sessão — a chave autentica, mas a conta está sem crédito ativo** (`insufficient_funds` em todos os modelos, incl. `sabiazinho`); reavaliar se/quando houver crédito |

O núcleo do MakeTests (Fase 5, Fase 6, `QuestionDissertative`) não depende de qual linha desta tabela está ativa.

**Pré-requisitos pedagógicos:** rubrica escrita pelo docente por questão (campo no módulo Python ou JSON).

**Governança:** não enviar dados identificáveis de alunos sem anonimização; verificar política de retenção/treinamento de cada provedor antes de decidir o uso em produção (critério institucional, não técnico).

---

### Fase 5 — Score de confiança heurístico (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | `confidence_score.py` agrega sinais (TCC §6.2) |
| **Ferramentas** | Python; opcional 2–3 chamadas LLM com temperatura > 0 para estabilidade |
| **Pré-requisitos** | Fases 2 e 4 |

| Sinal | Fonte |
|-------|-------|
| Qualidade OCR | `confidence_mean`, `char_doubt_ratio` (Fase 2) |
| Coerência parecer–nota | Parser da saída do `GradingResult` (Fase 4) |
| Cobertura de rubrica | Campos `rubric_coverage` |
| Resposta estruturada via fallback | `provider_metadata`/estado de `response_validator.py` (Fase 4) — penaliza se precisou cair no fallback em vez de structured output nativo |
| Estabilidade inferencial | Desvio entre execuções repetidas (opcional) |

**Saída:** inteiro 0–100 ou faixas (`alta` / `média` / `baixa`) + flag `review_recommended`.

**Entregável:** função pura testável sem MakeTests completo — recebe um `GradingResult` (ou um mock dele), não depende de qual provedor o gerou.

---

### Fase 6 — Integração HITL e persistência (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | Estender fluxo de correção para salvar recomendação **sem** substituir decisão docente |
| **Ferramentas** | CSV existente (`CorrectionManager`), JSON sidecar por aluno/questão |
| **Pré-requisitos** | Fases 1–5 |

**Implementações planejadas**

| # | Descrição |
|---|-----------|
| 6.1 | **Implementado.** Sidecar `Correcao/<aluno>/<Q_N>_assist.json` com score sugerido, confiança, parecer, texto OCR, e os campos de proveniência do provedor (`provider`, `model`, `prompt_version`, `inference_timestamp` — ver Fase 4 §Persistência e auditoria); preserva `status_hitl`/`manual_score` entre re-scans. `QuestionDissertative.doCorrection` popula `self.last_assist`; `Main.doCorrection` grava o sidecar. |
| 6.2 | **Implementado, com escopo reduzido por design.** CSV central (`notas.csv`) continua genérico, sem colunas `score_sugerido`/`confianca`/`status_hitl` — esses campos vivem só no sidecar (ensinar `CorrectionManager`, usado por qualquer tipo de questão, a conceitos exclusivos de dissertativas quebraria o desacoplamento). `Q_N` já recebe a nota sugerida automaticamente; `status_hitl="pendente"` no sidecar é quem sinaliza que falta HITL. |
| 6.3 | **Implementado.** `review_hitl.py` (CLI): `list [--all]`, `accept <aluno_dir> <questão>`, `adjust <aluno_dir> <questão> <nota>` — reaproveita `MakeTests.Main`/`CorrectionManager`. |
| 6.4 | **Já existia** desde a Fase 1 (`MakeTests.py:2594`, `examples['dissertative']`) — nenhum trabalho novo nesta fase. |

**Interface mínima Q2:** CLI interativa (sem GUI web na v1).

**Ferramentas CLI:** Python stdlib `argparse` ou extensão do modo `-i` existente.

---

### Fase 7 — Experimento OCR por estilo de escrita (Q2 exploratório)

| Item | Descrição |
|------|-----------|
| **O quê** | Script offline `experiments/ocr_styles_eval.py` |
| **Ferramentas** | **jiwer** (CER/WER), Tesseract (+ opcional TrOCR), planilha/CSV de resultados |
| **Pré-requisitos** | |

| Pré-requisito | Detalhe |
|---------------|---------|
| Corpus mínimo | Imagens rotuladas: cursiva, letra de forma, misto (texto curto PT) |
| Ground truth | Transcrição manual por imagem |
| Ambiente | Mesmo da Fase 0 |

**Métricas:** CER/WER por categoria; correlacionar com sinais de confiança (Fase 5).

**Não exige** integração ao fluxo principal de correção.

---

### Fase 8 — Extensões futuras (Q3 ou além)

| Item | Ferramentas | Quando |
|------|-------------|--------|
| Roteamento HMER (matemática) | Mathpix API, pix2tex, modelos dedicados | Exploratório Q3 |
| Modo formativo (feedback ao aluno) | Mesmo LLM, prompt distinto | Extensão TCC |
| Validação vs correção humana | `scipy`, kappa quadrático, pandas | Q3 |
| Suporte Windows nativo | Remover/adaptar `sys.exit` win32; testar ZBar | Se necessário |

---

## 4. Estrutura de arquivos prevista (após implementação)

```
MakeTests/
├── MakeTests.py                 # + class QuestionDissertative; + -e dissertative
├── requirements.txt             # + SDK do provedor ativo (ex.: google-genai), python-dotenv, jiwer (e opcionais)
├── .env.example                 # template de variáveis (sem secrets) - inclui LLM_PROVIDER e afins
├── maketests_ext/               # novo pacote (proposta)
│   ├── __init__.py
│   ├── ocr_extract.py
│   ├── text_normalize.py
│   ├── llm_grader.py            # fachada: grade(payload) -> GradingResult
│   ├── llm/                     # camada de abstração de provedor (Fase 4)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── schemas.py
│   │   ├── provider_factory.py
│   │   ├── prompt_builder.py
│   │   ├── response_validator.py
│   │   ├── gemini_provider.py
│   │   ├── openai_provider.py       # stub documental
│   │   ├── anthropic_provider.py    # stub documental
│   │   └── maritaca_provider.py     # stub documental
│   ├── confidence_score.py
│   └── prompts/
│       └── somativo_v1.txt
├── review_hitl.py               # CLI revisão docente
├── experiments/
│   └── ocr_styles_eval.py
├── Questions/
│   └── .../dissertative_example.py
└── GUIA-IMPLEMENTACAO.md        # este arquivo
```

---

## 5. Ordem de execução recomendada (Q2)

```
Fase 0   Ambiente
  ↓
Fase 1   QuestionDissertative (mock: score fixo)
  ↓
Fase 2   OCR (Tesseract)
  ↓
Fase 3   Normalização
  ↓
Fase 4a  Schema interno estável (schemas.py + base.py) - contrato antes de qualquer SDK
  ↓
Fase 4b  Adapter Gemini (gemini_provider.py) - primeira implementação concreta
  ↓
Fase 4c  llm_grader.py (fachada) plugado em QuestionDissertative.doCorrection
  ↓
Fase 5   Score de confiança (usa GradingResult + provider_metadata)
  ↓
Fase 6   HITL + sidecar (persiste provider/model/prompt_version) + template -e dissertative
  ↓
Fase 7   Experimento CER/WER (paralelo possível após Fase 2)
```

A ordem 4a→4b→4c é deliberada: o schema/contrato (4a) é definido **antes** de qualquer SDK concreto, para garantir que o resto do pipeline (5, 6) é desenhado contra o contrato, não contra particularidades do Gemini.

---

## 6. Checklist de pré-requisitos antes de codificar

- [ ] Ambiente WSL funcional (`GUIA-EXECUCAO-WSL.md` §6 — T0.1–T0.4)
- [ ] `MakeTests.py` gera e corrige questão objetiva de exemplo
- [ ] Tesseract com `por` instalado (`tesseract --list-langs`)
- [ ] Schema interno de avaliação definido (`GradingPayload`/`GradingResult` em `schemas.py`)
- [ ] Provedor padrão inicial escolhido (Gemini) e API key validada
- [ ] `.env` configurado a partir de `.env.example`, compatível com a abstração de provedor (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, ...)
- [ ] Rubrica piloto redigida para 1 questão dissertativa de teste
- [ ] Definição institucional sobre dados de alunos (anonimização)
- [ ] Política institucional de dados por provedor definida (LGPD, retenção, treinamento) — antes de decidir o provedor de produção

---

## 7. Referências internas

| Documento | Caminho |
|-----------|---------|
| Execução local WSL | `GUIA-EXECUCAO-WSL.md` |
| Testes e marco E2E-Q2 | `PLANO-TESTES-VALIDACAO.md` |
| TCC PGC1 (canônico) | `../descricoes-parte-escrita/tcc-latex/` |
| Análise técnica MakeTests | `../descricoes-parte-escrita/02-engenharia/analise-maketests-dissertativas.md` |
| Checklist Q2 | `../descricoes-parte-escrita/01-apoio-pgc/checklist-q2.md` |
| Pipeline e score (TCC) | `tcc-latex/conteudo/5_metodologia.tex` |

---

## 8. Controle de versão desta branch

| Branch | Propósito |
|--------|-----------|
| `master` | Código original MakeTests (estável) |
| `pgc/guia-implementacao` | Guia, `.env.example`, esqueleto futuro — merges incrementais quando cada fase estiver pronta |

**Fluxo sugerido:** implementar fase a fase em commits pequenos nesta branch; após revisão, merge em `master` ou branch `pgc/implementacao`.
