import importlib.util
import json
import os
import time
from pathlib import Path
from decimal import Decimal

from funcoes._db import cursor_banco
from funcoes.ia_texto import normalizar, extrair_termo_local


def _arquivo_config_usuario():
    base = os.getenv("APPDATA")
    if base:
        pasta = Path(base) / "TccMateriaisConstrucao"
    else:
        pasta = Path.home() / ".tcc_materiais_construcao"
    return pasta / "config.env"


def _carregar_config_usuario():
    """Carrega configuração local sem exigir python-dotenv."""
    caminho = _arquivo_config_usuario()
    if not caminho.exists():
        return

    try:
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            valor = valor.strip()
            if chave and valor and not os.getenv(chave):
                os.environ[chave] = valor
    except OSError:
        pass


_carregar_config_usuario()


MODELO_IA = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
ACOES = {"BUSCAR", "LOCALIZAR", "CONSULTAR_ESTOQUE", "ESTOQUE_BAIXO"}

# Evita deixar a interface esperando muito tempo por uma API indisponível.
TEMPO_LIMITE_IA = max(2.0, float(os.getenv("OPENAI_TIMEOUT_SECONDS", "6")))
COOLDOWN_FALHA_IA = max(10.0, float(os.getenv("OPENAI_FAILURE_COOLDOWN_SECONDS", "60")))
_IA_INDISPONIVEL_ATE = 0.0
_CLIENTE_OPENAI = None



def _serializar_produto(p):
    if p.get("tipo_localizacao") == "EXTERNA":
        localizacao = p.get("descricao_localizacao") or "Área externa sem descrição cadastrada"
    else:
        partes = []
        if p.get("corredor"):
            partes.append(f"Corredor {p['corredor']}")
        if p.get("prateleira"):
            partes.append(f"Prateleira {p['prateleira']}")
        localizacao = " / ".join(partes) or "Localização interna não cadastrada"

    return {
        "id_produto": p["id_produto"],
        "nome": p["nome"],
        "categoria": p.get("categoria"),
        "preco": str(p["preco"]),
        "quantidade_estoque": str(p["quantidade_estoque"]),
        "estoque_minimo": str(p["estoque_minimo"]),
        "unidade_medida": p["unidade_medida"],
        "tipo_localizacao": p.get("tipo_localizacao") or "INTERNA",
        "localizacao": localizacao,
    }


def consultar_catalogo(termo="", acao="BUSCAR", quantidade_desejada=None, limite=8):
    """Consulta somente leitura usada pela IA. Não executa INSERT/UPDATE/DELETE."""
    acao = (acao or "BUSCAR").upper()
    if acao not in ACOES:
        acao = "BUSCAR"

    limite = max(1, min(int(limite or 8), 20))
    termo = (termo or "").strip()

    with cursor_banco() as (_, cursor):
        if acao == "ESTOQUE_BAIXO":
            cursor.execute(
                """
                SELECT p.*, c.nome AS categoria
                FROM produto p
                JOIN categoria c ON c.id_categoria=p.id_categoria
                WHERE p.ativo=TRUE
                  AND p.quantidade_estoque <= p.estoque_minimo
                ORDER BY p.quantidade_estoque ASC, p.nome ASC
                LIMIT %s
                """,
                (limite,),
            )
        else:
            like = f"%{termo}%"
            cursor.execute(
                """
                SELECT p.*, c.nome AS categoria
                FROM produto p
                JOIN categoria c ON c.id_categoria=p.id_categoria
                WHERE p.ativo=TRUE
                  AND (
                    p.nome LIKE %s OR p.descricao LIKE %s OR c.nome LIKE %s
                    OR p.corredor LIKE %s OR p.prateleira LIKE %s
                    OR p.descricao_localizacao LIKE %s
                  )
                ORDER BY
                    CASE WHEN p.nome LIKE %s THEN 0 ELSE 1 END,
                    p.nome ASC
                LIMIT %s
                """,
                (like, like, like, like, like, like, like, limite),
            )
        produtos = cursor.fetchall()

    resultado = [_serializar_produto(p) for p in produtos]

    if quantidade_desejada is not None and resultado:
        try:
            desejada = Decimal(str(quantidade_desejada))
        except Exception:
            desejada = None
        if desejada is not None:
            for produto in resultado:
                estoque = Decimal(produto["quantidade_estoque"])
                produto["quantidade_desejada"] = str(desejada)
                produto["quantidade_suficiente"] = estoque >= desejada

    return {
        "acao": acao,
        "termo": termo,
        "quantidade_resultados": len(resultado),
        "produtos": resultado,
    }



def _resposta_local(pergunta):
    normalizada = normalizar(pergunta)
    if "estoque baixo" in normalizada or ("baixo" in normalizada and "estoque" in normalizada):
        dados = consultar_catalogo(acao="ESTOQUE_BAIXO", limite=10)
    else:
        termo = extrair_termo_local(pergunta)
        dados = consultar_catalogo(termo=termo, acao="BUSCAR", limite=8)
        if not dados["produtos"] and " " in termo:
            for palavra in termo.split():
                dados = consultar_catalogo(termo=palavra, acao="BUSCAR", limite=8)
                if dados["produtos"]:
                    break

    if not dados["produtos"]:
        return "Não encontrei um produto correspondente no cadastro.", "LOCAL"

    linhas = []
    for p in dados["produtos"][:8]:
        linhas.append(
            f"• {p['nome']} — {p['localizacao']}. "
            f"Estoque: {p['quantidade_estoque']} {p['unidade_medida']}."
        )
    return "\n".join(linhas), "LOCAL"


def _ferramentas_openai():
    return [
        {
            "type": "function",
            "name": "consultar_catalogo",
            "description": (
                "Consulta o catálogo real da loja. Use sempre antes de responder sobre "
                "produto, localização, preço ou estoque. A função é somente leitura."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {
                        "type": "string",
                        "description": "Nome, categoria ou parte do produto pesquisado.",
                    },
                    "acao": {
                        "type": "string",
                        "enum": ["BUSCAR", "LOCALIZAR", "CONSULTAR_ESTOQUE", "ESTOQUE_BAIXO"],
                    },
                    "quantidade_desejada": {
                        "type": ["number", "null"],
                        "description": "Quantidade que o usuário quer verificar, quando informada.",
                    },
                },
                "required": ["termo", "acao", "quantidade_desejada"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    ]


def _cliente_openai():
    """Cria o cliente uma única vez, com timeout curto e sem retries longos."""
    global _CLIENTE_OPENAI
    if _CLIENTE_OPENAI is None:
        from openai import OpenAI

        _CLIENTE_OPENAI = OpenAI(
            timeout=TEMPO_LIMITE_IA,
            max_retries=0,
        )
    return _CLIENTE_OPENAI


def _marcar_falha_online():
    global _IA_INDISPONIVEL_ATE
    _IA_INDISPONIVEL_ATE = time.monotonic() + COOLDOWN_FALHA_IA


def _limpar_falha_online():
    global _IA_INDISPONIVEL_ATE
    _IA_INDISPONIVEL_ATE = 0.0


def _online_em_cooldown():
    return time.monotonic() < _IA_INDISPONIVEL_ATE


def _formatar_resultado_catalogo(dados):
    """Formata o retorno real do banco sem uma segunda chamada à API."""
    produtos = dados.get("produtos") or []
    if not produtos:
        return "Não encontrei um produto correspondente no cadastro."

    linhas = []
    for p in produtos[:8]:
        linha = (
            f"• {p['nome']} — Preço: R$ {Decimal(p['preco']):.2f}. "
            f"Estoque: {p['quantidade_estoque']} {p['unidade_medida']}. "
            f"Local: {p['localizacao']}."
        )
        if "quantidade_suficiente" in p:
            linha += (
                " Quantidade suficiente: sim."
                if p["quantidade_suficiente"]
                else " Quantidade suficiente: não."
            )
        linhas.append(linha)
    return "\n".join(linhas)


def status_ia():
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return {
            "online": False,
            "texto": "Busca local rápida ativa. Configure OPENAI_API_KEY para usar a IA online.",
            "modelo": None,
        }
    if importlib.util.find_spec("openai") is None:
        return {
            "online": False,
            "texto": "Busca local rápida ativa. O pacote 'openai' não está instalado.",
            "modelo": None,
        }

    if _online_em_cooldown():
        restante = max(1, int(_IA_INDISPONIVEL_ATE - time.monotonic()))
        return {
            "online": False,
            "texto": (
                "Busca local rápida ativa. A IA online falhou recentemente e será "
                f"tentada novamente em cerca de {restante}s."
            ),
            "modelo": MODELO_IA,
        }

    return {
        "online": True,
        "texto": f"IA OpenAI ativa — modelo {MODELO_IA}. Consultas têm timeout curto.",
        "modelo": MODELO_IA,
    }


def responder_pergunta(pergunta):
    """
    Responde sem bloquear a interface quando chamado por uma thread de trabalho.

    Otimizações:
    - timeout curto na OpenAI;
    - sem retries demorados;
    - somente uma chamada online por pergunta;
    - segunda etapa formatada localmente com dados reais do MySQL;
    - cooldown após falha para consultas seguintes caírem no modo local na hora.
    """
    pergunta = (pergunta or "").strip()
    if not pergunta:
        raise ValueError("Digite uma pergunta.")

    status = status_ia()
    if not status["online"]:
        return _resposta_local(pergunta)

    try:
        client = _cliente_openai()
        ferramentas = _ferramentas_openai()
        instrucoes = (
            "Você é o assistente de consulta de uma loja de materiais de construção. "
            "Interprete a pergunta e escolha os argumentos para consultar_catalogo. "
            "Nunca invente preço, estoque, localização ou disponibilidade. "
            "Você não pode cadastrar, excluir, vender ou alterar estoque. "
            "Para perguntas sobre catálogo, sempre chame consultar_catalogo."
        )

        resposta = client.responses.create(
            model=MODELO_IA,
            instructions=instrucoes,
            input=pergunta,
            tools=ferramentas,
            tool_choice="required",
        )

        chamadas = [
            item for item in resposta.output
            if getattr(item, "type", None) == "function_call"
            and getattr(item, "name", None) == "consultar_catalogo"
        ]

        if not chamadas:
            _limpar_falha_online()
            return _resposta_local(pergunta)

        respostas = []
        for chamada in chamadas[:3]:
            argumentos = json.loads(chamada.arguments)
            dados = consultar_catalogo(**argumentos)
            respostas.append(_formatar_resultado_catalogo(dados))

        _limpar_falha_online()
        texto = "\n\n".join(x for x in respostas if x).strip()
        if not texto:
            return _resposta_local(pergunta)
        return texto, "OPENAI"

    except Exception:
        _marcar_falha_online()
        # A resposta continua limpa; o estado de fallback aparece no status da UI.
        resposta, _ = _resposta_local(pergunta)
        return resposta, "FALLBACK"

