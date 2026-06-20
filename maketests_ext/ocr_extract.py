def extract_text(image_bgr):
    """Extrai texto de uma imagem BGR (recorte da área de resposta) via Tesseract.

    O pré-processamento de QuestionOCR.doCorrection (blur+threshold+morphology)
    foi desenhado para reforçar marcas/bolhas grossas, não texto fino — testado
    contra uma área de resposta real (com as linhas pautadas de
    QuestionDissertative.drawAnswerArea), ele destrói completamente a
    legibilidade do texto. Sem pré-processamento, com --psm 6 (bloco de texto
    uniforme, suporta múltiplas linhas), funciona bem tanto nas fixtures
    golden quanto numa área pautada real.
    """
    import cv2
    import pytesseract
    from pytesseract import Output

    img_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    data = pytesseract.image_to_data(img_gray, lang="por", config="--psm 6", output_type=Output.DICT)

    words = []
    confs = []
    doubt_chars = 0
    total_chars = 0
    for word, conf in zip(data["text"], data["conf"]):
        word = word.strip()
        if not word:
            continue
        conf = int(conf)
        words.append(word)
        total_chars += len(word)
        if conf >= 0:
            confs.append(conf)
            if conf < 50:
                doubt_chars += len(word)

    confidence_mean = (sum(confs) / len(confs) / 100.0) if confs else None
    char_doubt_ratio = (doubt_chars / total_chars) if total_chars > 0 else 0.0

    return {
        "text": " ".join(words),
        "engine": "tesseract",
        "confidence_mean": confidence_mean,
        "char_doubt_ratio": char_doubt_ratio,
        "writing_style_hint": None,
    }
