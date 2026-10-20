import re
import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9\s-]", " ", texto).lower().strip()


def extrair_termo_local(pergunta):
    normalizada = normalizar(pergunta)
    stopwords = {
        "onde", "esta", "fica", "ficam", "tem", "tenho", "quanto", "quantos",
        "quantas", "estoque", "produto", "produtos", "preciso", "quero", "achar",
        "encontrar", "encontro", "localizar", "localizacao", "corredor", "prateleira",
        "da", "de", "do", "das", "dos", "no", "na", "nos", "nas", "um", "uma",
        "o", "a", "os", "as", "para", "por", "favor", "disponivel", "disponiveis",
    }
    palavras = [p for p in normalizada.split() if p not in stopwords and len(p) > 1]
    return " ".join(palavras)
