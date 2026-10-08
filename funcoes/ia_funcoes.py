import difflib
import re
from decimal import Decimal, InvalidOperation

from funcoes._db import cursor_banco
from funcoes.ia_texto import expandir_termos, normalizar, tokens_relevantes


ACOES = {"BUSCAR", "LOCALIZAR", "CONSULTAR_ESTOQUE", "ESTOQUE_BAIXO"}
MAX_RESULTADOS = 12


# ---------------------------------------------------------------------------
# Catálogo real da loja: somente leitura
# ---------------------------------------------------------------------------

def _serializar_produto(p):
    if p.get("tipo_localizacao") == "EXTERNA":
        localizacao = (
            p.get("descricao_localizacao")
            or "Área externa sem descrição cadastrada"
        )
    else:
        partes = []
        if p.get("corredor"):
            partes.append(f"Corredor {p['corredor']}")
        if p.get("prateleira"):
            partes.append(f"Prateleira {p['prateleira']}")
        localizacao = " / ".join(partes) or "Localização interna não cadastrada"

    return {
        "id_produto": p["id_produto"],
        "codigo": p.get("codigo"),
        "nome": p["nome"],
        "descricao": p.get("descricao") or "",
        "categoria": p.get("categoria") or "Sem categoria",
        "fornecedor": p.get("fornecedor") or "Sem fornecedor",
        "preco": str(p["preco"]),
        "quantidade_estoque": str(p["quantidade_estoque"]),
        "estoque_minimo": str(p["estoque_minimo"]),
        "unidade_medida": p["unidade_medida"],
        "tipo_localizacao": p.get("tipo_localizacao") or "INTERNA",
        "localizacao": localizacao,
    }


def _carregar_produtos():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT p.*, c.nome AS categoria,
                   COALESCE(f.nome_fantasia, f.razao_social) AS fornecedor
            FROM produto p
            JOIN categoria c ON c.id_categoria = p.id_categoria
            LEFT JOIN fornecedor f ON f.id_fornecedor = p.id_fornecedor
            WHERE p.ativo = TRUE
            ORDER BY p.nome ASC
            """
        )
        return cursor.fetchall()


def _pontuar_produto(produto, termos, categorias=None):
    nome = normalizar(produto.get("nome"))
    descricao = normalizar(produto.get("descricao"))
    categoria = normalizar(produto.get("categoria"))
    codigo = normalizar(produto.get("codigo"))
    fornecedor = normalizar(produto.get("fornecedor"))
    localizacao = normalizar(
        " ".join(
            str(produto.get(c) or "")
            for c in ("corredor", "prateleira", "descricao_localizacao")
        )
    )

    score = 0.0

    for cat in categorias or []:
        cat_n = normalizar(cat)
        if not cat_n:
            continue
        if cat_n == categoria:
            score += 24
        elif cat_n in categoria:
            score += 14

    for termo in termos:
        termo_n = normalizar(termo)
        if not termo_n:
            continue

        if termo_n == codigo:
            score += 60
        if termo_n == nome:
            score += 45
        elif termo_n in nome:
            score += 25
        if termo_n in categoria:
            score += 14
        if termo_n in fornecedor:
            score += 8
        if termo_n in descricao:
            score += 7
        if termo_n in localizacao:
            score += 5

        for palavra in tokens_relevantes(termo_n):
            if palavra in nome:
                score += 6
            if palavra in categoria:
                score += 3
            if palavra in descricao:
                score += 2
            if palavra in fornecedor:
                score += 2

        similar_nome = difflib.SequenceMatcher(None, termo_n, nome).ratio()
        if similar_nome >= 0.56:
            score += 9 * similar_nome

    return score


def consultar_catalogo_inteligente(
    termos=None,
    categorias=None,
    acao="BUSCAR",
    quantidade_desejada=None,
    limite=8,
):
    acao = (acao or "BUSCAR").upper()
    if acao not in ACOES:
        acao = "BUSCAR"

    limite = max(1, min(int(limite or 8), 20))
    termos = expandir_termos(termos or [])
    categorias = [c for c in (categorias or []) if str(c).strip()]
    produtos = _carregar_produtos()

    if acao == "ESTOQUE_BAIXO":
        selecionados = [
            p for p in produtos
            if Decimal(str(p["quantidade_estoque"]))
            <= Decimal(str(p["estoque_minimo"]))
        ]
        selecionados.sort(
            key=lambda p: (
                Decimal(str(p["quantidade_estoque"]))
                - Decimal(str(p["estoque_minimo"])),
                normalizar(p["nome"]),
            )
        )
        selecionados = selecionados[:limite]
    else:
        pontuados = []
        for p in produtos:
            score = _pontuar_produto(p, termos, categorias)
            if score > 0:
                pontuados.append((score, p))
        pontuados.sort(key=lambda item: (-item[0], normalizar(item[1]["nome"])))
        selecionados = [p for _, p in pontuados[:limite]]

    resultado = [_serializar_produto(p) for p in selecionados]

    if quantidade_desejada is not None and resultado:
        try:
            desejada = Decimal(str(quantidade_desejada))
        except (InvalidOperation, TypeError, ValueError):
            desejada = None
        if desejada is not None and desejada >= 0:
            for produto in resultado:
                estoque = Decimal(produto["quantidade_estoque"])
                produto["quantidade_desejada"] = str(desejada)
                produto["quantidade_suficiente"] = estoque >= desejada

    return {
        "acao": acao,
        "termos": termos,
        "categorias": categorias,
        "quantidade_resultados": len(resultado),
        "produtos": resultado,
    }


def consultar_catalogo(termo="", acao="BUSCAR", quantidade_desejada=None, limite=8):
    return consultar_catalogo_inteligente(
        termos=[termo] if termo else [],
        acao=acao,
        quantidade_desejada=quantidade_desejada,
        limite=limite,
    )


# ---------------------------------------------------------------------------
# Consultas administrativas locais
# ---------------------------------------------------------------------------

def _moeda(valor):
    valor = Decimal(str(valor or 0))
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _numero(valor):
    d = Decimal(str(valor or 0))
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


def _formatar_produto(p, mostrar_preco=True, mostrar_minimo=False):
    codigo = f" [{p['codigo']}]" if p.get("codigo") else ""
    linha = f"• {p['nome']}{codigo}"
    if mostrar_preco:
        linha += f" — {_moeda(p['preco'])}"
    linha += f" | Estoque: {_numero(p['quantidade_estoque'])} {p['unidade_medida']}"
    if mostrar_minimo:
        linha += f" | Mínimo: {_numero(p['estoque_minimo'])} {p['unidade_medida']}"
    linha += f" | {p['localizacao']}"
    return linha


def _resumo_estoque():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_produtos,
                SUM(CASE WHEN quantidade_estoque <= 0 THEN 1 ELSE 0 END) AS sem_estoque,
                SUM(CASE WHEN quantidade_estoque <= estoque_minimo THEN 1 ELSE 0 END) AS estoque_baixo,
                SUM(CASE WHEN tipo_localizacao='EXTERNA' THEN 1 ELSE 0 END) AS externos
            FROM produto
            WHERE ativo=TRUE
            """
        )
        resumo = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS total FROM categoria")
        total_categorias = cursor.fetchone()["total"]

    return (
        "Resumo do estoque\n\n"
        f"• Produtos ativos: {resumo['total_produtos'] or 0}\n"
        f"• Categorias: {total_categorias or 0}\n"
        f"• Produtos sem estoque: {resumo['sem_estoque'] or 0}\n"
        f"• Produtos no mínimo ou abaixo do mínimo: {resumo['estoque_baixo'] or 0}\n"
        f"• Produtos em localização externa: {resumo['externos'] or 0}"
    )


def _listar_categorias():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT c.nome, COUNT(p.id_produto) AS total
            FROM categoria c
            LEFT JOIN produto p
              ON p.id_categoria=c.id_categoria AND p.ativo=TRUE
            GROUP BY c.id_categoria, c.nome
            ORDER BY c.nome
            """
        )
        rows = cursor.fetchall()

    if not rows:
        return "Nenhuma categoria cadastrada."
    linhas = ["Categorias cadastradas:"]
    linhas.extend(f"• {r['nome']}: {r['total']} produto(s)" for r in rows)
    return "\n".join(linhas)


def _listar_sem_estoque(limite=MAX_RESULTADOS):
    produtos = [_serializar_produto(p) for p in _carregar_produtos() if Decimal(str(p["quantidade_estoque"])) <= 0]
    if not produtos:
        return "Não há produtos ativos com estoque zerado."
    linhas = [f"Produtos sem estoque ({len(produtos)} encontrado(s)):"]
    linhas.extend(_formatar_produto(p, mostrar_minimo=True) for p in produtos[:limite])
    if len(produtos) > limite:
        linhas.append(f"... e mais {len(produtos) - limite} produto(s).")
    return "\n".join(linhas)


def _listar_estoque_baixo(limite=MAX_RESULTADOS):
    dados = consultar_catalogo_inteligente(acao="ESTOQUE_BAIXO", limite=limite)
    produtos = dados["produtos"]
    if not produtos:
        return "Nenhum produto está no estoque mínimo ou abaixo dele."
    linhas = ["Produtos que precisam de atenção para reposição:"]
    linhas.extend(_formatar_produto(p, mostrar_minimo=True) for p in produtos)
    return "\n".join(linhas)


def _listar_sem_localizacao(limite=MAX_RESULTADOS):
    resultado = []
    for p in _carregar_produtos():
        if p.get("tipo_localizacao") == "EXTERNA":
            faltando = not str(p.get("descricao_localizacao") or "").strip()
        else:
            faltando = not str(p.get("corredor") or "").strip() and not str(p.get("prateleira") or "").strip()
        if faltando:
            resultado.append(_serializar_produto(p))

    if not resultado:
        return "Todos os produtos ativos possuem uma localização cadastrada."
    linhas = ["Produtos sem localização completa:"]
    linhas.extend(_formatar_produto(p, mostrar_preco=False) for p in resultado[:limite])
    if len(resultado) > limite:
        linhas.append(f"... e mais {len(resultado) - limite} produto(s).")
    return "\n".join(linhas)


def _listar_sem_fornecedor(limite=MAX_RESULTADOS):
    produtos = [_serializar_produto(p) for p in _carregar_produtos() if not p.get("id_fornecedor")]
    if not produtos:
        return "Todos os produtos ativos possuem fornecedor vinculado."
    linhas = ["Produtos sem fornecedor vinculado:"]
    linhas.extend(_formatar_produto(p, mostrar_preco=False) for p in produtos[:limite])
    if len(produtos) > limite:
        linhas.append(f"... e mais {len(produtos) - limite} produto(s).")
    return "\n".join(linhas)


def _ultimas_movimentacoes(tipo=None, limite=12):
    limite = max(1, min(int(limite), 30))
    with cursor_banco() as (_, cursor):
        sql = """
            SELECT m.data_movimentacao, m.tipo, m.quantidade,
                   m.quantidade_anterior, m.quantidade_nova, m.motivo,
                   p.nome AS produto, p.unidade_medida,
                   COALESCE(f.nome, 'Sistema') AS funcionario
            FROM movimentacao_estoque m
            JOIN produto p ON p.id_produto=m.id_produto
            LEFT JOIN funcionario f ON f.id_funcionario=m.id_funcionario
        """
        params = []
        if tipo:
            sql += " WHERE m.tipo=%s"
            params.append(tipo)
        sql += " ORDER BY m.data_movimentacao DESC, m.id_movimentacao DESC LIMIT %s"
        params.append(limite)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

    if not rows:
        return "Não há movimentações de estoque para mostrar."

    titulo = "Últimas movimentações de estoque"
    if tipo == "ENTRADA":
        titulo = "Últimas entradas de estoque"
    elif tipo == "SAIDA":
        titulo = "Últimas saídas de estoque"

    linhas = [titulo + ":"]
    for r in rows:
        quando = r["data_movimentacao"].strftime("%d/%m/%Y %H:%M") if hasattr(r["data_movimentacao"], "strftime") else str(r["data_movimentacao"])
        linha = (
            f"• {quando} | {r['tipo']} | {r['produto']} | "
            f"{_numero(r['quantidade'])} {r['unidade_medida']} | "
            f"{_numero(r['quantidade_anterior'])} → {_numero(r['quantidade_nova'])} | "
            f"{r['funcionario']}"
        )
        if r.get("motivo"):
            linha += f" | {r['motivo']}"
        linhas.append(linha)
    return "\n".join(linhas)


def _extrair_quantidade(pergunta):
    n = normalizar(pergunta)
    padroes = [
        r"(?:tem|temos|preciso|precisa|disponivel|disponiveis)\s+(\d+(?:[.,]\d+)?)",
        r"(\d+(?:[.,]\d+)?)\s*(?:un|unidades?|sc|sacos?|kg|l|litros?|m2|mc3|m3|m)\b",
    ]
    for padrao in padroes:
        m = re.search(padrao, n)
        if m:
            try:
                return Decimal(m.group(1).replace(",", "."))
            except InvalidOperation:
                pass
    return None


def _termos_da_pergunta(pergunta):
    tokens = tokens_relevantes(pergunta)
    removidos = {
        "preco", "custa", "custam", "valor", "local", "localizacao", "codigo",
        "categoria", "fornecedor", "barato", "baratos", "barata", "baratas",
        "caro", "caros", "cara", "caras", "saldo", "quantidade", "minimo",
        "abaixo", "repor", "reposicao", "lista", "listar", "mostra", "mostrar",
    }
    tokens = [t for t in tokens if t not in removidos and not t.replace(".", "").isdigit()]
    termo = " ".join(tokens).strip()
    return [termo] if termo else []


def _buscar_produtos_da_pergunta(pergunta, limite=8):
    termos = _termos_da_pergunta(pergunta)
    if not termos:
        return []
    dados = consultar_catalogo_inteligente(termos=termos, limite=limite)
    return dados["produtos"]


def _resposta_produtos(pergunta):
    n = normalizar(pergunta)
    quantidade = _extrair_quantidade(pergunta)
    produtos = _buscar_produtos_da_pergunta(pergunta, limite=8)

    if not produtos:
        return (
            "Não encontrei um produto correspondente no cadastro.\n\n"
            "Tente informar o nome, código ou categoria. Exemplos: “cimento”, “CIM-001”, "
            "“tintas”, “tubo PVC 25 mm” ou “areia média”."
        )

    # Perguntas por preço escolhem extremos dentre os resultados mais relevantes.
    if any(x in n for x in ("mais barato", "mais barata", "menor preco")):
        menor = min(produtos, key=lambda p: Decimal(p["preco"]))
        return "Produto com menor preço entre os encontrados:\n\n" + _formatar_produto(menor)

    if any(x in n for x in ("mais caro", "mais cara", "maior preco")):
        maior = max(produtos, key=lambda p: Decimal(p["preco"]))
        return "Produto com maior preço entre os encontrados:\n\n" + _formatar_produto(maior)

    if quantidade is not None:
        p = produtos[0]
        estoque = Decimal(p["quantidade_estoque"])
        suficiente = estoque >= quantidade
        resposta = _formatar_produto(p)
        resposta += (
            f"\n\nQuantidade solicitada: {_numero(quantidade)} {p['unidade_medida']}. "
            + ("O estoque atual é suficiente." if suficiente else "O estoque atual NÃO é suficiente.")
        )
        if not suficiente:
            falta = quantidade - estoque
            resposta += f" Faltam {_numero(falta)} {p['unidade_medida']}."
        return resposta

    mostrar_preco = not any(x in n for x in ("onde", "local", "localizacao", "corredor", "prateleira"))
    linhas = []
    if len(produtos) == 1:
        linhas.append("Produto encontrado:")
    else:
        linhas.append(f"Encontrei {len(produtos)} produto(s) relacionado(s):")
    linhas.extend(_formatar_produto(p, mostrar_preco=mostrar_preco) for p in produtos)
    return "\n".join(linhas)


def _ajuda():
    return (
        "Assistente Local da Loja\n\n"
        "Funciona sem internet, sem chave e sem créditos. Ele consulta somente os dados reais do MySQL.\n\n"
        "Você pode perguntar, por exemplo:\n"
        "• onde fica o cimento CP II?\n"
        "• quanto tem de areia média?\n"
        "• qual o preço do tubo PVC 25 mm?\n"
        "• temos 20 sacos de cimento?\n"
        "• quais produtos estão com estoque baixo?\n"
        "• quais produtos estão sem estoque?\n"
        "• quais produtos estão sem localização?\n"
        "• quais categorias existem?\n"
        "• mostre um resumo do estoque\n"
        "• últimas entradas de estoque\n"
        "• últimas saídas de estoque\n\n"
        "O assistente é somente leitura: ele não altera estoque, não cadastra e não apaga produtos."
    )


# ---------------------------------------------------------------------------
# Interpretador local de linguagem natural
# ---------------------------------------------------------------------------

def status_ia():
    return {
        "modo": "LOCAL",
        "online": False,
        "texto": "Assistente local ativo — sem internet, sem chave e sem custo de API.",
    }


def responder_pergunta(pergunta, historico=None):
    pergunta = str(pergunta or "").strip()
    if not pergunta:
        raise ValueError("Digite uma pergunta.")

    n = normalizar(pergunta)

    if n in {"ajuda", "help", "comandos", "o que voce faz", "o que vc faz"}:
        return _ajuda(), "LOCAL"

    if any(frase in n for frase in ("resumo do estoque", "resumo estoque", "situacao do estoque", "visao geral do estoque")):
        return _resumo_estoque(), "LOCAL"

    if "categor" in n and any(x in n for x in ("listar", "lista", "quais", "mostra", "mostrar", "cadastr")):
        return _listar_categorias(), "LOCAL"

    if any(x in n for x in ("estoque baixo", "abaixo do minimo", "estoque minimo", "precisa repor", "precisam repor", "reposicao")):
        return _listar_estoque_baixo(), "LOCAL"

    if any(x in n for x in ("sem estoque", "estoque zerado", "zerado", "esgotado", "esgotados")):
        return _listar_sem_estoque(), "LOCAL"

    if any(x in n for x in ("sem localizacao", "sem corredor", "sem prateleira", "localizacao faltando")):
        return _listar_sem_localizacao(), "LOCAL"

    if any(x in n for x in ("sem fornecedor", "fornecedor faltando")):
        return _listar_sem_fornecedor(), "LOCAL"

    if any(x in n for x in ("ultimas movimentacoes", "movimentacoes recentes", "historico estoque", "historico de estoque")):
        return _ultimas_movimentacoes(), "LOCAL"

    if any(x in n for x in ("ultimas entradas", "entradas recentes", "o que entrou")):
        return _ultimas_movimentacoes("ENTRADA"), "LOCAL"

    if any(x in n for x in ("ultimas saidas", "saidas recentes", "o que saiu")):
        return _ultimas_movimentacoes("SAIDA"), "LOCAL"

    # Perguntas de catálogo, preço, localização, saldo e disponibilidade.
    return _resposta_produtos(pergunta), "LOCAL"
