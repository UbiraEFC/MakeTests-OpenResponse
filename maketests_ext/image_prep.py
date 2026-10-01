def encode_for_vision(image_bgr, max_side=800, jpeg_quality=85):
    """Prepara um recorte BGR (area de resposta) para envio a um provider de
    LLM Vision: redimensiona para max_side no maior lado e codifica em JPEG.

    O recorte que chega em QuestionDissertative.doCorrection ja esta
    normalizado para 1024px de largura (MakeTests.py IMAGE_WIDTH) - maior
    que os ~800px recomendados no ADR-001 SS7 (estrategia de custo #2:
    tokens de imagem caem com a resolucao enviada). Redimensionar aqui evita
    gastar tokens sem ganho de legibilidade.

    Retorna (bytes, mime_type).
    """
    import cv2

    h, w = image_bgr.shape[:2]
    longest = max(h, w)
    if longest > max_side:
        scale = max_side / float(longest)
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))

    ok, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    if not ok:
        raise ValueError("Falha ao codificar imagem para JPEG")

    return buf.tobytes(), "image/jpeg"
