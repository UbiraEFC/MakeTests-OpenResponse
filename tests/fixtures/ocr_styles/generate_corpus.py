#!/usr/bin/env python3
"""Gera o corpus de estilos de escrita do experimento da Fase 7
(ver experiments/ocr_styles_eval.py): 3 frases curtas em PT, renderizadas
em 3 estilos (letra de forma, cursiva, misto) -> 9 imagens + ground truth.

Sintetico, nao caligrafia real (mesma ressalva ja documentada em
tests/fixtures/ocr/generate_fixtures.py para a Fase 2) - serve para
comparar como o OCR se comporta entre estilos, nao para validar
fidelidade a um manuscrito humano real.

Reproduzivel: roda de novo se precisar regenerar as imagens.
Uso: python3 generate_corpus.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(HERE, "..", "ocr", "fonts")
FORMA_FONT = os.path.join(FONTS_DIR, "PatrickHand-Regular.ttf")
CURSIVA_FONT = os.path.join(FONTS_DIR, "DancingScript-Regular.ttf")
FONT_SIZE = 48

SENTENCES = [
    "A fotossíntese converte luz solar em energia química.",
    "O ciclo da água envolve evaporação, condensação e precipitação.",
    "A revolução industrial transformou a produção e o trabalho.",
]


def _new_canvas(text, font):
    dummy = Image.new("RGB", (10, 10))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 60
    h = bbox[3] - bbox[1] + 60
    return Image.new("RGB", (w, h), color="white")


def render(text, font_path, out_png):
    font = ImageFont.truetype(font_path, FONT_SIZE)
    img = _new_canvas(text, font)
    ImageDraw.Draw(img).text((30, 30), text, font=font, fill="black")
    img.save(out_png)


def render_mixed(text, font_path_a, font_path_b, out_png):
    """Alterna a fonte palavra a palavra - simula a inconsistencia real de
    quem mistura cursiva e letra de forma na mesma resposta."""
    font_a = ImageFont.truetype(font_path_a, FONT_SIZE)
    font_b = ImageFont.truetype(font_path_b, FONT_SIZE)
    img = _new_canvas(text, font_a)  # canvas largo o suficiente nos dois casos
    draw = ImageDraw.Draw(img)
    x, y = 30, 30
    for i, word in enumerate(text.split(" ")):
        font = font_a if i % 2 == 0 else font_b
        draw.text((x, y), word, font=font, fill="black")
        x += draw.textbbox((0, 0), word + " ", font=font)[2]
    img.save(out_png)


def main():
    for i, sentence in enumerate(SENTENCES, start=1):
        render(sentence, FORMA_FONT, os.path.join(HERE, "forma_{}.png".format(i)))
        render(sentence, CURSIVA_FONT, os.path.join(HERE, "cursiva_{}.png".format(i)))
        render_mixed(sentence, FORMA_FONT, CURSIVA_FONT, os.path.join(HERE, "misto_{}.png".format(i)))
        for estilo in ("forma", "cursiva", "misto"):
            with open(os.path.join(HERE, "{}_{}.txt".format(estilo, i)), "w") as f:
                f.write(sentence + "\n")

    print("Corpus gerado em", HERE)


if __name__ == "__main__":
    main()
