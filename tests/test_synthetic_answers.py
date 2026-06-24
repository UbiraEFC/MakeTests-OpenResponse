#!/usr/bin/env python3
"""Teste de integracao: pipeline completo (gerar -> recortar -> corrigir) com
respostas sinteticas reais nas duas areas (multipla escolha e dissertativa).

Mistura corretos e em branco, igual ao experimento manual da Fase 0, mas
agora cobrindo tambem a area dissertativa e de forma reproduzivel:

  Joao   -> bolha certa (Q1) + escreve a frase na dissertativa em letra de
            forma (Q2)
  Maria  -> bolha certa (Q1); dissertativa em branco (controle)
  Carlos -> bolha em branco (controle); escreve a frase na dissertativa em
            cursiva (Q2)

Dois estilos de escrita (nao o mesmo duas vezes) para que o pipeline real
(nao so o experimento isolado da Fase 7) seja exercitado contra a variacao
de estilo que a Fase 7 mostrou afetar o OCR.

Uso: python3 tests/test_synthetic_answers.py
Assume cwd = MakeTests/ (raiz do repo, onde este script eh chamado por
validate-maketests.sh).
"""
import json
import os
import re
import shutil
import subprocess
import sys

import cv2
from PIL import Image, ImageDraw, ImageFont

TEST_QUICK = "test-quick"
DEBUG_DIR = "synth_debug"
FONT_PATH = os.path.abspath("tests/fixtures/ocr/fonts/PatrickHand-Regular.ttf")
CURSIVA_FONT_PATH = os.path.abspath("tests/fixtures/ocr/fonts/DancingScript-Regular.ttf")
PHRASE = "A LUZ VIRA ENERGIA"

# Geometria das areas de resposta (validada manualmente nas Fases 0/1)
WIDTH = 1024
HEADER_HEIGHT = 45
BORDER = 2
MARKER_RADIUS = HEADER_HEIGHT // 2
PADDING = MARKER_RADIUS


def mc_bubble_center(row):
    aspectrate = 32 / (4 + 1)
    ans_h = int(WIDTH / aspectrate)
    cell_w = WIDTH / 2
    cell_h = ans_h / 5
    cx = BORDER + cell_w / 2
    cy = BORDER + HEADER_HEIGHT + PADDING + (1 + row) * cell_h + cell_h / 2
    rad = int(min(cell_w, cell_h) // 3)
    if rad > WIDTH / 80:
        rad = int(WIDTH / 80)
    return int(cx), int(cy), rad


def paint_bubble(png_path, row):
    img = cv2.imread(png_path)
    cx, cy, rad = mc_bubble_center(row)
    cv2.circle(img, (cx, cy), rad, (0, 0, 0), thickness=-1)
    cv2.imwrite(png_path, img)


def write_handwritten_text(png_path, text, font_path=FONT_PATH):
    # Com a área redimensionada (lines=6, aspectrate=2/1) e a rasterização a
    # 300dpi, o limite de legibilidade caiu de ~60px (~8,4mm, ainda com
    # ruído) para ~12px (~1,7mm, leitura limpa) - testado empiricamente
    # variando o tamanho linha a linha. 36px (~5mm) fica confortavelmente
    # dentro da faixa de escrita manuscrita normal, com folga de segurança.
    img = Image.open(png_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, 36)
    y = BORDER + HEADER_HEIGHT + PADDING + 15
    draw.text((BORDER + 30, y), text, font=font, fill=(0, 0, 0))
    img.save(png_path)


def find_correct_rows(source_tex_path):
    text = open(source_tex_path).read()
    blocks = re.split(r"Nome: ", text)[1:]
    rows = []
    for b in blocks:
        m = re.search(
            r"\\begin\{multicols\}\{2\}\\begin\{enumerate\}.*?\]\\item (.*?)\\end\{enumerate\}\\end\{multicols\}",
            b, re.S)
        alts = [a.strip() for a in re.split(r"\\item ", m.group(1)) if a.strip()]
        rows.append([i for i, a in enumerate(alts) if "São Paulo" in a][0])
    return rows


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r


def fail(msg, r=None):
    print("SETUP FAIL:", msg)
    if r is not None:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    sys.exit(1)


def main():
    # 1) Regenerar com -t para ter os PNGs persistentes
    run('rm -rf {0} *.pdf Prova_Capital_SP_img.pdf Correcao/notas.csv '
        '"Correcao/João da Silva" "Correcao/Maria Santos" "Correcao/Carlos Oliveira"'
        .format(DEBUG_DIR), cwd=TEST_QUICK)
    r = run("python3 ../MakeTests.py -v -t {0}".format(DEBUG_DIR), cwd=TEST_QUICK)
    if r.returncode != 0:
        fail("geração inicial falhou", r)

    answer_dir = os.path.join(TEST_QUICK, DEBUG_DIR, "Tests")
    source_tex = os.path.join(answer_dir, "source.tex")
    correct_rows = find_correct_rows(source_tex)  # [joao, maria, carlos]

    # 2) Aplicar tratamentos (ver docstring do módulo) - Joao em letra de
    # forma, Carlos em cursiva: cobre os dois estilos que a Fase 7 mostrou
    # terem CER diferentes, em vez de testar o mesmo estilo duas vezes.
    paint_bubble(os.path.join(answer_dir, "AnswerArea-0.png"), correct_rows[0])
    write_handwritten_text(os.path.join(answer_dir, "AnswerArea-1.png"), PHRASE, font_path=FONT_PATH)
    paint_bubble(os.path.join(answer_dir, "AnswerArea-2.png"), correct_rows[1])
    write_handwritten_text(os.path.join(answer_dir, "AnswerArea-5.png"), PHRASE, font_path=CURSIVA_FONT_PATH)

    # 3) Recompilar pdflatex com as imagens já modificadas
    r = run("pdflatex -interaction=nonstopmode source.tex", cwd=answer_dir)
    if "Output written" not in r.stdout:
        fail("pdflatex não gerou o PDF", r)

    # 4) Copiar, rasterizar (simula prova escaneada)
    shutil.copy(os.path.join(answer_dir, "source.pdf"),
                os.path.join(TEST_QUICK, "Prova_Capital_SP.pdf"))
    r = run("bash ../convertPdfText2PdfImage.sh Prova_Capital_SP.pdf", cwd=TEST_QUICK)
    if r.returncode != 0:
        fail("conversão para imagem falhou", r)

    # 5) Corrigir com espião no banner de feedback (mesmo padrão de T2.4/T3.4)
    # Main.__init__ muda o cwd para a pasta do config_file; resolvemos os
    # caminhos para absolutos antes disso.
    notas_path = os.path.abspath(os.path.join(TEST_QUICK, "Correcao", "notas.csv"))
    config_path = os.path.abspath(os.path.join(TEST_QUICK, "config.json"))
    pdf_path = os.path.abspath(os.path.join(TEST_QUICK, "Prova_Capital_SP_img.pdf"))
    test_quick_abs = os.path.abspath(TEST_QUICK)

    sys.path.insert(0, os.getcwd())
    import MakeTests as MT
    captured = []
    original = MT.ImageUtils.drawTextInsideTheBox

    def spy(img, text, *a, **kw):
        captured.append(text)
        return original(img, text, *a, **kw)

    MT.ImageUtils.drawTextInsideTheBox = spy
    try:
        m = MT.Main(config_file=config_path,
                    config_default=MT.examples["config"], verbose=3, temp_dir=None)
        m.readPDF(pdf_path)
    finally:
        MT.ImageUtils.drawTextInsideTheBox = original

    # T0.6 — multipla escolha, end-to-end com resposta real
    notas = open(notas_path).read()
    rows = [line.split(";") for line in notas.strip().splitlines()[1:]]
    scores_q1 = {row[1]: row[3] for row in rows}
    ok_t06 = (scores_q1.get("João da Silva") == "100"
              and scores_q1.get("Maria Santos") == "100"
              and scores_q1.get("Carlos Oliveira") == "0")
    print("T0.6", "OK" if ok_t06 else "FAIL scores={}".format(scores_q1))

    # T1.8 — dissertativa, end-to-end com resposta real (texto realmente lido, nao mockado).
    # O OCR sobre a área pautada real ainda tem ruído residual ao redor do
    # texto (limitação conhecida, ver nota em ocr_extract.py) - a fidelidade
    # exata varia entre execuções, então o critério honesto aqui é "há sinal
    # real e substancial quando algo foi escrito, nada quando está em branco",
    # não reconhecimento perfeito.
    ocr_banners = [c for c in captured if c.startswith("OCR (raw):")]
    non_trivial = [c for c in ocr_banners if len(c) > len("OCR (raw): ") + 15]
    blank = [c for c in ocr_banners if c == "OCR (raw): "]
    ok_t18 = len(non_trivial) == 2 and len(blank) == 1
    print("T1.8", "OK" if ok_t18 else "FAIL ocr_banners={}".format(ocr_banners))

    # Fase 6 - sidecar HITL (q2_assist.json) + review_hitl.py
    joao_dir = os.path.join(test_quick_abs, "Correcao", "João da Silva")
    carlos_dir = os.path.join(test_quick_abs, "Correcao", "Carlos Oliveira")
    joao_sidecar_path = os.path.join(joao_dir, "Q_2_assist.json")
    carlos_sidecar_path = os.path.join(carlos_dir, "Q_2_assist.json")

    # T6.1 - sidecar criado com OCR, normalizado, nota sugerida, confianca e parecer
    try:
        joao_sidecar = json.load(open(joao_sidecar_path))
        ok_t61 = (joao_sidecar.get("ocr_text") and joao_sidecar.get("normalized_text")
                  and isinstance(joao_sidecar.get("suggested_score"), (int, float))
                  and joao_sidecar.get("confidence_score") is not None
                  and joao_sidecar.get("rationale") is not None)
    except Exception as e:
        ok_t61, joao_sidecar = False, {}
        print("T6.1 erro:", e)
    print("T6.1", "OK" if ok_t61 else "FAIL sidecar={}".format(joao_sidecar))

    # T6.2 - notas.csv ja tem Q_2 preenchido (nota sugerida), mas sidecar ainda pendente
    q2_joao_csv = {row[1]: row[4] for row in rows}.get("João da Silva")
    ok_t62 = (q2_joao_csv is not None and q2_joao_csv != ""
              and joao_sidecar.get("status_hitl") == "pendente")
    print("T6.2", "OK" if ok_t62 else "FAIL Q_2={} status_hitl={}".format(q2_joao_csv, joao_sidecar.get("status_hitl")))

    # T6.6 - regressao: questao objetiva (Q_1) nao gera sidecar
    ok_t66 = not os.path.exists(os.path.join(joao_dir, "Q_1_assist.json"))
    print("T6.6", "OK" if ok_t66 else "FAIL Q_1_assist.json nao deveria existir")

    # T6.3 - review_hitl.py list mostra o pendente do Joao
    r = run("python3 ../review_hitl.py list", cwd=test_quick_abs)
    ok_t63 = "João da Silva" in r.stdout and "pendente" in r.stdout
    print("T6.3", "OK" if ok_t63 else "FAIL stdout={}".format(r.stdout))

    # T6.4 - review_hitl.py accept confirma a nota sugerida do Joao
    r = run('python3 ../review_hitl.py accept "João da Silva" 2', cwd=test_quick_abs)
    joao_sidecar_after = json.load(open(joao_sidecar_path)) if os.path.exists(joao_sidecar_path) else {}
    ok_t64 = r.returncode == 0 and joao_sidecar_after.get("status_hitl") == "aceito"
    print("T6.4", "OK" if ok_t64 else "FAIL rc={} sidecar={}".format(r.returncode, joao_sidecar_after))

    # T6.5 - review_hitl.py adjust sobrescreve a nota sugerida do Carlos
    r = run('python3 ../review_hitl.py adjust "Carlos Oliveira" 2 70', cwd=test_quick_abs)
    carlos_sidecar_after = json.load(open(carlos_sidecar_path)) if os.path.exists(carlos_sidecar_path) else {}
    notas_after = open(notas_path).read()
    rows_after = [line.split(";") for line in notas_after.strip().splitlines()[1:]]
    q2_carlos_csv_after = {row[1]: row[4] for row in rows_after}.get("Carlos Oliveira")
    ok_t65 = (r.returncode == 0 and carlos_sidecar_after.get("status_hitl") == "ajustado"
              and carlos_sidecar_after.get("manual_score") == 70.0
              and q2_carlos_csv_after == "70.0")
    print("T6.5", "OK" if ok_t65 else "FAIL rc={} sidecar={} Q_2={}".format(r.returncode, carlos_sidecar_after, q2_carlos_csv_after))

    run("rm -rf {0} Prova_Capital_SP_img.pdf".format(DEBUG_DIR), cwd=test_quick_abs)


if __name__ == "__main__":
    main()
