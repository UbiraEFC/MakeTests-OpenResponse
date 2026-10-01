import re
import unicodedata


def normalize(raw):
    """Limpeza pos-OCR antes do LLM: NFKC, hifenizacao de fim de linha,
    quebras de linha espurias e espacos duplicados. Sem correcao gramatical.
    """
    text = unicodedata.normalize("NFKC", raw)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.replace("\n", " ")
    text = re.sub(r" +", " ", text)
    return text.strip()
