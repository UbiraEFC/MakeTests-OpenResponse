# Guia de implementação — extensão dissertativa assistida (MakeTests)

**Branch:** `pgc/guia-implementacao` (organização e planejamento; `master` permanece intacta até iniciar código)  
**Base acadêmica:** `descricoes-parte-escrita/tcc-latex/` (PGC1 entregue)  
**Status:** plano — **nenhuma implementação nesta fase**

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
# pip install openai python-dotenv jiwer
```

| Pré-requisito | Linux (Debian/Ubuntu) | macOS | Windows |
|---------------|----------------------|-------|---------|
| ZBar | `sudo apt install libzbar-dev libzbar0` | `brew install zbar` | WSL recomendado; ZBar nativo é mais trabalhoso |
| Tesseract | `sudo apt install tesseract-ocr tesseract-ocr-por` | `brew install tesseract tesseract-lang` | Instalar Tesseract + pacote `por` via installer; usar **WSL** para MakeTests |
| LaTeX | `texlive-full` ou subset mínimo | MacTeX | MiKTeX / TeX Live + WSL para execução |

**Observação:** até remover ou contornar o bloqueio `win32`, desenvolvimento e correção devem ocorrer em **Linux ou WSL**.

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

---

### Fase 4 — Avaliação semântica via LLM (Q2)

| Item | Descrição |
|------|-----------|
| **O quê** | `llm_grader.py`: envia enunciado + rubrica + texto do aluno; recebe JSON estruturado |
| **Ferramentas (escolher 1 provedor principal)** | |
| **Pré-requisitos** | |

| Provedor | Biblioteca | Pré-requisitos |
|----------|------------|----------------|
| **OpenAI** | `openai` | Conta, API key, créditos; modelo ex.: `gpt-4o-mini` (custo) ou `gpt-4o` (qualidade) |
| **Anthropic** | `anthropic` | API key; modelo Claude |
| **Maritaca (Sabiá)** | REST/`requests` | Conta Maritaca, API key — alinhado a PT-BR ([maritaca.ai](https://maritaca.ai)) |

**Configuração segura**

| Item | Detalhe |
|------|---------|
| Arquivo `.env` | `LLM_API_KEY=...`, `LLM_MODEL=...`, `LLM_BASE_URL=...` (se aplicável) |
| `.gitignore` | Garantir `.env` ignorado |
| `config.json` ou `llm.json` | Rubricas e prompts versionados **sem** secrets |

**Prompt e saída estruturada (modo somativo)**

Entrada: enunciado, rubrica, gabarito discursivo, texto OCR.

Saída JSON esperada:

```json
{
  "suggested_score": 75,
  "rationale": "A resposta aborda X e Y, mas omite Z.",
  "rubric_coverage": {"criterio_1": true, "criterio_2": false},
  "review_recommended": true
}
```

**Pré-requisitos pedagógicos:** rubrica escrita pelo docente por questão (campo no módulo Python ou JSON).

**Governança:** não enviar dados identificáveis de alunos sem anonimização; verificar política da API (retenção/treinamento).

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
| Coerência parecer–nota | Parser da saída LLM (Fase 4) |
| Cobertura de rubrica | Campos `rubric_coverage` |
| Estabilidade inferencial | Desvio entre execuções repetidas (opcional) |

**Saída:** inteiro 0–100 ou faixas (`alta` / `média` / `baixa`) + flag `review_recommended`.

**Entregável:** função pura testável sem MakeTests completo.

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
| 6.1 | Sidecar `Correction/<aluno>/q<N>_assist.json` com score sugerido, confiança, parecer, texto OCR |
| 6.2 | CSV: manter coluna de score **consolidado**; opcional colunas `score_sugerido`, `confianca`, `status_hitl` (`pendente`/`aceito`/`ajustado`) |
| 6.3 | Script `review_hitl.py` (CLI): listar pendentes de baixa confiança; professor informa nota final |
| 6.4 | Template `-e dissertative` em `MakeTests.py` (como `-e ocr`, `-e essay`) |

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
├── requirements.txt             # + openai, python-dotenv, jiwer (e opcionais)
├── .env.example                 # template de variáveis (sem secrets)
├── maketests_ext/               # novo pacote (proposta)
│   ├── __init__.py
│   ├── ocr_extract.py
│   ├── text_normalize.py
│   ├── llm_grader.py
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
Fase 0  Ambiente
  ↓
Fase 1  QuestionDissertative (mock: score fixo)
  ↓
Fase 2  OCR (Tesseract)
  ↓
Fase 3  Normalização
  ↓
Fase 4  LLM (JSON estruturado)
  ↓
Fase 5  Score de confiança
  ↓
Fase 6  HITL + sidecar + template -e dissertative
  ↓
Fase 7  Experimento CER/WER (paralelo possível após Fase 2)
```

---

## 6. Checklist de pré-requisitos antes de codificar

- [ ] Ambiente Linux ou WSL funcional
- [ ] `MakeTests.py` gera e corrige questão objetiva de exemplo
- [ ] Tesseract com `por` instalado (`tesseract --list-langs`)
- [ ] Conta e API key do provedor LLM escolhido
- [ ] `.env` configurado a partir de `.env.example`
- [ ] Rubrica piloto redigida para 1 questão dissertativa de teste
- [ ] Definição institucional sobre dados de alunos (anonimização)

---

## 7. Referências internas

| Documento | Caminho |
|-----------|---------|
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
