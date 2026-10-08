import re
import unicodedata
from funcoes.produto_funcoes import buscar_produto


STOPWORDS = {
    "onde", "esta", "está", "fica", "ficam", "encontro", "encontrar",
    "tem", "tenho", "produto", "produtos", "o", "a", "os", "as", "um", "uma",
    "no", "na", "nos", "nas", "do", "da", "dos", "das", "de", "por", "favor",
    "estoque", "localizacao", "localização", "qual", "corredor", "prateleira",
}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9\s-]", " ", texto).lower()


def extrair_termo(pergunta):
    palavras = _normalizar(pergunta).split()
    uteis = [p for p in palavras if p not in STOPWORDS and len(p) > 1]
    return " ".join(uteis).strip()


def _localizacao_produto(produto):
    if produto.get("tipo_localizacao") == "EXTERNA":
        descricao = produto.get("descricao_localizacao") or "local externo não descrito"
        return f"fora da loja — {descricao}"

    local = []
    if produto.get("corredor"):
        local.append(f"corredor {produto['corredor']}")
    if produto.get("prateleira"):
        local.append(f"prateleira {produto['prateleira']}")
    return ", ".join(local) if local else "localização interna não cadastrada"


def localizar_por_pergunta(pergunta):
    termo = extrair_termo(pergunta)
    if not termo:
        termo = (pergunta or "").strip()

    resultados = buscar_produto(termo, apenas_ativos=True)

    if not resultados and " " in termo:
        palavras = termo.split()
        candidatos = []
        vistos = set()
        for palavra in palavras:
            for produto in buscar_produto(palavra, apenas_ativos=True):
                if produto["id_produto"] not in vistos:
                    vistos.add(produto["id_produto"])
                    candidatos.append(produto)
        resultados = candidatos

    if not resultados:
        return {
            "mensagem": "Não encontrei um produto correspondente no cadastro.",
            "produtos": [],
        }

    linhas = []
    for p in resultados[:5]:
        linhas.append(
            f"{p['nome']}: {_localizacao_produto(p)}. "
            f"Estoque: {p['quantidade_estoque']} {p['unidade_medida']}."
        )

    return {
        "mensagem": "\n".join(linhas),
        "produtos": resultados[:5],
    }
