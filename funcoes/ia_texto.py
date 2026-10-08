import re
import unicodedata


SINONIMOS_MATERIAIS = {
    "areia para concreto": ["areia media", "areia lavada"],
    "areia concreto": ["areia media", "areia lavada"],
    "concreto": ["cimento", "areia media", "brita 1"],
    "reboco": ["areia para reboco", "areia fina", "argamassa reboco"],
    "assentamento": ["argamassa assentamento"],
    "porcelanato": ["argamassa porcelanato", "argamassa ac iii"],
    "piso sobre piso": ["argamassa piso sobre piso"],
    "piso externo": ["piso externo", "piso antiderrapante"],
    "fio": ["fio flexivel", "cabo flexivel"],
    "cano": ["tubo pvc"],
    "tubo": ["tubo pvc"],
    "brita": ["brita 0", "brita 1", "brita 2", "pedrisco"],
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-zA-Z0-9\s.,/%x-]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.lower().strip()


def tokens_relevantes(texto):
    stopwords = {
        "onde", "esta", "fica", "ficam", "tem", "tenho", "quanto", "quantos",
        "quantas", "estoque", "produto", "produtos", "preciso", "quero", "achar",
        "encontrar", "encontro", "localizar", "localizacao", "corredor", "prateleira",
        "da", "de", "do", "das", "dos", "no", "na", "nos", "nas", "um", "uma",
        "o", "a", "os", "as", "para", "por", "favor", "disponivel", "disponiveis",
        "qual", "quais", "usar", "uso", "fazer", "obra", "cliente", "me", "indica",
        "indicar", "recomenda", "recomendar", "seria", "melhor", "material", "materiais",
    }
    return [
        p for p in normalizar(texto).split()
        if p not in stopwords and len(p) > 1
    ]


def extrair_termo_local(pergunta):
    return " ".join(tokens_relevantes(pergunta))


def expandir_termos(termos):
    """Expande termos comuns sem inventar produtos nem acessar o banco."""
    if isinstance(termos, str):
        termos = [termos]

    resultado = []
    vistos = set()

    for termo in termos or []:
        bruto = (termo or "").strip()
        if not bruto:
            continue

        norm = normalizar(bruto)
        candidatos = [bruto]

        for chave, extras in SINONIMOS_MATERIAIS.items():
            if chave in norm or norm in chave:
                candidatos.extend(extras)

        for candidato in candidatos:
            chave = normalizar(candidato)
            if chave and chave not in vistos:
                vistos.add(chave)
                resultado.append(candidato)

    return resultado


def contem_todos(texto, palavras):
    norm = normalizar(texto)
    return all(normalizar(p) in norm for p in palavras)
