import uuid

from funcoes._db import cursor_banco
from funcoes.utils import (
    texto_obrigatorio, decimal_nao_negativo, vazio_para_none
)

UNIDADES = [
    "UN",   # unidade
    "PC",   # peça
    "CX",   # caixa
    "SC",   # saco
    "KG",   # quilograma
    "G",    # grama
    "L",    # litro
    "ML",   # mililitro
    "M",    # metro linear
    "M2",   # metro quadrado
    "MC3",  # metro cúbico
    "RL",   # rolo
]
TIPOS_LOCALIZACAO = ["INTERNA", "EXTERNA"]


def _validar_localizacao(tipo_localizacao, corredor=None, prateleira=None,
                         descricao_localizacao=None):
    tipo = (tipo_localizacao or "INTERNA").strip().upper()
    if tipo not in TIPOS_LOCALIZACAO:
        raise ValueError("Tipo de localização inválido.")

    if tipo == "EXTERNA":
        descricao = texto_obrigatorio(
            descricao_localizacao,
            "Descrição do local externo",
        )
        return tipo, None, None, descricao

    return (
        tipo,
        vazio_para_none(corredor),
        vazio_para_none(prateleira),
        None,
    )


def cadastrar_produto(nome, descricao, preco, quantidade_estoque, estoque_minimo,
                      unidade_medida, id_categoria, id_fornecedor=None,
                      tipo_localizacao="INTERNA", corredor=None, prateleira=None,
                      descricao_localizacao=None, ativo=True):
    nome = texto_obrigatorio(nome, "Nome")
    preco = decimal_nao_negativo(preco, "Preço")
    quantidade_estoque = decimal_nao_negativo(quantidade_estoque, "Estoque")
    estoque_minimo = decimal_nao_negativo(estoque_minimo, "Estoque mínimo")
    unidade_medida = texto_obrigatorio(unidade_medida, "Unidade de medida").upper()
    if unidade_medida not in UNIDADES:
        raise ValueError("Unidade de medida inválida.")

    tipo_localizacao, corredor, prateleira, descricao_localizacao = _validar_localizacao(
        tipo_localizacao, corredor, prateleira, descricao_localizacao
    )

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()
            # Código temporário único; após obter o ID, vira PRD-000001 etc.
            cursor.execute(
                """
                INSERT INTO produto
                    (codigo, nome, descricao, preco, quantidade_estoque, estoque_minimo,
                     unidade_medida, id_categoria, id_fornecedor, tipo_localizacao,
                     corredor, prateleira, descricao_localizacao, ativo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"TMP-{uuid.uuid4().hex[:20]}", nome, vazio_para_none(descricao), preco, quantidade_estoque,
                    estoque_minimo, unidade_medida, id_categoria, id_fornecedor or None,
                    tipo_localizacao, corredor, prateleira, descricao_localizacao, bool(ativo)
                ),
            )
            id_produto = cursor.lastrowid
            codigo = f"PRD-{id_produto:06d}"
            cursor.execute(
                "UPDATE produto SET codigo=%s WHERE id_produto=%s",
                (codigo, id_produto),
            )
            conexao.commit()
            return id_produto
        except Exception:
            conexao.rollback()
            raise


def listar_produtos(apenas_ativos=False):
    filtro = "WHERE p.ativo = TRUE" if apenas_ativos else ""
    with cursor_banco() as (_, cursor):
        cursor.execute(
            f"""
            SELECT p.*, c.nome AS categoria,
                   COALESCE(f.nome_fantasia, f.razao_social) AS fornecedor
            FROM produto p
            JOIN categoria c ON c.id_categoria = p.id_categoria
            LEFT JOIN fornecedor f ON f.id_fornecedor = p.id_fornecedor
            {filtro}
            ORDER BY p.nome
            """
        )
        return cursor.fetchall()


def obter_produto(id_produto):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT p.*, c.nome AS categoria,
                   COALESCE(f.nome_fantasia, f.razao_social) AS fornecedor
            FROM produto p
            JOIN categoria c ON c.id_categoria = p.id_categoria
            LEFT JOIN fornecedor f ON f.id_fornecedor = p.id_fornecedor
            WHERE p.id_produto=%s
            """,
            (id_produto,),
        )
        return cursor.fetchone()


def buscar_produto(termo, apenas_ativos=True):
    termo = f"%{(termo or '').strip()}%"
    ativo = "AND p.ativo = TRUE" if apenas_ativos else ""
    with cursor_banco() as (_, cursor):
        cursor.execute(
            f"""
            SELECT p.*, c.nome AS categoria,
                   COALESCE(f.nome_fantasia, f.razao_social) AS fornecedor
            FROM produto p
            JOIN categoria c ON c.id_categoria = p.id_categoria
            LEFT JOIN fornecedor f ON f.id_fornecedor = p.id_fornecedor
            WHERE (
                p.codigo LIKE %s OR p.nome LIKE %s OR c.nome LIKE %s
                OR f.razao_social LIKE %s OR f.nome_fantasia LIKE %s
                OR p.descricao_localizacao LIKE %s
            )
            {ativo}
            ORDER BY p.nome
            """,
            (termo, termo, termo, termo, termo, termo),
        )
        return cursor.fetchall()


def atualizar_produto(id_produto, nome, descricao, preco, quantidade_estoque,
                      estoque_minimo, unidade_medida, id_categoria,
                      id_fornecedor=None, tipo_localizacao="INTERNA",
                      corredor=None, prateleira=None,
                      descricao_localizacao=None, ativo=True):
    nome = texto_obrigatorio(nome, "Nome")
    preco = decimal_nao_negativo(preco, "Preço")
    decimal_nao_negativo(quantidade_estoque, "Estoque")
    estoque_minimo = decimal_nao_negativo(estoque_minimo, "Estoque mínimo")
    unidade_medida = texto_obrigatorio(unidade_medida, "Unidade de medida").upper()
    if unidade_medida not in UNIDADES:
        raise ValueError("Unidade de medida inválida.")

    tipo_localizacao, corredor, prateleira, descricao_localizacao = _validar_localizacao(
        tipo_localizacao, corredor, prateleira, descricao_localizacao
    )

    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            UPDATE produto
            SET nome=%s, descricao=%s, preco=%s,
                estoque_minimo=%s, unidade_medida=%s, id_categoria=%s,
                id_fornecedor=%s, tipo_localizacao=%s, corredor=%s,
                prateleira=%s, descricao_localizacao=%s, ativo=%s
            WHERE id_produto=%s
            """,
            (
                nome, vazio_para_none(descricao), preco,
                estoque_minimo, unidade_medida, id_categoria,
                id_fornecedor or None, tipo_localizacao, corredor, prateleira,
                descricao_localizacao, bool(ativo), id_produto
            ),
        )
        conexao.commit()
        return cursor.rowcount > 0


def excluir_produto(id_produto):
    # Exclusão lógica evita quebrar histórico de vendas.
    with cursor_banco() as (conexao, cursor):
        cursor.execute("UPDATE produto SET ativo=FALSE WHERE id_produto=%s", (id_produto,))
        conexao.commit()
        return cursor.rowcount > 0
