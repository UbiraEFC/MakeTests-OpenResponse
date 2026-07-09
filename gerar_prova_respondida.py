#!/usr/bin/env python3
"""Gera uma "prova respondida" sintética (sem precisar imprimir/escanear),
a partir de um arquivo `respostas.json` editável pelo usuário.

Etapa 1.5 do fluxo de teste manual (ver GUIA-TESTE-AO-VIVO.md): fica entre
"1) gerar prova em branco" e "2) corrigir". Reaproveita a mesma técnica já
validada em tests/test_synthetic_answers.py (pintar a bolha certa/errada,
escrever texto com fonte de mão na área pautada, recompilar o LaTeX,
rasterizar) só que controlada por dados em vez de hardcoded no teste.

Formato de respostas.json (chaves = %NAME% exato do Students.csv):

    {
      "João da Silva": {
        "Q1": "correta",
        "Q2": {"texto": "A fotossintese converte luz solar em energia...", "estilo": "forma"}
      },
      "Maria Santos": {"Q1": "errada", "Q2": "branco"},
      "Carlos Oliveira": {"Q1": "branco", "Q2": {"texto": "...", "estilo": "cursiva"}}
    }

Limitação conhecida (assumida de propósito, não é bug): assume a mesma
configuração da fixture test-quick/ hoje — Q1 é a primeira questão
selecionada em config.json e é de múltipla escolha (4 alternativas,
resposta correta contendo o texto de CORRECT_SUBSTRING); Q2 é a segunda
selecionada e é QuestionDissertative. Se test-quick/config.json mudar de
formato (mais questões, outros tipos), este script precisa de ajuste — não
é uma ferramenta genérica para qualquer config.json, é um atalho para a
fixture de demonstração usada no teste ao vivo com o professor.

Uso:
    python3 gerar_prova_respondida.py                       # usa test-quick/respostas.json
    python3 gerar_prova_respondida.py --respostas outro.json
    python3 gerar_prova_respondida.py --dir test-quick

Saída: <dir>/Prova_Capital_SP_img.pdf, pronto para a Etapa 2 (correção):
    python3 MakeTests.py -vv -p <dir>/Prova_Capital_SP_img.pdf
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import cv2
from PIL import Image, ImageDraw, ImageFont

FONT_FORMA = "tests/fixtures/ocr/fonts/PatrickHand-Regular.ttf"
FONT_CURSIVA = "tests/fixtures/ocr/fonts/DancingScript-Regular.ttf"
CORRECT_SUBSTRING = "São Paulo"  # ver docstring: específico da fixture capital_sp.py
DEBUG_DIR = "gerar_prova_respondida_tmp"

# Geometria das áreas de resposta (mesma da Fase 0/1, ver test_synthetic_answers.py)
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


def write_handwritten_text(png_path, text, font_path):
    img = Image.open(png_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, 36)
    y = BORDER + HEADER_HEIGHT + PADDING + 15
    draw.text((BORDER + 30, y), text, font=font, fill=(0, 0, 0))
    img.save(png_path)


def find_alternatives(source_tex_path):
    """Retorna, por aluno (na ordem do Students.csv), a lista de alternativas
    da questão de múltipla escolha e o índice da correta."""
    text = open(source_tex_path).read()
    blocks = re.split(r"Nome: ", text)[1:]
    result = []
    for b in blocks:
        m = re.search(
            r"\\begin\{multicols\}\{2\}\\begin\{enumerate\}.*?\]\\item (.*?)\\end\{enumerate\}\\end\{multicols\}",
            b, re.S)
        alts = [a.strip() for a in re.split(r"\\item ", m.group(1)) if a.strip()]
        correct = next(i for i, a in enumerate(alts) if CORRECT_SUBSTRING in a)
        result.append((alts, correct))
    return result


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r


def fail(msg, r=None):
    print("FALHA:", msg)
    if r is not None:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default="test-quick", help="Pasta da fixture (config.json, Students.csv). Default: test-quick")
    parser.add_argument("--respostas", default=None, help="Caminho do respostas.json. Default: <dir>/respostas.json")
    args = parser.parse_args()

    base = os.path.abspath(args.dir)
    respostas_path = args.respostas or os.path.join(base, "respostas.json")
    if not os.path.exists(respostas_path):
        fail("arquivo de respostas não encontrado: {}".format(respostas_path))

    respostas = json.load(open(respostas_path, encoding="utf-8"))

    # Ordem dos alunos = ordem no Students.csv (mesma ordem em que MakeTests.py gera as provas)
    students_csv = os.path.join(base, "Students.csv")
    with open(students_csv, encoding="utf-8") as f:
        header = f.readline().split(";")
        name_col = [h.strip().strip('"') for h in header].index("%NAME%")
        student_names = []
        for line in f:
            if not line.strip():
                continue
            student_names.append(line.split(";")[name_col].strip().strip('"'))

    for name in student_names:
        if name not in respostas:
            fail("respostas.json não tem entrada para o aluno '{}' (Students.csv)".format(name))

    root = os.getcwd()
    maketests_py = os.path.join(root, "MakeTests.py")

    # 1) Regenerar com -t para ter os PNGs persistentes
    run('rm -rf "{0}" *.pdf Prova_Capital_SP_img.pdf'.format(DEBUG_DIR), cwd=base)
    r = run('python3 "{0}" -v -t {1}'.format(maketests_py, DEBUG_DIR), cwd=base)
    if r.returncode != 0:
        fail("geração inicial da prova em branco falhou", r)

    answer_dir = os.path.join(base, DEBUG_DIR, "Tests")
    source_tex = os.path.join(answer_dir, "source.tex")
    alternativas_por_aluno = find_alternatives(source_tex)

    num_questions = 2  # Q1 (múltipla escolha) + Q2 (dissertativa) — ver limitação no docstring

    # 2) Aplicar as respostas de cada aluno nas imagens AnswerArea-N.png
    #    (N = student_idx * num_questions + question_idx, ordem de geração do MakeTests.py)
    for student_idx, name in enumerate(student_names):
        r_aluno = respostas[name]
        q1 = r_aluno.get("Q1", "branco")
        q2 = r_aluno.get("Q2", "branco")

        alts, correct_row = alternativas_por_aluno[student_idx]
        q1_png = os.path.join(answer_dir, "AnswerArea-{}.png".format(student_idx * num_questions + 0))
        if q1 == "correta":
            paint_bubble(q1_png, correct_row)
        elif q1 == "errada":
            wrong_row = next(i for i in range(len(alts)) if i != correct_row)
            paint_bubble(q1_png, wrong_row)
        elif q1 == "branco":
            pass
        else:
            fail("valor inválido para Q1 do aluno '{}': {!r} (use correta/errada/branco)".format(name, q1))

        q2_png = os.path.join(answer_dir, "AnswerArea-{}.png".format(student_idx * num_questions + 1))
        if q2 == "branco":
            pass
        elif isinstance(q2, dict) and "texto" in q2:
            estilo = q2.get("estilo", "forma")
            font_path = os.path.abspath(FONT_CURSIVA if estilo == "cursiva" else FONT_FORMA)
            write_handwritten_text(q2_png, q2["texto"], font_path)
        else:
            fail("valor inválido para Q2 do aluno '{}': {!r} (use \"branco\" ou {{texto, estilo}})".format(name, q2))

        print("[{}] Q1={} Q2={}".format(name, q1, q2 if q2 == "branco" else "texto ({} chars, estilo={})".format(len(q2["texto"]), q2.get("estilo", "forma"))))

    # 3) Recompilar pdflatex com as imagens já modificadas
    r = run("pdflatex -interaction=nonstopmode source.tex", cwd=answer_dir)
    if "Output written" not in r.stdout:
        fail("pdflatex não conseguiu recompilar com as respostas aplicadas", r)

    # 4) Copiar para a raiz da fixture e rasterizar (simula prova escaneada)
    shutil.copy(os.path.join(answer_dir, "source.pdf"), os.path.join(base, "Prova_Capital_SP.pdf"))
    convert_sh = os.path.join(root, "convertPdfText2PdfImage.sh")
    r = run('bash "{0}" Prova_Capital_SP.pdf'.format(convert_sh), cwd=base)
    if r.returncode != 0:
        fail("conversão para PDF de imagens (simulação de scanner) falhou", r)

    run('rm -rf "{0}"'.format(DEBUG_DIR), cwd=base)

    print("\nOK: {} pronto.".format(os.path.join(args.dir, "Prova_Capital_SP_img.pdf")))
    print("Próximo passo (Etapa 2 — correção):")
    print('  python3 MakeTests.py -vv -p {}'.format(os.path.join(args.dir, "Prova_Capital_SP_img.pdf")))


if __name__ == "__main__":
    main()
