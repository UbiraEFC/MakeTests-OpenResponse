#!/usr/bin/env python3
"""Fase 5 do roadmap Q3 (ADR-001 §11): resultados estatisticos para o TCC.

Calcula, sem nenhuma chamada de API:
  1. Concordancia nota humana x nota do modelo (Pearson, Spearman, MAE,
     kappa ponderado quadratico em faixas de 20 pontos).
  2. Erro por estilo de escrita (letra de forma x cursiva).
  3. Taxa de encaminhamento ao HITL: Q2 (OCR) x vision com a formula antiga
     x vision recalibrada (modality="vision" em confidence_score.py),
     com precisao/recall contra as revisoes de fato necessarias.

Entradas:
  - Nota humana e CER por resposta: valores publicados em
    RESULTADOS-TESTE-CORPUS-FASE2.md §7.2 (derivados da transcricao
    ground-truth, que fica fora do repo por minimizacao de dados).
  - Sinais do modelo: sidecars corpus-fase2/*/Correcao-*/Escritor 1/Q_*_assist.json
    (gitignored, gerados localmente pela correcao real da Fase 2).

Uso: python3 experiments/fase5_resultados.py
"""
import glob
import json
import os
import statistics
import sys

from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maketests_ext.confidence_score import ConfidenceSignals, compute

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROVAS = {
    "aed": "prova1-algoritmos-estruturas-dados",
    "bm": "prova2-bases-matematicas",
    "matdis": "prova3-matematica-discreta",
}
ESTILO = {"ubi": "letra de forma", "lari": "cursiva"}

# (prova, escritor, questao) -> (nota_humana, CER%)  — RESULTADOS-TESTE-CORPUS-FASE2.md §7.2
GROUND_TRUTH = {
    ("aed", "lari", 1): (65, 2.6), ("aed", "lari", 2): (100, 0.0), ("aed", "lari", 3): (65, 0.0),
    ("aed", "ubi", 1): (80, 1.2), ("aed", "ubi", 2): (100, 0.7), ("aed", "ubi", 3): (50, 0.0),
    ("bm", "lari", 1): (65, 13.3), ("bm", "lari", 2): (45, 0.8), ("bm", "lari", 3): (100, 25.4),
    ("bm", "ubi", 1): (100, 15.1), ("bm", "ubi", 2): (85, 4.1), ("bm", "ubi", 3): (100, 0.0),
    ("matdis", "lari", 1): (100, 29.9), ("matdis", "lari", 2): (65, 14.9), ("matdis", "lari", 3): (45, 17.1),
    ("matdis", "ubi", 1): (65, 9.3), ("matdis", "ubi", 2): (25, 1.4), ("matdis", "ubi", 3): (90, 12.5),
}

# Revisao humana "necessaria": nota do modelo diverge da humana em mais que
# este limiar (pontos, escala 0-100). 10 pontos ~ meio criterio de rubrica.
LIMIAR_DIVERGENCIA = 10

# Baseline Q2 (RESULTADOS-TESTE-PROVAS-REAIS-OCR.md §5.3): 4/4 encaminhadas.
Q2_ENCAMINHADAS, Q2_TOTAL = 4, 4


def faixa(nota, largura=20):
    return min(int(nota // largura), 100 // largura - 1)


def kappa_ponderado_quadratico(a, b, k):
    n = len(a)
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x][y] += 1
    hist_a = [sum(obs[i]) for i in range(k)]
    hist_b = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = (i - j) ** 2 / (k - 1) ** 2
            num += w * obs[i][j]
            den += w * hist_a[i] * hist_b[j] / n
    return 1 - num / den if den else 1.0


def carregar():
    linhas = []
    for (prova, escritor, q), (nota_h, cer) in sorted(GROUND_TRUTH.items()):
        path = os.path.join(ROOT, "corpus-fase2", PROVAS[prova], "Correcao-" + escritor,
                            "Escritor 1", "Q_{}_assist.json".format(q))
        with open(path) as f:
            s = json.load(f)
        sinais = dict(llm_review_recommended=s["review_recommended"], llm_error=s.get("error"),
                      rubric_coverage=s.get("rubric_coverage") or {},
                      used_fallback=s["provider_metadata"].get("used_fallback", False))
        antiga = compute(ConfidenceSignals(**sinais))  # modality="ocr": formula pre-recalibracao
        nova = compute(ConfidenceSignals(modality="vision", **sinais))
        nota_m = s["suggested_score"]
        linhas.append({
            "id": "{}-{} Q{}".format(prova, escritor, q), "escritor": escritor,
            "nota_h": nota_h, "nota_m": nota_m, "delta": abs(nota_h - nota_m), "cer": cer,
            "llm_flag": s["review_recommended"],
            "conf_antiga": antiga.score, "hitl_antigo": antiga.review_recommended,
            "conf_nova": nova.score, "hitl_novo": nova.review_recommended,
            "necessaria": abs(nota_h - nota_m) > LIMIAR_DIVERGENCIA,
        })
    return linhas


def prec_recall(linhas, chave):
    enc = [l for l in linhas if l[chave]]
    nec = [l for l in linhas if l["necessaria"]]
    tp = sum(1 for l in enc if l["necessaria"])
    prec = tp / len(enc) if enc else float("nan")
    rec = tp / len(nec) if nec else float("nan")
    return len(enc), tp, prec, rec


def main():
    L = carregar()
    n = len(L)
    hs = [l["nota_h"] for l in L]
    ms = [l["nota_m"] for l in L]

    print("== 1. Concordancia nota humana x modelo (N={}) ==".format(n))
    r, p_r = pearsonr(hs, ms)
    rho, p_rho = spearmanr(hs, ms)
    print("Pearson r = {:.3f} (p={:.2g})".format(r, p_r))
    print("Spearman rho = {:.3f} (p={:.2g})".format(rho, p_rho))
    print("MAE = {:.2f} pontos | mediana |delta| = {} | max = {}".format(
        statistics.mean(l["delta"] for l in L), statistics.median(l["delta"] for l in L),
        max(l["delta"] for l in L)))
    print("|delta| <= 10: {}/{}".format(sum(1 for l in L if l["delta"] <= 10), n))
    vies = statistics.mean(m - h for h, m in zip(hs, ms))
    print("Vies medio (modelo - humano) = {:+.2f}".format(vies))
    qwk = kappa_ponderado_quadratico([faixa(x) for x in hs], [faixa(x) for x in ms], 5)
    print("Kappa ponderado quadratico (5 faixas de 20 pts) = {:.3f}".format(qwk))
    print("Faixa identica: {}/{}".format(sum(1 for h, m in zip(hs, ms) if faixa(h) == faixa(m)), n))

    print()
    print("== 2. Erro por estilo de escrita ==")
    for esc in ("ubi", "lari"):
        sub = [l for l in L if l["escritor"] == esc]
        print("{:15} N={}  CER medio={:5.2f}%  MAE nota={:5.2f}  vies={:+.2f}".format(
            ESTILO[esc], len(sub), statistics.mean(l["cer"] for l in sub),
            statistics.mean(l["delta"] for l in sub),
            statistics.mean(l["nota_m"] - l["nota_h"] for l in sub)))

    print()
    print("== 3. Encaminhamento ao HITL ==")
    print("Revisoes necessarias (|delta| > {}): {}/{} -> {}".format(
        LIMIAR_DIVERGENCIA, sum(l["necessaria"] for l in L), n,
        [l["id"] for l in L if l["necessaria"]]))
    print("Q2 (OCR)                  : {}/{} = {:.0%}".format(Q2_ENCAMINHADAS, Q2_TOTAL, Q2_ENCAMINHADAS / Q2_TOTAL))
    for rotulo, chave in (("Vision, formula antiga", "hitl_antigo"), ("Vision, recalibrada", "hitl_novo")):
        enc, tp, prec, rec = prec_recall(L, chave)
        print("{:26}: {}/{} = {:.0%}  | precisao={:.2f} recall={:.2f}".format(
            rotulo, enc, n, enc / n, prec, rec))
    print("Confianca media: antiga={:.1f} (max {}) | recalibrada={:.1f} (max {})".format(
        statistics.mean(l["conf_antiga"] for l in L), max(l["conf_antiga"] for l in L),
        statistics.mean(l["conf_nova"] for l in L), max(l["conf_nova"] for l in L)))

    print()
    print("{:16} {:>6} {:>6} {:>5} {:>6} {:>8} {:>8} {:>5}".format(
        "resposta", "nota_h", "nota_m", "|d|", "CER", "conf_ant", "conf_nov", "HITL"))
    for l in L:
        print("{:16} {:6} {:6} {:5} {:6.1f} {:8} {:8} {:>5}".format(
            l["id"], l["nota_h"], l["nota_m"], l["delta"], l["cer"], l["conf_antiga"],
            l["conf_nova"], "sim" if l["hitl_novo"] else "nao"))


if __name__ == "__main__":
    main()
