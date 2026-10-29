from decimal import Decimal
from funcoes._db import cursor_banco
from funcoes.utils import decimal_nao_negativo, decimal_positivo, vazio_para_none


def movimentar_estoque(id_produto, id_funcionario, tipo, quantidade, motivo=None):
    tipo = (tipo or "").upper()
    if tipo not in {"ENTRADA", "SAIDA", "AJUSTE"}:
        raise ValueError("Tipo de movimentação inválido.")

    if tipo == "AJUSTE":
        valor_informado = decimal_nao_negativo(quantidade, "Saldo final")
    else:
        valor_informado = decimal_positivo(quantidade, "Quantidade")

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()
            cursor.execute(
                "SELECT quantidade_estoque FROM produto WHERE id_produto=%s FOR UPDATE",
                (id_produto,),
            )
            produto = cursor.fetchone()
            if not produto:
                raise ValueError("Produto não encontrado.")

            anterior = Decimal(produto["quantidade_estoque"])

            if tipo == "ENTRADA":
                novo = anterior + valor_informado
                quantidade_movimento = valor_informado
            elif tipo == "SAIDA":
                novo = anterior - valor_informado
                if novo < 0:
                    raise ValueError("Estoque insuficiente. O saldo não pode ficar negativo.")
                quantidade_movimento = valor_informado
            else:
                novo = valor_informado
                quantidade_movimento = abs(novo - anterior)

            cursor.execute(
                "UPDATE produto SET quantidade_estoque=%s WHERE id_produto=%s",
                (novo, id_produto),
            )
            cursor.execute(
                """
                INSERT INTO movimentacao_estoque
                    (id_produto, id_funcionario, tipo, quantidade,
                     quantidade_anterior, quantidade_nova, motivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_produto, id_funcionario, tipo, quantidade_movimento,
                    anterior, novo, vazio_para_none(motivo)
                ),
            )
            conexao.commit()
            return novo
        except Exception:
            conexao.rollback()
            raise


def listar_movimentacoes(limite=200):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT m.id_movimentacao, m.data_movimentacao, p.nome AS produto,
                   m.tipo, m.quantidade, m.quantidade_anterior,
                   m.quantidade_nova, m.motivo,
                   COALESCE(f.nome, 'Sistema') AS funcionario
            FROM movimentacao_estoque m
            JOIN produto p ON p.id_produto = m.id_produto
            LEFT JOIN funcionario f ON f.id_funcionario = m.id_funcionario
            ORDER BY m.data_movimentacao DESC
            LIMIT %s
            """,
            (limite,),
        )
        return cursor.fetchall()


def produtos_estoque_baixo():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT id_produto, nome, quantidade_estoque, estoque_minimo, unidade_medida
            FROM produto
            WHERE ativo=TRUE AND quantidade_estoque <= estoque_minimo
            ORDER BY quantidade_estoque
            """
        )
        return cursor.fetchall()
