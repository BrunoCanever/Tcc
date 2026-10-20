from funcoes._db import cursor_banco


STATUS_ENTREGA = ["AGUARDANDO", "EM ROTA", "ENTREGUE", "CANCELADA"]


def listar_entregas(status=None):
    where = "WHERE e.status=%s" if status else ""
    params = (status,) if status else ()
    with cursor_banco() as (_, cursor):
        cursor.execute(
            f"""
            SELECT e.id_entrega, e.id_venda, e.endereco, e.data_prevista,
                   e.status, e.observacao, e.data_entrega,
                   COALESCE(c.nome, 'Consumidor não identificado') AS cliente
            FROM entrega e
            JOIN venda v ON v.id_venda = e.id_venda
            LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
            {where}
            ORDER BY
                FIELD(e.status, 'AGUARDANDO', 'EM ROTA', 'ENTREGUE', 'CANCELADA'),
                e.data_prevista
            """,
            params,
        )
        return cursor.fetchall()


def atualizar_status_entrega(id_entrega, novo_status):
    novo_status = (novo_status or "").upper()
    if novo_status not in STATUS_ENTREGA:
        raise ValueError("Status de entrega inválido.")

    with cursor_banco() as (conexao, cursor):
        if novo_status == "ENTREGUE":
            cursor.execute(
                """
                UPDATE entrega
                SET status=%s, data_entrega=NOW()
                WHERE id_entrega=%s
                """,
                (novo_status, id_entrega),
            )
        else:
            cursor.execute(
                """
                UPDATE entrega
                SET status=%s,
                    data_entrega=CASE WHEN %s='ENTREGUE' THEN data_entrega ELSE NULL END
                WHERE id_entrega=%s
                """,
                (novo_status, novo_status, id_entrega),
            )
        conexao.commit()
        return cursor.rowcount > 0
