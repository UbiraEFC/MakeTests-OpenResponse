#!/usr/bin/env python3
"""Experimento offline da Fase 7: como o estilo de escrita (letra de forma,
cursiva, misto) afeta a qualidade do OCR (CER/WER), e correlacao qualitativa
com o score de confianca da Fase 5.

Corpus sintetico (nao caligrafia real - ver
tests/fixtures/ocr_styles/generate_corpus.py): 3 frases curtas em PT, cada
uma renderizada nos 3 estilos, 9 imagens no total.

Nao exige integracao ao fluxo principal de correcao - script independente,
sem rede/LLM (so Tesseract via maketests_ext.ocr_extract + jiwer).

Uso: python3 experiments/ocr_styles_eval.py
"""
import csv
import glob
import os
import sys

import cv2
import jiwer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maketests_ext.ocr_extract import extract_text
from maketests_ext.confidence_score import ConfidenceSignals, compute as compute_confidence

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "..", "tests", "fixtures", "ocr_styles")
RESULTS_CSV = os.path.join(HERE, "ocr_styles_results.csv")
ESTILOS = ("forma", "cursiva", "misto")


def load_corpus():
    items = []
    for png_path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.png"))):
        base = os.path.splitext(os.path.basename(png_path))[0]  # ex.: "cursiva_2"
        estilo = base.rsplit("_", 1)[0]
        txt_path = os.path.join(CORPUS_DIR, base + ".txt")
        with open(txt_path) as f:
            expected = f.read().strip()
        items.append({"estilo": estilo, "arquivo": base, "png": png_path, "expected": expected})
    return items


def evaluate(item):
    img = cv2.imread(item["png"])
    ocr_result = extract_text(img)
    obtained = ocr_result["text"]

    cer = jiwer.cer(item["expected"], obtained) if obtained else 1.0
    wer = jiwer.wer(item["expected"], obtained) if obtained else 1.0

    # Sinais LLM neutralizados - isola a contribuicao do OCR no score de
    # confianca, ja que aqui nao ha avaliacao semantica real rodando.
    confidence = compute_confidence(ConfidenceSignals(
        ocr_confidence_mean=ocr_result.get("confidence_mean"),
        ocr_char_doubt_ratio=ocr_result.get("char_doubt_ratio", 0.0),
        llm_review_recommended=False,
        rubric_coverage={},
    ))

    return {
        "estilo": item["estilo"],
        "arquivo": item["arquivo"],
        "texto_esperado": item["expected"],
        "texto_obtido": obtained,
        "cer": round(cer, 4),
        "wer": round(wer, 4),
        "confidence_score": confidence.score,
    }


def main():
    corpus = load_corpus()
    por_estilo = {e: [c for c in corpus if c["estilo"] == e] for e in ESTILOS}
    ok_t71 = len(corpus) >= 9 and all(len(por_estilo[e]) >= 3 for e in ESTILOS)
    print("T7.1", "OK" if ok_t71 else "FAIL corpus={} por_estilo={}".format(
        len(corpus), {e: len(v) for e, v in por_estilo.items()}))

    rows = [evaluate(item) for item in corpus]

    fieldnames = ["estilo", "arquivo", "texto_esperado", "texto_obtido", "cer", "wer", "confidence_score"]
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ok_t72 = os.path.exists(RESULTS_CSV) and len(rows) == len(corpus)
    print("T7.2", "OK" if ok_t72 else "FAIL rows={}".format(len(rows)))

    print()
    print("Resumo por estilo (medias):")
    medias = {}
    for estilo in ESTILOS:
        estilo_rows = [r for r in rows if r["estilo"] == estilo]
        mean_cer = sum(r["cer"] for r in estilo_rows) / len(estilo_rows)
        mean_wer = sum(r["wer"] for r in estilo_rows) / len(estilo_rows)
        mean_conf = sum(r["confidence_score"] for r in estilo_rows) / len(estilo_rows)
        medias[estilo] = {"cer": mean_cer, "wer": mean_wer, "confidence_score": mean_conf}
        print("  {:<10} CER={:.4f}  WER={:.4f}  confianca_media={:.1f}".format(
            estilo, mean_cer, mean_wer, mean_conf))

    # T7.3 - hipotese documentada (nao bloqueante): cursiva tende a ter CER
    # maior que letra de forma. Reporta o numero real, nunca falha.
    print("T7.3", "OK cer_cursiva={:.4f} cer_forma={:.4f} hipotese_confirmada={}".format(
        medias["cursiva"]["cer"], medias["forma"]["cer"],
        medias["cursiva"]["cer"] >= medias["forma"]["cer"]))

    print()
    print("Resultados completos em", RESULTS_CSV)


if __name__ == "__main__":
    main()
