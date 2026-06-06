# Guia de execução local — MakeTests no WSL

Ambiente alvo: **WSL2 + Ubuntu** (MakeTests **não** roda nativamente no Windows — `MakeTests.py` encerra em `win32`).

**Relacionados:** `GUIA-IMPLEMENTACAO.md`, `PLANO-TESTES-VALIDACAO.md` (Fase 0).

---

## 1. Pré-requisitos no Windows

1. **WSL2** instalado (Ubuntu 22.04 ou 24.04 recomendado):

   ```powershell
   wsl --install -d Ubuntu
   ```

2. Reinicie se necessário e abra **Ubuntu** no terminal.

3. Atualize pacotes:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

---

## 2. Dependências do sistema (Ubuntu no WSL)

Instale tudo de uma vez:

```bash
sudo apt install -y \
  python3 python3-venv python3-pip \
  libzbar0 libzbar-dev \
  tesseract-ocr tesseract-ocr-por \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
  texlive-lang-portuguese \
  ghostscript poppler-utils \
  git
```

| Pacote | Uso no MakeTests |
|--------|------------------|
| `libzbar0` | Leitura de QR Code e códigos de barras |
| `tesseract-ocr` + `por` | OCR (`QuestionOCR` e extensão dissertativa) |
| `texlive-*` | Compilação LaTeX → PDF das provas |
| `ghostscript` / `poppler-utils` | Conversão/manipulação de PDF quando necessário |

**Verificações:**

```bash
tesseract --version
tesseract --list-langs | grep -E '^por|^eng'
python3 --version
pdflatex --version
```

Esperado: Tesseract ≥ 4.x, idioma `por` listado, Python ≥ 3.8, `pdflatex` disponível.

---

## 3. Acesso ao projeto no WSL

O repositório no Windows fica em `/mnt/c/...`. Exemplo (ajuste o usuário/caminho):

```bash
cd /mnt/c/Users/ubirata.emiliano/projetos/estudos/PGC/pgc-via-maketest/MakeTests
```

**Dica:** clonar ou copiar o projeto **dentro** do filesystem Linux (`~/projetos/...`) acelera I/O do LaTeX e evita problemas de permissão:

```bash
mkdir -p ~/projetos/pgc && cp -r /mnt/c/Users/ubirata.emiliano/projetos/estudos/PGC/pgc-via-maketest/MakeTests ~/projetos/pgc/
cd ~/projetos/pgc/MakeTests
```

Use **um** caminho de forma consistente (Windows mount ou cópia Linux).

---

## 4. Ambiente Python

```bash
cd /caminho/para/MakeTests   # diretório com MakeTests.py

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Smoke test de imports:**

```bash
python3 -c "import cv2, pyzbar, pytesseract, qrcode; print('OK')"
```

Se falhar, reinstale o pacote indicado ou a lib do sistema correspondente.

---

## 5. Primeira execução — fluxo completo (MakeTests original)

### 5.1 Gerar banco de questões de exemplo

```bash
source .venv/bin/activate
mkdir -p Questions/Easy Questions/Medium Questions/Hard

./MakeTests.py -e choices       > Questions/Easy/choices.py
./MakeTests.py -e truefalse     > Questions/Easy/truefalse.py
./MakeTests.py -e questionanswer > Questions/Medium/questionanswer.py
./MakeTests.py -e number        > Questions/Medium/number.py
./MakeTests.py -e essay         > Questions/Hard/essay.py
./MakeTests.py -e ocr           > Questions/Hard/ocr.py
```

Torne executável se necessário: `chmod +x MakeTests.py`

### 5.2 Config e lista de alunos

```bash
./MakeTests.py -e config > config.json
```

Crie `Students.csv` mínimo (cabeçalhos conforme `config.json`):

```csv
%ID%;%NAME%;%EMAIL%
100000001;"Aluno Teste";teste@example.com
100000002;"Aluna Teste";teste2@example.com
```

Delimitador e aspas devem coincidir com `config.json` (`;` e `"` no template padrão).

### 5.3 Gerar PDFs

```bash
./MakeTests.py -v
```

**Saída esperada:** `Tests.pdf`, `AnswerKeys.pdf` (ou nomes definidos em `config.json`), pasta temporária LaTeX sem erro fatal.

**Se LaTeX falhar:**

```bash
./MakeTests.py -v -t tex_debug
# Inspecionar .tex gerado e rodar pdflatex manualmente na pasta tex_debug
```

### 5.4 Corrigir via PDF escaneado

1. Imprima ou simule: gere imagens/PDF com marcas (para teste rápido, use o fluxo webcam ou um PDF de teste já escaneado).
2. Para PDF escaneado:

   ```bash
   ./MakeTests.py -v -p caminho/para/prova_escaneada.pdf
   ```

3. Resultados em `Correction/` (`_scores.csv`, pastas por aluno).

**PDF incompatível:** use `convertPdfText2PdfImage.sh` (requer `ghostscript`):

```bash
bash convertPdfText2PdfImage.sh entrada.pdf saida.pdf
./MakeTests.py -v -p saida.pdf
```

### 5.5 Corrigir via webcam (opcional)

No WSL, webcam exige **WSLg** (Windows 11) ou configuração USB (`usbipd`). Se não disponível, prefira correção por **PDF** no desenvolvimento.

```bash
./MakeTests.py -v -w 0
```

---

## 6. Checklist Fase 0 (critério de pronto)

Execute na ordem e marque em `PLANO-TESTES-VALIDACAO.md`:

| # | Comando / verificação | OK? |
|---|------------------------|-----|
| 1 | `python3 -c "import cv2, pyzbar, pytesseract"` | |
| 2 | `tesseract --list-langs` contém `por` | |
| 3 | `./MakeTests.py -e config` gera JSON | |
| 4 | `./MakeTests.py -v` gera `Tests.pdf` | |
| 5 | `./MakeTests.py -v -p <pdf>` grava `Correction/_scores.csv` | |

**Entrega Fase 0:** ambiente documentado + evidência (print ou log) dos itens 1–4; item 5 quando houver PDF de teste.

---

## 7. Variáveis de ambiente (extensão dissertativa — fases posteriores)

Copie o template e preencha **fora** do Git:

```bash
cp .env.example .env
# Editar .env com editor no WSL: nano .env
```

Carregue no shell antes de testes com LLM:

```bash
set -a && source .env && set +a
```

---

## 8. Problemas comuns no WSL

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `Windows has not yet been tested` | Rodou no PowerShell/CMD | Use terminal **Ubuntu (WSL)** |
| `libzbar.so` não encontrado | ZBar não instalado | `sudo apt install libzbar0` |
| Tesseract vazio / idioma errado | Pacote `por` ausente | `sudo apt install tesseract-ocr-por` |
| LaTeX `command not found` | texlive incompleto | Instalar pacotes §2 ou `texlive-full` |
| Permissão negada em `.venv` | Projeto em `/mnt/c/` | `chmod` ou mover para `~/projetos` |
| PDF correção falha | PDF texto vs imagem | `convertPdfText2PdfImage.sh` |
| Webcam não abre | WSL sem WSLg/USB | Usar `-p PDF` |
| Lento compilar LaTeX | Projeto em `/mnt/c/` | Copiar repo para filesystem Linux |

---

## 9. Workflow diário recomendado

```bash
# 1. Abrir Ubuntu (WSL)
cd ~/projetos/pgc/MakeTests    # ou /mnt/c/...
source .venv/bin/activate
git checkout pgc/guia-implementacao   # ou branch de implementação

# 2. Antes de codificar: smoke Fase 0
python3 -c "import cv2, pyzbar, pytesseract; print('OK')"

# 3. Após mudanças: testes da fase (ver PLANO-TESTES-VALIDACAO.md)
# 4. Commit na branch de trabalho — master só após marco validado
```

---

## 10. Referências

- README original: `README.md`
- Plano de implementação: `GUIA-IMPLEMENTACAO.md`
- Testes por fase: `PLANO-TESTES-VALIDACAO.md`
- Demo em vídeo: link no `README.md`
