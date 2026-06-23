#!/bin/bash
################################################################################
# validate-maketests.sh
#
# Validação de regressão dos principais fluxos do MakeTests, organizada por
# fase conforme MakeTests/PLANO-TESTES-VALIDACAO.md. Cada fase tem sua própria
# função validate_faseN(); ao implementar uma fase nova, preencha o corpo da
# função correspondente com os testes TN.x reais (hoje é só um placeholder que
# avisa "ainda não implementada" e não conta como falha).
#
# Regra do projeto: ao concluir a implementação de uma fase, rode este script
# e só então preencha a linha da fase no "Registro de progresso" de
# PLANO-TESTES-VALIDACAO.md.
#
# Uso:
#   bash validate-maketests.sh
#
# Saída: PASS/FAIL/SKIP por critério; exit code 0 só se nada falhou.
################################################################################

set -u

MAKETESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_HOME="$MAKETESTS_DIR"
TEST_DIR="$MAKETESTS_DIR/test-quick"
MAKETESTS_PY="$MAKETESTS_DIR/MakeTests.py"
CONVERT_SH="$MAKETESTS_DIR/convertPdfText2PdfImage.sh"

PASS=0
FAIL=0
SKIP=0
declare -a RESULTS

check() {
    local id="$1" desc="$2" status="$3"
    if [ "$status" -eq 0 ]; then
        RESULTS+=("✅ $id  $desc")
        PASS=$((PASS+1))
    else
        RESULTS+=("❌ $id  $desc")
        FAIL=$((FAIL+1))
    fi
}

skip() {
    local id="$1" desc="$2"
    RESULTS+=("⏭️  $id  $desc (ainda não implementada)")
    SKIP=$((SKIP+1))
}

################################################################################
# Fase 0 — Ambiente de desenvolvimento (WSL, Python, Tesseract, LaTeX, ZBar)
################################################################################
validate_fase0() {
    # T0.1 — Imports Python
    python3 -c "import cv2, pyzbar, pytesseract, qrcode" > /tmp/validate_t01.log 2>&1
    check "T0.1" "Imports Python (cv2, pyzbar, pytesseract, qrcode)" $?

    # T0.2 — Tesseract com português
    tesseract --list-langs 2>/dev/null | grep -q '^por$'
    check "T0.2" "Tesseract com idioma 'por' instalado" $?

    # Preparar diretório de teste
    cd "$TEST_DIR" || { echo "❌ test-quick/ não encontrado"; exit 1; }
    rm -rf Correcao/notas.csv latex_debug Prova_Capital_SP.pdf Gabarito_Capital_SP.pdf Prova_Capital_SP_img.pdf

    # T0.4 — Geração de PDF (prova + gabarito)
    python "$MAKETESTS_PY" -v > /tmp/validate_gen.log 2>&1
    gen_status=$?
    [ -f Prova_Capital_SP.pdf ] && [ -f Gabarito_Capital_SP.pdf ]
    files_ok=$?
    if [ $gen_status -eq 0 ] && [ $files_ok -eq 0 ]; then gen_ok=0; else gen_ok=1; fi
    check "T0.4" "Geração de Prova_Capital_SP.pdf e Gabarito_Capital_SP.pdf (LaTeX)" $gen_ok

    # Converte a prova (PDF "digital") em PDF de imagens, simulando uma prova escaneada
    bash "$CONVERT_SH" Prova_Capital_SP.pdf > /tmp/validate_convert.log 2>&1
    convert_status=$?

    # T0.3 — QR/código de barras: uma área de resposta por (aluno x questão selecionada)
    # T0.5 — Correção: CSV final atualizado com nota para os 3 alunos
    num_students=$(python3 -c "import csv; print(sum(1 for _ in csv.reader(open('Students.csv'), delimiter=';'))-1)")
    num_questions=$(python3 -c "import json; print(len(json.load(open('config.json'))['questions']['select']))")
    expected_areas=$((num_students*num_questions))

    if [ $convert_status -eq 0 ]; then
        python "$MAKETESTS_PY" -vv -p Prova_Capital_SP_img.pdf > /tmp/validate_correction.log 2>&1
        correction_status=$?
        qr_found=$(grep -c "^Answer area found" /tmp/validate_correction.log)
    else
        correction_status=1
        qr_found=0
    fi

    [ "$qr_found" -eq "$expected_areas" ]
    check "T0.3" "QR/código de barras gerado e lido ($expected_areas/$expected_areas áreas identificadas)" $?

    if [ $correction_status -eq 0 ] && [ -f Correcao/notas.csv ] && [ "$(grep -c ';[0-9]\+;[0-9.]\+' Correcao/notas.csv)" -eq 3 ]; then
        correction_ok=0
    else
        correction_ok=1
    fi
    check "T0.5" "Correção via PDF: atualização de Correcao/notas.csv para os 3 alunos" $correction_ok

    rm -f Prova_Capital_SP_img.pdf
    cd "$PROJECT_HOME"
}

################################################################################
# Fase 1 — Classe QuestionDissertative + área de escrita livre
################################################################################
validate_fase1() {
    if ! grep -q "class QuestionDissertative" "$MAKETESTS_PY" 2>/dev/null; then
        skip "T1.x" "QuestionDissertative ainda não existe em MakeTests.py"
        return
    fi

    # T1.1 / T1.2 / T1.3 / T1.6 — testes unitários isolados, sem precisar da fixture
    (cd "$MAKETESTS_DIR" && python3 - <<'PYEOF'
import numpy as np
from MakeTests import QuestionDissertative, Question

methods = ['makeVariables','getQuestionTex','answerAreaAspectRate','drawAnswerArea','doCorrection','getAnswerText']
missing = [m for m in methods if getattr(QuestionDissertative, m) is getattr(Question, m)]
print("T1.1", "OK" if not missing else "FAIL faltam: {}".format(missing))

class T(QuestionDissertative):
    def makeSetup(self):
        self.statement = "Explique X."
        self.rubric = "Deve mencionar Y."

t = T()
t.makeVariables()
rate = t.answerAreaAspectRate()
print("T1.2", "OK" if rate > 1 else "FAIL rate={}".format(rate))

canvas = np.full((100,600,3), 255, np.uint8)
before = canvas.copy()
t.drawAnswerArea(canvas)
print("T1.3", "OK" if not (canvas==before).all() else "FAIL imagem nao mudou")

result = t.doCorrection(canvas)
ok_shape = isinstance(result, tuple) and len(result) == 3
score = result[0] if ok_shape else None
ok_score = ok_shape and isinstance(score, (int,float)) and 0 <= score <= 100
print("T1.6", "OK" if ok_score else "FAIL result={}".format(result))
PYEOF
    ) > /tmp/validate_fase1_unit.log 2>&1

    grep -q "^T1.1 OK" /tmp/validate_fase1_unit.log; check "T1.1" "Contrato Question totalmente implementado" $?
    grep -q "^T1.2 OK" /tmp/validate_fase1_unit.log; check "T1.2" "answerAreaAspectRate > 1" $?
    grep -q "^T1.3 OK" /tmp/validate_fase1_unit.log; check "T1.3" "drawAnswerArea altera a imagem (sem matriz de círculos)" $?
    grep -q "^T1.6 OK" /tmp/validate_fase1_unit.log; check "T1.6" "doCorrection mock retorna 3 valores; score 0-100" $?

    # T1.4 / T1.5 / T1.7 — geração + correção end-to-end com a fixture (objetiva + dissertativa juntas)
    if [ ! -f "$TEST_DIR/Questions/Hard/dissertative_example.py" ]; then
        skip "T1.4/T1.5/T1.7" "test-quick/Questions/Hard/dissertative_example.py ainda não existe"
        return
    fi

    cd "$TEST_DIR" || { echo "❌ test-quick/ não encontrado"; exit 1; }
    rm -rf Correcao/notas.csv "Correcao/João da Silva" "Correcao/Maria Santos" "Correcao/Carlos Oliveira" latex_debug Prova_Capital_SP.pdf Gabarito_Capital_SP.pdf Prova_Capital_SP_img.pdf

    python "$MAKETESTS_PY" -v > /tmp/validate_fase1_gen.log 2>&1
    gen_status=$?
    [ -f Prova_Capital_SP.pdf ] && [ -f Gabarito_Capital_SP.pdf ]
    files_ok=$?
    if [ $gen_status -eq 0 ] && [ $files_ok -eq 0 ]; then gen_ok=0; else gen_ok=1; fi
    check "T1.4" "Prova com 2 questões (objetiva + dissertativa) compila em LaTeX" $gen_ok

    if [ $gen_ok -eq 0 ]; then
        python3 -c "
import PyPDF2, sys
text = ''.join(p.extract_text() or '' for p in PyPDF2.PdfReader('Prova_Capital_SP.pdf').pages)
sys.exit(0 if 'fotossintese' in text else 1)
" 2>/tmp/validate_fase1_pdftext.log
        check "T1.5" "PDF inclui o enunciado da questão dissertativa" $?
    else
        check "T1.5" "PDF inclui o enunciado da questão dissertativa" 1
    fi

    bash "$CONVERT_SH" Prova_Capital_SP.pdf > /tmp/validate_fase1_convert.log 2>&1
    convert_status=$?
    if [ $convert_status -eq 0 ]; then
        python "$MAKETESTS_PY" -vv -p Prova_Capital_SP_img.pdf > /tmp/validate_fase1_correction.log 2>&1
        correction_status=$?
    else
        correction_status=1
    fi
    if [ $correction_status -eq 0 ] && [ -f Correcao/notas.csv ] && [ "$(grep -c ';[0-9]\+;[0-9]\+;[0-9.]\+' Correcao/notas.csv)" -eq 3 ]; then
        regress_ok=0
    else
        regress_ok=1
    fi
    check "T1.7" "Regressão: Q_1 (objetiva) e Q_2 (dissertativa) coexistem em Correcao/notas.csv" $regress_ok

    rm -f Prova_Capital_SP_img.pdf
    cd "$PROJECT_HOME"
}

################################################################################
# Fase 2 — Extração OCR/HTR (maketests_ext/ocr_extract.py)
################################################################################
validate_fase2() {
    if [ ! -f "$MAKETESTS_DIR/maketests_ext/ocr_extract.py" ]; then
        skip "T2.x" "maketests_ext/ocr_extract.py ainda não existe"
        return
    fi

    (cd "$MAKETESTS_DIR" && python3 - <<'PYEOF'
import cv2, numpy as np
from maketests_ext.ocr_extract import extract_text
from MakeTests import QuestionDissertative, ImageUtils

# T2.1 — imagem vazia, sem crash
blank = np.full((50, 200, 3), 255, np.uint8)
r = extract_text(blank)
print("T2.1", "OK" if r["text"] == "" else "FAIL text={!r}".format(r["text"]))

def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]

def cer(expected, obtained):
    return (levenshtein(expected, obtained) / len(expected)) if expected else 0.0

# T2.2 — texto impresso sintetico, CER < 15%
img = cv2.imread("tests/fixtures/ocr/printed_pt_01.png")
expected = open("tests/fixtures/ocr/printed_pt_01.txt").read().strip()
c = cer(expected, extract_text(img)["text"])
print("T2.2", "OK" if c < 0.15 else "FAIL cer={:.3f}".format(c))

# T2.3 — "manuscrito" letra de forma sintetico, exploratorio (sem crash)
img = cv2.imread("tests/fixtures/ocr/forma_pt_01.png")
expected = open("tests/fixtures/ocr/forma_pt_01.txt").read().strip()
c = cer(expected, extract_text(img)["text"])
print("T2.3", "OK cer={:.3f}".format(c))

# T2.4 — integracao com QuestionDissertative.doCorrection
class T(QuestionDissertative):
    def makeSetup(self):
        self.statement = "Explique X."
        self.rubric = "Y"

captured = []
original = ImageUtils.drawTextInsideTheBox
def spy(img, text, *a, **kw):
    captured.append(text)
    return original(img, text, *a, **kw)
ImageUtils.drawTextInsideTheBox = spy
try:
    t = T(); t.makeVariables()
    img = cv2.imread("tests/fixtures/ocr/printed_pt_01.png")
    score, img_proc, feedback = t.doCorrection(img)
finally:
    ImageUtils.drawTextInsideTheBox = original

ok = isinstance(score, (int, float)) and any("OCR" in c and "fotoss" in c.lower() for c in captured)
print("T2.4", "OK" if ok else "FAIL captured={}".format(captured))
PYEOF
    ) > /tmp/validate_fase2_unit.log 2>&1

    grep -q "^T2.1 OK" /tmp/validate_fase2_unit.log; check "T2.1" "Imagem vazia: extract_text sem crash, texto vazio" $?
    grep -q "^T2.2 OK" /tmp/validate_fase2_unit.log; check "T2.2" "Texto impresso sintético: CER < 15%" $?
    grep -q "^T2.3 OK" /tmp/validate_fase2_unit.log; check "T2.3" "'Manuscrito' letra de forma sintético (exploratório)" $?
    grep -q "^T2.4 OK" /tmp/validate_fase2_unit.log; check "T2.4" "doCorrection inclui texto OCR no feedback" $?

    # T2.5 — regressão: erro claro se o binário tesseract não estiver no PATH
    if command -v tesseract > /dev/null 2>&1; then
        clean_path=""
        IFS=':' read -ra path_dirs <<< "$PATH"
        for d in "${path_dirs[@]}"; do
            if [ ! -x "$d/tesseract" ]; then
                clean_path="${clean_path:+$clean_path:}$d"
            fi
        done
        (cd "$MAKETESTS_DIR" && PATH="$clean_path" python3 -c "
import numpy as np
from maketests_ext.ocr_extract import extract_text
try:
    extract_text(np.full((50,200,3), 255, dtype='uint8'))
    print('T2.5 FAIL: nao levantou excecao sem tesseract no PATH')
except Exception as e:
    print('T2.5 OK', type(e).__name__)
" > /tmp/validate_fase2_t25.log 2>&1)
        grep -q "^T2.5 OK" /tmp/validate_fase2_t25.log
        check "T2.5" "Erro claro quando tesseract não está no PATH" $?
    else
        skip "T2.5" "tesseract não encontrado no PATH atual; não foi possível testar a regressão"
    fi
}

################################################################################
# Fase 3 — Normalização textual (maketests_ext/text_normalize.py)
################################################################################
validate_fase3() {
    if [ ! -f "$MAKETESTS_DIR/maketests_ext/text_normalize.py" ]; then
        skip "T3.x" "maketests_ext/text_normalize.py ainda não existe"
        return
    fi

    (cd "$MAKETESTS_DIR" && python3 - <<'PYEOF'
import cv2
from maketests_ext.text_normalize import normalize
from maketests_ext.ocr_extract import extract_text
from MakeTests import QuestionDissertative, ImageUtils

# T3.1 — espacos duplos
print("T3.1", "OK" if normalize("foo  bar") == "foo bar" else "FAIL")

# T3.2 — hifenizacao de fim de linha
print("T3.2", "OK" if normalize("exem-\nplo") == "exemplo" else "FAIL")

# T3.3 — normalizacao NFKC (ligature fi -> f+i)
print("T3.3", "OK" if normalize("A ﬁgura") == "A figura" else "FAIL")

# T3.4 — doCorrection preserva raw e normalizado, ambos visiveis
class T(QuestionDissertative):
    def makeSetup(self):
        self.statement = "Explique X."
        self.rubric = "Y"

captured = []
original = ImageUtils.drawTextInsideTheBox
def spy(img, text, *a, **kw):
    captured.append(text)
    return original(img, text, *a, **kw)
ImageUtils.drawTextInsideTheBox = spy
try:
    t = T(); t.makeVariables()
    img = cv2.imread("tests/fixtures/ocr/printed_pt_01.png")
    t.doCorrection(img)
finally:
    ImageUtils.drawTextInsideTheBox = original

has_raw = any(c.startswith("OCR (raw):") for c in captured)
has_norm = any(c.startswith("Normalizado:") for c in captured)
print("T3.4", "OK" if has_raw and has_norm else "FAIL captured={}".format(captured))

# T3.5 — pipeline OCR -> normalize, sem excecao, resultado estavel
img = cv2.imread("tests/fixtures/ocr/printed_pt_01.png")
r1 = normalize(extract_text(img)["text"])
r2 = normalize(extract_text(img)["text"])
print("T3.5", "OK" if r1 and r1 == r2 else "FAIL r1={!r} r2={!r}".format(r1, r2))
PYEOF
    ) > /tmp/validate_fase3_unit.log 2>&1

    grep -q "^T3.1 OK" /tmp/validate_fase3_unit.log; check "T3.1" "Espaços duplos -> espaço único" $?
    grep -q "^T3.2 OK" /tmp/validate_fase3_unit.log; check "T3.2" "Hifenização de fim de linha removida" $?
    grep -q "^T3.3 OK" /tmp/validate_fase3_unit.log; check "T3.3" "Normalização Unicode NFKC" $?
    grep -q "^T3.4 OK" /tmp/validate_fase3_unit.log; check "T3.4" "doCorrection mantém raw e normalizado visíveis" $?
    grep -q "^T3.5 OK" /tmp/validate_fase3_unit.log; check "T3.5" "Pipeline OCR->normalize estável, sem exceção" $?
}

################################################################################
# Fase 4 — Avaliação semântica via LLM (maketests_ext/llm_grader.py)
################################################################################
validate_fase4() {
    if [ ! -f "$MAKETESTS_DIR/maketests_ext/llm_grader.py" ]; then
        skip "T4.x" "maketests_ext/llm_grader.py ainda não existe"
        return
    fi

    # Suite automatizada roda sem rede/credencial: LLM_PROVIDER=mock.
    (cd "$MAKETESTS_DIR" && LLM_PROVIDER=mock python3 - <<'PYEOF'
from maketests_ext.llm.schemas import GradingPayload
from maketests_ext.llm_grader import grade
from maketests_ext.llm.gemini_provider import GeminiProvider

rubric = "Deve citar: conversao de luz solar em energia quimica, papel da clorofila, liberacao de oxigenio."
aligned = GradingPayload(statement="Explique fotossintese.", rubric=rubric,
                          normalized_text="A fotossintese converte luz solar em energia quimica usando a clorofila e libera oxigenio.")
blank = GradingPayload(statement="Explique fotossintese.", rubric=rubric, normalized_text="")

# T4.1 - mock deterministico (mesma entrada -> mesma saida)
r1 = grade(aligned)
r2 = grade(aligned)
print("T4.1", "OK" if r1 == r2 else "FAIL r1={} r2={}".format(r1, r2))

# T4.2 - schema da saida
fields = ("suggested_score", "rationale", "rubric_coverage", "review_recommended", "provider_metadata")
ok = all(hasattr(r1, f) for f in fields)
print("T4.2", "OK" if ok else "FAIL")

# T4.3 - score bounds
print("T4.3", "OK" if 0 <= r1.suggested_score <= 100 else "FAIL score={}".format(r1.suggested_score))

# T4.4 - resposta vazia -> score baixo + review_recommended
r_blank = grade(blank)
ok = r_blank.suggested_score == 0 and r_blank.review_recommended is True
print("T4.4", "OK" if ok else "FAIL {}".format(r_blank))

# T4.5 - payload alinhado ao gabarito -> score bem maior que o vazio
ok = r1.suggested_score >= 50 and r1.suggested_score > r_blank.suggested_score
print("T4.5", "OK" if ok else "FAIL score={}".format(r1.suggested_score))

# T4.7 - sem API key (provider gemini direto, nao a fachada) -> erro claro, sem excecao.
# Remove LLM_API_KEY do ambiente explicitamente: get_provider() ja deu load_dotenv()
# antes (efeito colateral do .env real), api_key=None sozinho nao bastaria.
import os
os.environ.pop("LLM_API_KEY", None)
gp = GeminiProvider(api_key=None)
r_noauth = gp.grade_answer(aligned)
ok = r_noauth.error == "missing_api_key" and r_noauth.review_recommended is True
print("T4.7", "OK" if ok else "FAIL {}".format(r_noauth))
PYEOF
    ) > /tmp/validate_fase4_unit.log 2>&1

    grep -q "^T4.1 OK" /tmp/validate_fase4_unit.log; check "T4.1" "Mock determinístico (mesma entrada -> mesma saída)" $?
    grep -q "^T4.2 OK" /tmp/validate_fase4_unit.log; check "T4.2" "Schema da saída (GradingResult completo)" $?
    grep -q "^T4.3 OK" /tmp/validate_fase4_unit.log; check "T4.3" "suggested_score dentro de [0,100]" $?
    grep -q "^T4.4 OK" /tmp/validate_fase4_unit.log; check "T4.4" "Resposta vazia -> score baixo + review_recommended" $?
    grep -q "^T4.5 OK" /tmp/validate_fase4_unit.log; check "T4.5" "Resposta alinhada à rubrica -> score alto" $?
    grep -q "^T4.7 OK" /tmp/validate_fase4_unit.log; check "T4.7" "Sem API key (Gemini): erro claro, sem excecao" $?
}

################################################################################
# T4.6 (manual/opt-in) — 1 chamada real à API do provedor configurado em .env.
# NÃO é chamada por padrão em validate-maketests.sh (custo/rede/quota) — só
# roda se invocada explicitamente: bash -c 'source validate-maketests.sh; validate_fase4_live'
################################################################################
validate_fase4_live() {
    (cd "$MAKETESTS_DIR" && python3 - <<'PYEOF'
from maketests_ext.llm.schemas import GradingPayload
from maketests_ext.llm_grader import grade

p = GradingPayload(
    statement="Explique o que e fotossintese e sua importancia para os seres vivos.",
    rubric="Deve citar: conversao de luz solar em energia quimica, papel da clorofila/cloroplastos, liberacao de oxigenio.",
    normalized_text="A fotossintese converte luz solar em energia quimica usando a clorofila presente nos cloroplastos, liberando oxigenio como subproduto.",
)
r = grade(p)
print(r)
ok = r.error is None and 0 <= r.suggested_score <= 100 and r.rationale
print("T4.6", "OK" if ok else "FAIL")
PYEOF
    )
}

################################################################################
# Fase 5 — Score de confiança (maketests_ext/confidence_score.py)
################################################################################
validate_fase5() {
    if [ ! -f "$MAKETESTS_DIR/maketests_ext/confidence_score.py" ]; then
        skip "T5.x" "maketests_ext/confidence_score.py ainda não existe"
        return
    fi

    # Suite automatizada roda sem rede/credencial: LLM_PROVIDER=mock.
    (cd "$MAKETESTS_DIR" && LLM_PROVIDER=mock python3 - <<'PYEOF'
import cv2
from maketests_ext.confidence_score import ConfidenceSignals, compute
from MakeTests import QuestionDissertative, ImageUtils

# T5.1 - OCR ruim (cenario realista: OCR ruim correlaciona com LLM inseguro) -> confianca baixa
r1 = compute(ConfidenceSignals(ocr_confidence_mean=0.1, ocr_char_doubt_ratio=0.8,
                                llm_review_recommended=True, rubric_coverage={"a": True, "b": False}))
print("T5.1", "OK" if r1.level == "baixa" and r1.review_recommended else "FAIL {}".format(r1))

# T5.2 - OCR bom + LLM confiante + boa cobertura -> confianca alta, sem necessidade de revisao
r2 = compute(ConfidenceSignals(ocr_confidence_mean=0.95, ocr_char_doubt_ratio=0.0,
                                llm_review_recommended=False, rubric_coverage={"a": True, "b": True}))
print("T5.2", "OK" if r2.level == "alta" and not r2.review_recommended else "FAIL {}".format(r2))

# T5.3 - divergencia: OCR otimo mas LLM pede revisao -> nunca mais otimista que o LLM
r3 = compute(ConfidenceSignals(ocr_confidence_mean=0.99, ocr_char_doubt_ratio=0.0,
                                llm_review_recommended=True, rubric_coverage={"a": True}))
print("T5.3", "OK" if r3.review_recommended is True else "FAIL {}".format(r3))

# T5.5 - integracao com QuestionDissertative.doCorrection (LLM_PROVIDER=mock)
class T(QuestionDissertative):
    def makeSetup(self):
        self.statement = "Explique X."
        self.rubric = "Y"

captured = []
original = ImageUtils.drawTextInsideTheBox
def spy(img, text, *a, **kw):
    captured.append(text)
    return original(img, text, *a, **kw)
ImageUtils.drawTextInsideTheBox = spy
try:
    t = T(); t.makeVariables()
    img = cv2.imread("tests/fixtures/ocr/printed_pt_01.png")
    score, img_proc, feedback = t.doCorrection(img)
finally:
    ImageUtils.drawTextInsideTheBox = original

ok = any(c.startswith("Confianca:") for c in captured)
print("T5.5", "OK" if ok else "FAIL captured={}".format(captured))
PYEOF
    ) > /tmp/validate_fase5_unit.log 2>&1

    grep -q "^T5.1 OK" /tmp/validate_fase5_unit.log; check "T5.1" "OCR ruim + LLM inseguro -> confiança baixa" $?
    grep -q "^T5.2 OK" /tmp/validate_fase5_unit.log; check "T5.2" "OCR bom + LLM confiante -> confiança alta" $?
    grep -q "^T5.3 OK" /tmp/validate_fase5_unit.log; check "T5.3" "Divergência: LLM pede revisão -> review_recommended sempre true" $?
    skip "T5.4" "Estabilidade entre execuções não implementada (hook reservado em score_stability_std, ver confidence_score.py)"
    grep -q "^T5.5 OK" /tmp/validate_fase5_unit.log; check "T5.5" "doCorrection inclui linha de confiança no feedback" $?
}

################################################################################
# Fase 6 — HITL e persistência (review_hitl.py) — marco E2E-Q2
################################################################################
validate_fase6() {
    if [ ! -f "$MAKETESTS_DIR/review_hitl.py" ]; then
        skip "T6.x / E2E-Q2" "review_hitl.py ainda não existe"
        return
    fi
    skip "T6.x / E2E-Q2" "review_hitl.py existe, mas validate_fase6() ainda não foi escrita"
}

################################################################################
# Teste de integração robusto: pipeline completo com respostas sintéticas
# reais (não em branco) tanto na múltipla escolha quanto na dissertativa.
# T0.6/T1.8 — ver tests/test_synthetic_answers.py para o passo a passo.
################################################################################
validate_synthetic_answers() {
    (cd "$MAKETESTS_DIR" && python3 tests/test_synthetic_answers.py) > /tmp/validate_synthetic_answers.log 2>&1

    grep -q "^T0.6 OK" /tmp/validate_synthetic_answers.log
    check "T0.6" "Múltipla escolha end-to-end com resposta real (não em branco)" $?
    grep -q "^T1.8 OK" /tmp/validate_synthetic_answers.log
    check "T1.8" "Dissertativa end-to-end com resposta real (OCR real, não mockado)" $?
}

################################################################################
# main
################################################################################
echo "================================================"
echo "Validação dos principais fluxos do MakeTests"
echo "================================================"
echo ""

source "$MAKETESTS_DIR/.venv/bin/activate" 2>/dev/null || source "$MAKETESTS_DIR/../.venv/bin/activate" 2>/dev/null

validate_fase0
validate_fase1
validate_synthetic_answers
validate_fase2
validate_fase3
validate_fase4
validate_fase5
validate_fase6

echo ""
echo "------------------------------------------------"
for r in "${RESULTS[@]}"; do echo "$r"; done
echo "------------------------------------------------"
echo "$PASS passaram, $FAIL falharam, $SKIP ainda não implementadas."
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "Logs em /tmp/validate_*.log para diagnóstico."
    exit 1
fi

echo "✅ Nenhuma falha nos fluxos já implementados."
exit 0
