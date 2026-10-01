#!/usr/bin/env python3
"""CLI de revisao humana (HITL) para notas sugeridas por LLM em questoes
dissertativas (Fase 6). Le os sidecars `<questao>_assist.json` gravados por
Main.doCorrection em MakeTests.py e permite ao professor:

  list    - listar sidecars pendentes de revisao (ordenado por confianca)
  accept  - confirmar a nota sugerida como nota final
  adjust  - sobrescrever a nota sugerida com uma nota manual

Reusa MakeTests.Main/CorrectionManager (mesma forma de carregar config/CSV
usada por MakeTests.py e por tests/test_synthetic_answers.py) em vez de
reimplementar leitura de config.json/notas.csv.
"""
import argparse
import glob
import json
import os
import sys

import MakeTests as MT


def load_main(config_file):
    return MT.Main(config_file=config_file, config_default=MT.examples["config"], verbose=0)


def find_student_by_dirname(m, dirname):
    for s in m.students:
        _, full_path_student = m.makeDirectoryForAStudent(s)
        if os.path.basename(full_path_student) == dirname:
            return s
    return None


def sidecar_path_for(m, student, question_num):
    field_name = m.correction.fieldsname_quest[question_num - 1]
    _, full_path_student = m.makeDirectoryForAStudent(student)
    return field_name, os.path.join(full_path_student, field_name + "_assist.json")


def iter_sidecars(m):
    for s in m.students:
        _, full_path_student = m.makeDirectoryForAStudent(s)
        for path in sorted(glob.glob(os.path.join(full_path_student, "*_assist.json"))):
            with open(path) as f:
                yield path, json.load(f)


def cmd_list(args):
    m = load_main(args.config)
    rows = []
    for path, assist in iter_sidecars(m):
        if not args.all and assist.get("status_hitl") != "pendente":
            continue
        rows.append(assist)
    rows.sort(key=lambda a: (a.get("confidence_score") if a.get("confidence_score") is not None else -1))

    if not rows:
        print("Nenhum sidecar {}.".format("encontrado" if args.all else "pendente"))
        return

    for a in rows:
        student_label = " ".join(str(v) for v in a.get("student", {}).values())
        print("{:<10} {:<20} score={:<5} confianca={:<6}({:<3}) revisar={:<5} status={}".format(
            a.get("question", "?"),
            student_label,
            a.get("suggested_score"),
            a.get("confidence_level"),
            a.get("confidence_score"),
            a.get("review_recommended"),
            a.get("status_hitl"),
        ))


def cmd_accept(args):
    m = load_main(args.config)
    student = find_student_by_dirname(m, args.student_dir)
    if student is None:
        print("Aluno '{}' nao encontrado.".format(args.student_dir))
        sys.exit(1)

    field_name, path = sidecar_path_for(m, student, args.question_num)
    if not os.path.exists(path):
        print("Sidecar '{}' nao encontrado para '{}'.".format(path, args.student_dir))
        sys.exit(1)

    with open(path) as f:
        assist = json.load(f)

    score = assist["suggested_score"]
    m.correction.updateScore(student, args.question_num - 1, score)
    m.correction.save()

    assist["status_hitl"] = "aceito"
    with open(path, "w") as f:
        json.dump(assist, f, ensure_ascii=False, indent=2)

    print("{} de '{}' aceito com nota {}.".format(field_name, args.student_dir, score))


def cmd_adjust(args):
    m = load_main(args.config)
    student = find_student_by_dirname(m, args.student_dir)
    if student is None:
        print("Aluno '{}' nao encontrado.".format(args.student_dir))
        sys.exit(1)

    field_name, path = sidecar_path_for(m, student, args.question_num)
    if not os.path.exists(path):
        print("Sidecar '{}' nao encontrado para '{}'.".format(path, args.student_dir))
        sys.exit(1)

    with open(path) as f:
        assist = json.load(f)

    m.correction.updateScore(student, args.question_num - 1, args.score)
    m.correction.save()

    assist["status_hitl"] = "ajustado"
    assist["manual_score"] = args.score
    with open(path, "w") as f:
        json.dump(assist, f, ensure_ascii=False, indent=2)

    print("{} de '{}' ajustado para nota {}.".format(field_name, args.student_dir, args.score))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json", help="Arquivo de configuracao (JSON). Default: config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Listar sidecars de revisao.")
    p_list.add_argument("--all", action="store_true", help="Mostrar tambem os ja revisados (aceito/ajustado).")
    p_list.set_defaults(func=cmd_list)

    p_accept = sub.add_parser("accept", help="Confirmar a nota sugerida como nota final.")
    p_accept.add_argument("student_dir", help="Nome da pasta do aluno em Correcao/.")
    p_accept.add_argument("question_num", type=int, help="Numero da questao (1-based).")
    p_accept.set_defaults(func=cmd_accept)

    p_adjust = sub.add_parser("adjust", help="Sobrescrever a nota sugerida com uma nota manual.")
    p_adjust.add_argument("student_dir", help="Nome da pasta do aluno em Correcao/.")
    p_adjust.add_argument("question_num", type=int, help="Numero da questao (1-based).")
    p_adjust.add_argument("score", type=float, help="Nota final definida pelo professor.")
    p_adjust.set_defaults(func=cmd_adjust)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
