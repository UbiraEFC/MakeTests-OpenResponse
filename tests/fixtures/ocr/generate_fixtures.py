#!/usr/bin/env python3
"""Gera o corpus golden de OCR (texto impresso + "manuscrito" sintetico).

Reproducivel: roda de novo se precisar regenerar as imagens.
Uso: python3 generate_fixtures.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = "A fotossíntese converte luz solar em energia química."

SYSTEM_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HAND_FONT = os.path.join(HERE, "fonts", "PatrickHand-Regular.ttf")


def render(text, font_path, font_size, out_png):
    font = ImageFont.truetype(font_path, font_size)
    dummy = Image.new("RGB", (10, 10))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 60
    h = bbox[3] - bbox[1] + 60
    img = Image.new("RGB", (w, h), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), text, font=font, fill="black")
    img.save(out_png)


def main():
    render(TEXT, SYSTEM_FONT, 36, os.path.join(HERE, "printed_pt_01.png"))
    with open(os.path.join(HERE, "printed_pt_01.txt"), "w") as f:
        f.write(TEXT + "\n")

    render(TEXT, HAND_FONT, 48, os.path.join(HERE, "forma_pt_01.png"))
    with open(os.path.join(HERE, "forma_pt_01.txt"), "w") as f:
        f.write(TEXT + "\n")

    print("Fixtures geradas em", HERE)


if __name__ == "__main__":
    main()
