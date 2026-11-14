#!/usr/bin/env python3
"""Teste de integracao: pipeline completo (gerar -> responder -> corrigir ->
revisar) com respostas sinteticas nas duas areas (multipla escolha e
dissertativa), pelo caminho LLM Vision com LLM_PROVIDER=mock.

Roda numa COPIA isolada de tests/prova-exemplo, com Students.csv proprio de 3
alunos. Tudo que depende do tema e derivado do config.json da fixture.

  Joao   -> bolha certa (Q1) + escreve a frase na dissertativa em letra de forma (Q2)
  Maria  -> bolha certa (Q1); dissertativa em branco (controle)
  Carlos -> bolha em branco (controle); escreve a frase na dissertativa em cursiva (Q2)

A aplicacao das respostas reusa tests/gerar_prova_respondida.py (pintar bolha,
escrever com fonte de mao, recompilar o LaTeX e rasterizar).

O mock nao le pixels (ver mock_provider.py): a transcricao e sempre o mesmo
texto fixo. O teste da dissertativa aqui e de wiring (o caminho vision roda
para as 3 respostas e produz feedback/sidecar), nao de qualidade de leitura.

Uso (a partir da raiz do repo): LLM_PROVIDER=mock python3 tests/test_synthetic_answers.py
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile

PHRASE = "A LUZ VIRA ENERGIA"

STUDENTS_CSV = """ID;Fullname;Email
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
    tests_home = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(tests_home, "prova-exemplo")

    # 1) Fixture isolada: copia de prova-exemplo (sem artefatos gerados), com
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
        os.path.join(tests_home, "gerar_prova_respondida.py"), fixture), cwd=root)
    if r.returncode != 0:
        fail("gerar_prova_respondida.py falhou", r)

    # 3) Corrigir com espiao no banner de feedback.
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
    name_key = next(k for k, v in cfg["input"]["header_replaces"].items() if v == "%NAME%")
    name_col = corr["headers"]["identification"][name_key]

    def q_col(n):
        return corr["headers"]["intermediate"].replace(corr["headers"]["counter"], str(n))

    def read_notas():
        with open(notas_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=corr["delimiter"], quotechar=corr["quotechar"])
            return {row[name_col]: row for row in reader}

    # T4.1 — multipla escolha, end-to-end com resposta marcada
    notas = read_notas()
    scores_q1 = {nome: row[q_col(1)] for nome, row in notas.items()}
    ok = (scores_q1.get("João da Silva") == "100"
          and scores_q1.get("Maria Santos") == "100"
          and scores_q1.get("Carlos Oliveira") == "0")
    print("T4.1", "OK" if ok else "FAIL scores={}".format(scores_q1))

    # T4.2 — dissertativa pelo caminho vision: banner de transcricao nas 3 respostas
    vision_banners = [c for c in captured if c.startswith("Transcricao (LLM):")]
    print("T4.2", "OK" if len(vision_banners) == 3 else "FAIL vision_banners={}".format(vision_banners))

    review_py = os.path.join(root, "review_hitl.py")
    joao_dir = os.path.join(fixture, corr["path"], "João da Silva")
    carlos_dir = os.path.join(fixture, corr["path"], "Carlos Oliveira")
    joao_sidecar_path = os.path.join(joao_dir, "Q_2_assist.json")
    carlos_sidecar_path = os.path.join(carlos_dir, "Q_2_assist.json")

    # T4.3 — sidecar com transcricao, nota sugerida, confianca e parecer
    try:
        joao_sidecar = json.load(open(joao_sidecar_path))
        ok = (joao_sidecar.get("transcription")
              and isinstance(joao_sidecar.get("suggested_score"), (int, float))
              and joao_sidecar.get("confidence_score") is not None
              and "confidence_review_recommended" in joao_sidecar
              and joao_sidecar.get("rationale") is not None)
    except Exception as e:
        ok, joao_sidecar = False, {}
        print("T4.3 erro:", e)
    print("T4.3", "OK" if ok else "FAIL sidecar={}".format(joao_sidecar))

    # T4.4 — notas.csv ja tem Q_2 (nota sugerida), mas sidecar ainda pendente
    q2_joao_csv = notas.get("João da Silva", {}).get(q_col(2))
    ok = q2_joao_csv not in (None, "") and joao_sidecar.get("status_hitl") == "pendente"
    print("T4.4", "OK" if ok else "FAIL Q_2={} status_hitl={}".format(q2_joao_csv, joao_sidecar.get("status_hitl")))

    # T4.5 — questao objetiva (Q_1) nao gera sidecar
    ok = not os.path.exists(os.path.join(joao_dir, "Q_1_assist.json"))
    print("T4.5", "OK" if ok else "FAIL Q_1_assist.json nao deveria existir")

    # T4.6 — review_hitl.py list mostra o pendente do Joao
    r = run('python3 "{0}" list'.format(review_py), cwd=fixture)
    ok = "João da Silva" in r.stdout and "pendente" in r.stdout
    print("T4.6", "OK" if ok else "FAIL stdout={} stderr={}".format(r.stdout, r.stderr[-500:]))

    # T4.7 — review_hitl.py accept confirma a nota sugerida do Joao
    r = run('python3 "{0}" accept "João da Silva" 2'.format(review_py), cwd=fixture)
    after = json.load(open(joao_sidecar_path)) if os.path.exists(joao_sidecar_path) else {}
    ok = r.returncode == 0 and after.get("status_hitl") == "aceito"
    print("T4.7", "OK" if ok else "FAIL rc={} sidecar={}".format(r.returncode, after))

    # T4.8 — review_hitl.py adjust sobrescreve a nota sugerida do Carlos
    r = run('python3 "{0}" adjust "Carlos Oliveira" 2 70'.format(review_py), cwd=fixture)
    after = json.load(open(carlos_sidecar_path)) if os.path.exists(carlos_sidecar_path) else {}
    q2_carlos = read_notas().get("Carlos Oliveira", {}).get(q_col(2))
    ok = (r.returncode == 0 and after.get("status_hitl") == "ajustado"
          and after.get("manual_score") == 70.0 and q2_carlos == "70.0")
    print("T4.8", "OK" if ok else "FAIL rc={} sidecar={} Q_2={}".format(r.returncode, after, q2_carlos))


if __name__ == "__main__":
    main()
