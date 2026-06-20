def extract_text(image_bgr):
    """Extrai texto de uma imagem BGR (recorte da área de resposta) via Tesseract.

    Reaproveita o pré-processamento de QuestionOCR.doCorrection (MakeTests.py).
    """
    import cv2
    import pytesseract
    from pytesseract import Output

    img_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.medianBlur(img_gray, 5)
    img_gray = cv2.GaussianBlur(img_gray, (7, 7), 0)
    img_gray = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 9, C=2)
    img_gray = cv2.morphologyEx(img_gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    data = pytesseract.image_to_data(img_gray, lang="por", output_type=Output.DICT)

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
