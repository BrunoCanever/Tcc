from funcoes._db import cursor_banco

FORMAS_PAGAMENTO = [
    "DINHEIRO",
    "PIX",
    "CARTAO_CREDITO",
    "CARTAO_DEBITO",
    "CREDIARIO",
]


def listar_pagamentos_venda(id_venda):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            "SELECT * FROM pagamento WHERE id_venda=%s ORDER BY id_pagamento",
            (id_venda,),
        )
        return cursor.fetchall()
