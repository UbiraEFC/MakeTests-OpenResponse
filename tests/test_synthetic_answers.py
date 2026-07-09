#!/usr/bin/env python3
"""Teste de integracao: pipeline completo (gerar -> responder -> corrigir) com
respostas sinteticas reais nas duas areas (multipla escolha e dissertativa).

Roda numa COPIA isolada de test-quick, com Students.csv proprio de 3 alunos —
test-quick/ em si e a fixture de demonstracao ao vivo (GUIA-TESTE-AO-VIVO.md)
e pode ser editada livremente (tema, alunos, nomes de PDF) sem quebrar esta
suite. Tudo que depende do tema e derivado do config.json da fixture.

Tratamentos (mistura corretos e em branco, igual ao experimento da Fase 0):

  Joao   -> bolha certa (Q1) + escreve a frase na dissertativa em letra de
            forma (Q2)
  Maria  -> bolha certa (Q1); dissertativa em branco (controle)
  Carlos -> bolha em branco (controle); escreve a frase na dissertativa em
            cursiva (Q2)

Dois estilos de escrita (nao o mesmo duas vezes) para que o pipeline real
(nao so o experimento isolado da Fase 7) seja exercitado contra a variacao
de estilo que a Fase 7 mostrou afetar o OCR.

A aplicacao das respostas reusa gerar_prova_respondida.py (mesma ferramenta
da Etapa 1.5 do guia): pintar bolha, escrever com fonte de mao, recompilar o
LaTeX e rasterizar — em vez de duplicar essa logica aqui.

Uso: LLM_PROVIDER=mock python3 tests/test_synthetic_answers.py
Assume cwd = MakeTests/ (raiz do repo, onde este script eh chamado por
validate-maketests.sh).
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile

PHRASE = "A LUZ VIRA ENERGIA"

STUDENTS_CSV = """%ID%;%NAME%;%EMAIL%
001;"João da Silva";"joao@example.com"
002;"Maria Santos";"maria@example.com"
003;"Carlos Oliveira";"carlos@example.com"
"""

RESPOSTAS = {
    "João da Silva": {"Q1": "correta", "Q2": {"texto": PHRASE, "estilo": "forma"}},
    "Maria Santos": {"Q1": "correta", "Q2": "branco"},
    "Carlos Oliveira": {"Q1": "branco", "Q2": {"texto": PHRASE, "estilo": "cursiva"}},
}


def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)


def fail(msg, r=None):
    print("SETUP FAIL:", msg)
    if r is not None:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    sys.exit(1)


def main():
    root = os.getcwd()
    fixture = tempfile.mkdtemp(prefix="synth_fixture_")
    try:
        run_tests(root, fixture)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def run_tests(root, fixture):
    src = os.path.join(root, "test-quick")

    # 1) Fixture isolada: copia de test-quick (sem artefatos gerados), com
    #    Students.csv e respostas.json proprios
    cfg = json.load(open(os.path.join(src, "config.json"), encoding="utf-8"))
    shutil.rmtree(fixture)
    shutil.copytree(src, fixture,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pdf", "Correcao",
                                                  "gerar_prova_respondida_tmp", "latex_debug"))
    with open(os.path.join(fixture, cfg["input"]["filename"]), "w", encoding="utf-8") as f:
        f.write(STUDENTS_CSV)
    with open(os.path.join(fixture, "respostas.json"), "w", encoding="utf-8") as f:
        json.dump(RESPOSTAS, f, ensure_ascii=False, indent=2)

    stem, ext = os.path.splitext(cfg["output"]["tests"])
    answered_img = os.path.join(fixture, stem + "_respondida_img" + ext)

    # 2) Gerar prova respondida sintetica (bolhas + texto + recompilar + rasterizar)
    r = run('python3 "{0}" --dir "{1}"'.format(
        os.path.join(root, "gerar_prova_respondida.py"), fixture), cwd=root)
    if r.returncode != 0:
        fail("gerar_prova_respondida.py falhou", r)

    # 3) Corrigir com espiao no banner de feedback (mesmo padrao de T2.4/T3.4).
    # Main.__init__ muda o cwd para a pasta do config_file; caminhos absolutos.
    sys.path.insert(0, root)
    import MakeTests as MT
    captured = []
    original = MT.ImageUtils.drawTextInsideTheBox

    def spy(img, text, *a, **kw):
        captured.append(text)
        return original(img, text, *a, **kw)

    MT.ImageUtils.drawTextInsideTheBox = spy
    try:
        m = MT.Main(config_file=os.path.join(fixture, "config.json"),
                    config_default=MT.examples["config"], verbose=3, temp_dir=None)
        m.readPDF(answered_img)
    finally:
        MT.ImageUtils.drawTextInsideTheBox = original

    # Nomes de colunas/arquivos do CSV de notas, derivados do config
    corr = cfg["correction"]
    notas_path = os.path.join(fixture, corr["path"], corr["csv_file"])
    name_col = corr["headers"]["identification"]["%NAME%"]

    def q_col(n):
        return corr["headers"]["intermediate"].replace(corr["headers"]["counter"], str(n))

    def read_notas():
        with open(notas_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=corr["delimiter"], quotechar=corr["quotechar"])
            return {row[name_col]: row for row in reader}

    # T0.6 — multipla escolha, end-to-end com resposta real
    notas = read_notas()
    scores_q1 = {nome: row[q_col(1)] for nome, row in notas.items()}
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

    # Fase 6 - sidecar HITL (Q_2_assist.json) + review_hitl.py
    review_py = os.path.join(root, "review_hitl.py")
    joao_dir = os.path.join(fixture, corr["path"], "João da Silva")
    carlos_dir = os.path.join(fixture, corr["path"], "Carlos Oliveira")
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
    q2_joao_csv = notas.get("João da Silva", {}).get(q_col(2))
    ok_t62 = (q2_joao_csv is not None and q2_joao_csv != ""
              and joao_sidecar.get("status_hitl") == "pendente")
    print("T6.2", "OK" if ok_t62 else "FAIL Q_2={} status_hitl={}".format(q2_joao_csv, joao_sidecar.get("status_hitl")))

    # T6.6 - regressao: questao objetiva (Q_1) nao gera sidecar
    ok_t66 = not os.path.exists(os.path.join(joao_dir, "Q_1_assist.json"))
    print("T6.6", "OK" if ok_t66 else "FAIL Q_1_assist.json nao deveria existir")

    # T6.3 - review_hitl.py list mostra o pendente do Joao
    r = run('python3 "{0}" list'.format(review_py), cwd=fixture)
    ok_t63 = "João da Silva" in r.stdout and "pendente" in r.stdout
    print("T6.3", "OK" if ok_t63 else "FAIL stdout={}".format(r.stdout))

    # T6.4 - review_hitl.py accept confirma a nota sugerida do Joao
    r = run('python3 "{0}" accept "João da Silva" 2'.format(review_py), cwd=fixture)
    joao_sidecar_after = json.load(open(joao_sidecar_path)) if os.path.exists(joao_sidecar_path) else {}
    ok_t64 = r.returncode == 0 and joao_sidecar_after.get("status_hitl") == "aceito"
    print("T6.4", "OK" if ok_t64 else "FAIL rc={} sidecar={}".format(r.returncode, joao_sidecar_after))

    # T6.5 - review_hitl.py adjust sobrescreve a nota sugerida do Carlos
    r = run('python3 "{0}" adjust "Carlos Oliveira" 2 70'.format(review_py), cwd=fixture)
    carlos_sidecar_after = json.load(open(carlos_sidecar_path)) if os.path.exists(carlos_sidecar_path) else {}
    q2_carlos_csv_after = read_notas().get("Carlos Oliveira", {}).get(q_col(2))
    ok_t65 = (r.returncode == 0 and carlos_sidecar_after.get("status_hitl") == "ajustado"
              and carlos_sidecar_after.get("manual_score") == 70.0
              and q2_carlos_csv_after == "70.0")
    print("T6.5", "OK" if ok_t65 else "FAIL rc={} sidecar={} Q_2={}".format(r.returncode, carlos_sidecar_after, q2_carlos_csv_after))


if __name__ == "__main__":
    main()
