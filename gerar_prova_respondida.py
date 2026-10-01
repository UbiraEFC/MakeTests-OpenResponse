#!/usr/bin/env python3
"""Gera uma "prova respondida" sintética (sem precisar imprimir/escanear),
a partir de um arquivo `respostas.json` editável pelo usuário.

Etapa 1.5 do fluxo de teste manual (ver GUIA-TESTE-AO-VIVO.md): fica entre
"1) gerar prova em branco" e "2) corrigir". Reaproveita a mesma técnica já
validada em tests/test_synthetic_answers.py (pintar a bolha certa/errada,
escrever texto com fonte de mão na área pautada, recompilar o LaTeX,
rasterizar) só que controlada por dados em vez de hardcoded no teste.

Tudo é derivado do config.json da fixture — para trocar o tema da prova
NÃO é preciso editar este script:

  - Questões e ordem ....... config.json -> questions.select
  - Tipo de cada questão ... detectado do próprio .py (QuestionMultipleChoice
                             ou QuestionDissertative, via herança)
  - Alternativa correta .... lida das flags True nas `alternatives` do .py da
                             questão (o texto correto é estável mesmo com o
                             embaralhamento por aluno; casamos esse texto com
                             o source.tex gerado para cada aluno)
  - Nome dos PDFs .......... config.json -> output.tests
  - Cabeçalho por aluno .... config.json -> tex.test.header

Formato de respostas.json (chaves = %NAME% exato do Students.csv; Q1..QN
seguem a ordem de questions.select do config.json):

    {
      "João da Silva": {
        "Q1": "correta",
        "Q2": {"texto": "A fotossintese converte luz solar em energia...", "estilo": "forma"}
      },
      "Maria Santos": {"Q1": "errada", "Q2": "branco"},
      "Carlos Oliveira": {"Q1": "branco", "Q2": {"texto": "...", "estilo": "cursiva"}}
    }

O texto dissertativo é quebrado em linhas automaticamente para caber na
largura da área de resposta ("\n" no texto força quebra de parágrafo); se
não couber na altura, a fonte é reduzida gradualmente.

Limitação conhecida (assumida de propósito, não é bug): cada questão de
múltipla escolha deve ter exatamente 1 enunciado (1 coluna de bolhas) — é o
caso da fixture de demonstração. Tipos de questão além de múltipla
escolha/dissertativa não são suportados.

Uso:
    python3 gerar_prova_respondida.py                       # usa test-quick/respostas.json
    python3 gerar_prova_respondida.py --respostas outro.json
    python3 gerar_prova_respondida.py --dir test-quick

Saída: dois PDFs em <dir>:
    <nome>_respondida.pdf      — PDF digital (pdflatex) com as respostas, p/ conferência
    <nome>_respondida_img.pdf  — o mesmo, rasterizado a 300dpi (simula scanner);
                                 é ESTE que a Etapa 2 corrige:
    python3 MakeTests.py -vv -p <nome>_respondida_img.pdf <dir>/config.json
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

import cv2
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FORMA = os.path.join(SCRIPT_DIR, "tests", "fixtures", "ocr", "fonts", "PatrickHand-Regular.ttf")
FONT_CURSIVA = os.path.join(SCRIPT_DIR, "tests", "fixtures", "ocr", "fonts", "DancingScript-Regular.ttf")
DEBUG_DIR = "gerar_prova_respondida_tmp"

# Geometria das áreas de resposta (mesma da Fase 0/1, ver test_synthetic_answers.py)
WIDTH = 1024
HEADER_HEIGHT = 45
BORDER = 2
MARKER_RADIUS = HEADER_HEIGHT // 2
PADDING = MARKER_RADIUS

# Texto "manuscrito" na área dissertativa
TEXT_MARGIN_X = 30
TEXT_FONT_SIZE = 36   # tamanho inicial; reduz sozinho se o texto não couber
TEXT_MIN_FONT_SIZE = 20
TEXT_LINE_SPACING = 1.35


def mc_bubble_center(row, n_alts):
    aspectrate = 32 / (n_alts + 1)
    ans_h = int(WIDTH / aspectrate)
    cell_w = WIDTH / 2
    cell_h = ans_h / (n_alts + 1)
    cx = BORDER + cell_w / 2
    cy = BORDER + HEADER_HEIGHT + PADDING + (1 + row) * cell_h + cell_h / 2
    rad = int(min(cell_w, cell_h) // 3)
    if rad > WIDTH / 80:
        rad = int(WIDTH / 80)
    return int(cx), int(cy), rad


def paint_bubble(png_path, row, n_alts):
    img = cv2.imread(png_path)
    cx, cy, rad = mc_bubble_center(row, n_alts)
    cv2.circle(img, (cx, cy), rad, (0, 0, 0), thickness=-1)
    cv2.imwrite(png_path, img)


def wrap_text(draw, text, font, max_width):
    """Quebra `text` em linhas que caibam em `max_width` px ("\n" força parágrafo)."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if draw.textlength(candidate, font=font) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def write_handwritten_text(png_path, text, font_path):
    img = Image.open(png_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    x = BORDER + TEXT_MARGIN_X
    top = BORDER + HEADER_HEIGHT + PADDING + 15
    max_width = img.width - x - TEXT_MARGIN_X
    max_height = img.height - top - 15

    # Tenta o tamanho padrão; se as linhas não couberem na altura da área,
    # reduz a fonte gradualmente até caber (ou até o mínimo legível p/ OCR).
    for size in range(TEXT_FONT_SIZE, TEXT_MIN_FONT_SIZE - 1, -4):
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(draw, text, font, max_width)
        line_height = int(size * TEXT_LINE_SPACING)
        if len(lines) * line_height <= max_height:
            break
    else:
        print("AVISO: texto de {} não coube na área nem com fonte {}px; vai transbordar.".format(
            os.path.basename(png_path), TEXT_MIN_FONT_SIZE))

    y = top
    for line in lines:
        draw.text((x, y), line, font=font, fill=(0, 0, 0))
        y += line_height
    img.save(png_path)


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


def load_question(base, db_path, qpath):
    """Importa o .py da questão e devolve (instância, kind), onde kind é
    'mc' ou 'dissertativa' conforme a classe base herdada de MakeTests."""
    filename = os.path.join(base, db_path, qpath + ".py")
    if not os.path.exists(filename):
        fail("questão do config.json não encontrada: {}".format(filename))
    module_name = "_q_" + os.path.basename(qpath)
    spec = importlib.util.spec_from_file_location(module_name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    import inspect
    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module_name:
            mro_names = [c.__name__ for c in inspect.getmro(obj)]
            if "QuestionMultipleChoice" in mro_names:
                return obj(), "mc"
            if "QuestionDissertative" in mro_names:
                return obj(), "dissertativa"
    fail("não achei em {} uma classe QuestionMultipleChoice/QuestionDissertative "
         "(outros tipos não são suportados por este script)".format(filename))


def find_mc_blocks(source_tex_path, header_prefix, num_students):
    """Retorna, por aluno (ordem do Students.csv), a lista de blocos de
    alternativas (um bloco por questão de múltipla escolha, na ordem do
    config.json). Cada bloco é a lista dos textos das alternativas."""
    text = open(source_tex_path, encoding="utf-8").read()
    blocks = re.split(re.escape(header_prefix), text)[1:]
    if len(blocks) != num_students:
        fail("esperava {} blocos de aluno no source.tex (cabeçalho '{}'), achei {}".format(
            num_students, header_prefix, len(blocks)))
    # Enumerate de alternativas: label=\Alph*) — ver QuestionMultipleChoice.getQuestionTex
    alt_block_re = re.compile(r"label=\\textbf\{\\Alph\*\)\}\](.*?)\\end\{enumerate\}", re.S)
    result = []
    for b in blocks:
        student_blocks = []
        for content in alt_block_re.findall(b):
            alts = [normalize(a) for a in re.split(r"\\item ", content) if a.strip()]
            student_blocks.append(alts)
        result.append(student_blocks)
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

    # config.json é a fonte única: questões, nomes de saída, cabeçalho
    sys.path.insert(0, SCRIPT_DIR)  # p/ os .py das questões fazerem `from MakeTests import ...`
    config_path = os.path.join(base, "config.json")
    if not os.path.exists(config_path):
        fail("config.json não encontrado em {}".format(base))
    config = json.load(open(config_path, encoding="utf-8"))

    db_path = config["questions"]["db_path"]
    select = config["questions"]["select"]
    num_questions = len(select)

    # Nomes de saída derivados de output.tests (ex.: aed.pdf -> aed_respondida.pdf)
    tests_pdf = config["output"]["tests"]
    stem, ext = os.path.splitext(tests_pdf)
    answered_pdf = stem + "_respondida" + ext
    answered_img_pdf = stem + "_respondida_img" + ext

    # Prefixo do cabeçalho de cada aluno no LaTeX (tudo antes do 1º placeholder %...%)
    header_tpl = config["tex"]["test"]["header"]
    header_prefix = header_tpl.split("%")[0]
    if not header_prefix.strip():
        fail("tex.test.header do config.json não tem prefixo fixo antes do 1º placeholder — "
             "não dá para separar os alunos no source.tex")

    # Carrega cada questão selecionada e classifica (mc/dissertativa).
    # Para as MC, extrai os textos das alternativas corretas (flag True) —
    # estáveis sob embaralhamento — e o nº de alternativas (geometria).
    questions = []
    for sel in select:
        q, kind = load_question(base, db_path, sel["path"])
        info = {"path": sel["path"], "kind": kind}
        if kind == "mc":
            q.makeVariables()
            if len(q.questions) != 1:
                fail("questão MC '{}' tem {} enunciados; este script suporta apenas 1 (ver docstring)".format(
                    sel["path"], len(q.questions)))
            alts = q.questions[0]["alternatives"]
            info["n_alts"] = len(alts)
            info["correct_texts"] = {normalize(a[0]) for a in alts if a[1]}
            if not info["correct_texts"]:
                fail("questão MC '{}' não tem nenhuma alternativa com flag True".format(sel["path"]))
        questions.append(info)
    mc_indexes = [i for i, q in enumerate(questions) if q["kind"] == "mc"]

    # Ordem dos alunos = ordem no Students.csv (mesma ordem em que MakeTests.py gera as provas)
    students_csv = os.path.join(base, config["input"]["filename"])
    delimiter = config["input"].get("delimiter", ";")
    with open(students_csv, encoding="utf-8") as f:
        header = f.readline().split(delimiter)
        name_col = [h.strip().strip('"') for h in header].index("%NAME%")
        student_names = []
        for line in f:
            if not line.strip():
                continue
            student_names.append(line.split(delimiter)[name_col].strip().strip('"'))

    for name in student_names:
        if name not in respostas:
            fail("respostas.json não tem entrada para o aluno '{}' (Students.csv)".format(name))

    maketests_py = os.path.join(SCRIPT_DIR, "MakeTests.py")

    # 1) Regenerar com -t para ter os PNGs persistentes
    run('rm -rf "{0}" *.pdf'.format(DEBUG_DIR), cwd=base)
    r = run('python3 "{0}" -v -t {1}'.format(maketests_py, DEBUG_DIR), cwd=base)
    if r.returncode != 0:
        fail("geração inicial da prova em branco falhou", r)

    answer_dir = os.path.join(base, DEBUG_DIR, "Tests")
    source_tex = os.path.join(answer_dir, "source.tex")
    mc_blocks_por_aluno = find_mc_blocks(source_tex, header_prefix, len(student_names))

    # 2) Aplicar as respostas de cada aluno nas imagens AnswerArea-N.png
    #    (N = student_idx * num_questions + question_idx, ordem de geração do MakeTests.py)
    for student_idx, name in enumerate(student_names):
        r_aluno = respostas[name]
        resumo = []
        for qi, qinfo in enumerate(questions):
            key = "Q{}".format(qi + 1)
            valor = r_aluno.get(key, "branco")
            png = os.path.join(answer_dir, "AnswerArea-{}.png".format(student_idx * num_questions + qi))

            if qinfo["kind"] == "mc":
                blocks = mc_blocks_por_aluno[student_idx]
                alts = blocks[mc_indexes.index(qi)]
                if len(alts) != qinfo["n_alts"]:
                    fail("aluno '{}', {}: source.tex tem {} alternativas, esperava {}".format(
                        name, key, len(alts), qinfo["n_alts"]))
                correct_rows = [i for i, a in enumerate(alts) if a in qinfo["correct_texts"]]
                if len(correct_rows) != len(qinfo["correct_texts"]):
                    fail("aluno '{}', {}: não casei as alternativas corretas de {} com o source.tex "
                         "(corretas: {!r}; no tex: {!r})".format(name, key, qinfo["path"],
                                                                 qinfo["correct_texts"], alts))
                if valor == "correta":
                    for row in correct_rows:
                        paint_bubble(png, row, qinfo["n_alts"])
                elif valor == "errada":
                    wrong_row = next(i for i in range(len(alts)) if i not in correct_rows)
                    paint_bubble(png, wrong_row, qinfo["n_alts"])
                elif valor == "branco":
                    pass
                else:
                    fail("valor inválido para {} do aluno '{}': {!r} (use correta/errada/branco)".format(key, name, valor))
                resumo.append("{}={}".format(key, valor))

            else:  # dissertativa
                if valor == "branco":
                    resumo.append("{}=branco".format(key))
                elif isinstance(valor, dict) and "texto" in valor:
                    estilo = valor.get("estilo", "forma")
                    font_path = FONT_CURSIVA if estilo == "cursiva" else FONT_FORMA
                    write_handwritten_text(png, valor["texto"], font_path)
                    resumo.append("{}=texto ({} chars, estilo={})".format(key, len(valor["texto"]), estilo))
                else:
                    fail("valor inválido para {} do aluno '{}': {!r} (use \"branco\" ou {{texto, estilo}})".format(key, name, valor))

        print("[{}] {}".format(name, " ".join(resumo)))

    # 3) Recompilar pdflatex com as imagens já modificadas
    r = run("pdflatex -interaction=nonstopmode source.tex", cwd=answer_dir)
    if "Output written" not in r.stdout:
        fail("pdflatex não conseguiu recompilar com as respostas aplicadas", r)

    # 4) Copiar para a raiz da fixture e rasterizar (simula prova escaneada)
    shutil.copy(os.path.join(answer_dir, "source.pdf"), os.path.join(base, answered_pdf))
    convert_sh = os.path.join(SCRIPT_DIR, "convertPdfText2PdfImage.sh")
    r = run('bash "{0}" "{1}"'.format(convert_sh, answered_pdf), cwd=base)
    if r.returncode != 0:
        fail("conversão para PDF de imagens (simulação de scanner) falhou", r)

    run('rm -rf "{0}"'.format(DEBUG_DIR), cwd=base)

    print("\nOK: {} pronto.".format(os.path.join(args.dir, answered_img_pdf)))
    print("Próximo passo (Etapa 2 — correção; o config.json precisa estar no diretório")
    print("atual ou ser passado como argumento — o -p é relativo à pasta do config):")
    print('  python3 MakeTests.py -vv -p {} {}'.format(answered_img_pdf, os.path.join(args.dir, "config.json")))


if __name__ == "__main__":
    main()
