from decimal import Decimal

from funcoes._db import cursor_banco
from funcoes.calculos_caixa import calcular_diferenca, calcular_saldo_esperado
from funcoes.utils import decimal_nao_negativo, decimal_positivo, vazio_para_none


def obter_caixa_hoje():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT cd.*,
                   fa.nome AS funcionario_abertura,
                   ff.nome AS funcionario_fechamento
            FROM caixa_diario cd
            JOIN funcionario fa
              ON fa.id_funcionario = cd.id_funcionario_abertura
            LEFT JOIN funcionario ff
              ON ff.id_funcionario = cd.id_funcionario_fechamento
            WHERE cd.data_caixa = CURDATE()
            """
        )
        return cursor.fetchone()


def obter_caixa_aberto_hoje(cursor=None, for_update=False):
    sufixo = " FOR UPDATE" if for_update else ""
    if cursor is not None:
        cursor.execute(
            """
            SELECT *
            FROM caixa_diario
            WHERE data_caixa = CURDATE()
              AND status = 'ABERTO'
            LIMIT 1
            """ + sufixo
        )
        return cursor.fetchone()

    with cursor_banco() as (_, cur):
        return obter_caixa_aberto_hoje(cur, for_update=False)


def exigir_caixa_aberto(cursor=None, for_update=False):
    caixa = obter_caixa_aberto_hoje(cursor, for_update=for_update)
    if not caixa:
        raise ValueError(
            "O Caixa Diário não está aberto. Abra o Caixa Diário (F3) "
            "antes de finalizar uma venda."
        )
    return caixa


def abrir_caixa(id_funcionario, valor_abertura=0):
    """Abre o caixa do dia ou reabre o mesmo caixa caso ele esteja fechado.

    Existe apenas um registro de ``caixa_diario`` por data. Ao reabrir, o
    registro existente é reaproveitado para manter intactas as vendas e
    movimentações já vinculadas ao caixa. O valor de abertura original do dia
    também é preservado, evitando que o fundo de troco seja somado novamente.
    """
    valor_abertura = decimal_nao_negativo(valor_abertura, "Valor de abertura")

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()

            cursor.execute(
                """
                SELECT id_caixa, status
                FROM caixa_diario
                WHERE data_caixa = CURDATE()
                FOR UPDATE
                """
            )
            existente = cursor.fetchone()

            if existente:
                if existente["status"] == "ABERTO":
                    raise ValueError("O Caixa Diário de hoje já está aberto.")

                cursor.execute(
                    """
                    UPDATE caixa_diario
                    SET status = 'ABERTO'
                    WHERE id_caixa = %s
                    """,
                    (existente["id_caixa"],),
                )
                conexao.commit()
                return existente["id_caixa"]

            cursor.execute(
                """
                INSERT INTO caixa_diario
                    (data_caixa, id_funcionario_abertura, valor_abertura, status)
                VALUES (CURDATE(), %s, %s, 'ABERTO')
                """,
                (id_funcionario, valor_abertura),
            )
            id_caixa = cursor.lastrowid
            conexao.commit()
            return id_caixa
        except Exception:
            conexao.rollback()
            raise


def _totais_por_forma(cursor, id_caixa):
    cursor.execute(
        """
        SELECT pg.forma, COALESCE(SUM(pg.valor), 0) AS total
        FROM pagamento pg
        JOIN venda v ON v.id_venda = pg.id_venda
        WHERE v.id_caixa = %s
          AND v.status = 'FINALIZADA'
        GROUP BY pg.forma
        """,
        (id_caixa,),
    )
    dados = {linha["forma"]: Decimal(linha["total"]) for linha in cursor.fetchall()}
    return dados


def _totais_movimentacao(cursor, id_caixa):
    cursor.execute(
        """
        SELECT tipo, COALESCE(SUM(valor), 0) AS total
        FROM movimentacao_caixa
        WHERE id_caixa = %s
        GROUP BY tipo
        """,
        (id_caixa,),
    )
    dados = {linha["tipo"]: Decimal(linha["total"]) for linha in cursor.fetchall()}
    return dados


def _resumo_com_cursor(cursor, caixa):
    formas = _totais_por_forma(cursor, caixa["id_caixa"])
    movimentos = _totais_movimentacao(cursor, caixa["id_caixa"])

    vendas_dinheiro = formas.get("DINHEIRO", Decimal("0"))
    acrescimos = movimentos.get("ACRESCIMO", Decimal("0"))
    sangrias = movimentos.get("SANGRIA", Decimal("0"))
    saldo_esperado = calcular_saldo_esperado(
        caixa["valor_abertura"],
        vendas_dinheiro,
        acrescimos,
        sangrias,
    )

    total_vendas = sum(formas.values(), Decimal("0"))

    return {
        **caixa,
        "formas": formas,
        "total_vendas": total_vendas,
        "vendas_dinheiro": vendas_dinheiro,
        "acrescimos_caixa": acrescimos,
        "sangrias": sangrias,
        "saldo_esperado": saldo_esperado,
    }


def resumo_caixa_hoje():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT cd.*,
                   fa.nome AS funcionario_abertura,
                   ff.nome AS funcionario_fechamento
            FROM caixa_diario cd
            JOIN funcionario fa
              ON fa.id_funcionario = cd.id_funcionario_abertura
            LEFT JOIN funcionario ff
              ON ff.id_funcionario = cd.id_funcionario_fechamento
            WHERE cd.data_caixa = CURDATE()
            """
        )
        caixa = cursor.fetchone()
        if not caixa:
            return None
        return _resumo_com_cursor(cursor, caixa)


def listar_movimentacoes_hoje():
    caixa = obter_caixa_hoje()
    if not caixa:
        return []

    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT mc.id_movimentacao_caixa,
                   mc.data_movimentacao,
                   mc.tipo,
                   mc.valor,
                   mc.motivo,
                   f.nome AS funcionario
            FROM movimentacao_caixa mc
            JOIN funcionario f
              ON f.id_funcionario = mc.id_funcionario
            WHERE mc.id_caixa = %s
            ORDER BY mc.data_movimentacao DESC,
                     mc.id_movimentacao_caixa DESC
            """,
            (caixa["id_caixa"],),
        )
        return cursor.fetchall()


def listar_atividades_caixa_hoje():
    """
    Retorna, em uma única linha do tempo, todas as vendas e movimentações
    manuais do Caixa Diário de hoje.
    """
    caixa = obter_caixa_hoje()
    if not caixa:
        return []

    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT *
            FROM (
                SELECT
                    v.data_venda AS data_hora,
                    'VENDA' AS tipo,
                    v.id_venda AS referencia,
                    v.total AS valor,
                    CONCAT(
                        'Venda #',
                        v.id_venda,
                        CASE
                            WHEN c.nome IS NOT NULL AND TRIM(c.nome) <> ''
                                THEN CONCAT(' - ', c.nome)
                            ELSE ' - Consumidor não identificado'
                        END
                    ) AS descricao,
                    COALESCE(
                        GROUP_CONCAT(
                            DISTINCT pg.forma
                            ORDER BY pg.id_pagamento
                            SEPARATOR ' + '
                        ),
                        '-'
                    ) AS forma_pagamento,
                    f.nome AS funcionario,
                    v.status AS status
                FROM venda v
                LEFT JOIN cliente c
                  ON c.id_cliente = v.id_cliente
                JOIN funcionario f
                  ON f.id_funcionario = v.id_funcionario
                LEFT JOIN pagamento pg
                  ON pg.id_venda = v.id_venda
                WHERE v.id_caixa = %s
                GROUP BY
                    v.id_venda,
                    v.data_venda,
                    v.total,
                    c.nome,
                    f.nome,
                    v.status

                UNION ALL

                SELECT
                    mc.data_movimentacao AS data_hora,
                    mc.tipo AS tipo,
                    mc.id_movimentacao_caixa AS referencia,
                    mc.valor AS valor,
                    mc.motivo AS descricao,
                    '-' AS forma_pagamento,
                    f.nome AS funcionario,
                    'REGISTRADA' AS status
                FROM movimentacao_caixa mc
                JOIN funcionario f
                  ON f.id_funcionario = mc.id_funcionario
                WHERE mc.id_caixa = %s
            ) atividade
            ORDER BY data_hora DESC, referencia DESC
            """,
            (caixa["id_caixa"], caixa["id_caixa"]),
        )
        return cursor.fetchall()


def registrar_movimentacao(id_funcionario, tipo, valor, motivo):
    tipo = (tipo or "").strip().upper()
    if tipo not in {"SANGRIA", "ACRESCIMO"}:
        raise ValueError("Tipo de movimentação do caixa inválido.")

    valor = decimal_positivo(valor, "Valor")
    motivo = vazio_para_none(motivo)
    if not motivo:
        raise ValueError("Informe o motivo da movimentação.")

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()

            cursor.execute(
                """
                SELECT cd.*
                FROM caixa_diario cd
                WHERE cd.data_caixa = CURDATE()
                  AND cd.status = 'ABERTO'
                FOR UPDATE
                """
            )
            caixa = cursor.fetchone()
            if not caixa:
                raise ValueError("Abra o Caixa Diário antes de registrar movimentações.")

            if tipo == "SANGRIA":
                resumo = _resumo_com_cursor(cursor, caixa)
                if valor > resumo["saldo_esperado"]:
                    raise ValueError(
                        "A sangria não pode ser maior que o saldo em dinheiro esperado no caixa."
                    )

            cursor.execute(
                """
                INSERT INTO movimentacao_caixa
                    (id_caixa, id_funcionario, tipo, valor, motivo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    caixa["id_caixa"],
                    id_funcionario,
                    tipo,
                    valor,
                    motivo,
                ),
            )
            conexao.commit()
            return cursor.lastrowid
        except Exception:
            conexao.rollback()
            raise


def fechar_caixa(id_funcionario, valor_contado, observacao=None):
    valor_contado = decimal_nao_negativo(valor_contado, "Dinheiro contado")

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()

            cursor.execute(
                """
                SELECT cd.*
                FROM caixa_diario cd
                WHERE cd.data_caixa = CURDATE()
                  AND cd.status = 'ABERTO'
                FOR UPDATE
                """
            )
            caixa = cursor.fetchone()
            if not caixa:
                raise ValueError("Não existe Caixa Diário aberto para fechar.")

            resumo = _resumo_com_cursor(cursor, caixa)
            diferenca = calcular_diferenca(
                valor_contado,
                resumo["saldo_esperado"],
            )

            cursor.execute(
                """
                UPDATE caixa_diario
                SET status = 'FECHADO',
                    id_funcionario_fechamento = %s,
                    data_fechamento = NOW(),
                    valor_contado = %s,
                    saldo_esperado_fechamento = %s,
                    diferenca = %s,
                    observacao_fechamento = %s
                WHERE id_caixa = %s
                """,
                (
                    id_funcionario,
                    valor_contado,
                    resumo["saldo_esperado"],
                    diferenca,
                    vazio_para_none(observacao),
                    caixa["id_caixa"],
                ),
            )
            conexao.commit()
            return {
                "saldo_esperado": resumo["saldo_esperado"],
                "valor_contado": valor_contado,
                "diferenca": diferenca,
            }
        except Exception:
            conexao.rollback()
            raise
