from datetime import date
from funcoes._db import cursor_banco


def atualizar_atrasadas():
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            UPDATE parcela
            SET status='ATRASADA'
            WHERE status='PENDENTE' AND data_vencimento < CURDATE()
            """
        )
        conexao.commit()


def listar_parcelas(status=None, termo_cliente=None):
    atualizar_atrasadas()
    filtros = []
    params = []

    if status:
        filtros.append("p.status=%s")
        params.append(status)
    if termo_cliente:
        filtros.append("(c.nome LIKE %s OR c.cpf_cnpj LIKE %s)")
        termo = f"%{termo_cliente.strip()}%"
        params.extend([termo, termo])

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    with cursor_banco() as (_, cursor):
        cursor.execute(
            f"""
            SELECT p.id_parcela, p.numero, p.valor, p.data_vencimento,
                   p.data_pagamento, p.status, c.id_cliente,
                   c.nome AS cliente, v.id_venda
            FROM parcela p
            JOIN cliente c ON c.id_cliente = p.id_cliente
            JOIN pagamento pg ON pg.id_pagamento = p.id_pagamento
            JOIN venda v ON v.id_venda = pg.id_venda
            {where}
            ORDER BY
                FIELD(p.status, 'ATRASADA', 'PENDENTE', 'PAGA'),
                p.data_vencimento
            """,
            tuple(params),
        )
        return cursor.fetchall()


def dar_baixa_parcela(id_parcela):
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            UPDATE parcela
            SET status='PAGA', data_pagamento=%s
            WHERE id_parcela=%s AND status <> 'PAGA'
            """,
            (date.today(), id_parcela),
        )
        conexao.commit()
        return cursor.rowcount > 0
