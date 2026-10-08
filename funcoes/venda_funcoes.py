from datetime import date, timedelta
from decimal import Decimal

from funcoes._db import cursor_banco
from funcoes.caixa_diario_funcoes import exigir_caixa_aberto
from funcoes.pagamento_funcoes import FORMAS_PAGAMENTO
from funcoes.calculos_venda import calcular_item_venda, calcular_totais, q2
from funcoes.utils import decimal_nao_negativo, decimal_positivo, vazio_para_none


def finalizar_venda(
    id_funcionario,
    itens,
    forma_pagamento,
    id_cliente=None,
    valor_recebido=None,
    parcelas=1,
    tipo_retirada="RETIRADA",
    endereco_entrega=None,
    data_prevista=None,
    observacao_entrega=None,
    observacao_venda=None,
    desconto_tipo="NENHUM",
    desconto_valor=0,
    acrescimo_tipo="NENHUM",
    acrescimo_valor=0,
):
    if not itens:
        raise ValueError("A venda precisa ter pelo menos um produto.")

    forma_pagamento = (forma_pagamento or "").upper()
    if forma_pagamento not in FORMAS_PAGAMENTO:
        raise ValueError("Forma de pagamento inválida.")

    tipo_retirada = (tipo_retirada or "RETIRADA").upper()
    if tipo_retirada not in {"RETIRADA", "ENTREGA"}:
        raise ValueError("Tipo de retirada inválido.")

    if forma_pagamento == "CREDIARIO":
        if not id_cliente:
            raise ValueError("Crediário exige um cliente identificado.")
        parcelas = int(parcelas)
        if parcelas not in (1, 2):
            raise ValueError("O crediário aceita somente 1 ou 2 parcelas.")
    else:
        parcelas = 1

    if tipo_retirada == "ENTREGA" and not (endereco_entrega or "").strip():
        raise ValueError("Informe o endereço para entrega.")

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()

            # Toda venda pertence ao Caixa Diário aberto daquele dia.
            caixa = exigir_caixa_aberto(cursor, for_update=True)
            id_caixa = caixa["id_caixa"]

            itens_processados = []
            subtotal = Decimal("0.00")

            for item in itens:
                id_produto = int(item["id_produto"])
                quantidade = decimal_positivo(item["quantidade"], "Quantidade")

                cursor.execute(
                    """
                    SELECT id_produto, nome, preco, quantidade_estoque, unidade_medida, ativo
                    FROM produto
                    WHERE id_produto=%s
                    FOR UPDATE
                    """,
                    (id_produto,),
                )
                produto = cursor.fetchone()

                if not produto or not produto["ativo"]:
                    raise ValueError(f"Produto {id_produto} indisponível.")

                estoque_atual = Decimal(produto["quantidade_estoque"])
                if quantidade > estoque_atual:
                    raise ValueError(
                        f"Estoque insuficiente para {produto['nome']}. "
                        f"Disponível: {estoque_atual}."
                    )

                preco_tabela = q2(produto["preco"])
                preco_informado = item.get("preco_unitario")

                if preco_informado in (None, ""):
                    preco_informado = preco_tabela

                calculo_item = calcular_item_venda(
                    preco_tabela,
                    preco_informado,
                    quantidade,
                )
                preco_venda = calculo_item["preco_venda"]
                item_subtotal = calculo_item["subtotal"]
                subtotal += item_subtotal

                itens_processados.append(
                    {
                        "id_produto": id_produto,
                        "nome": produto["nome"],
                        "quantidade": quantidade,
                        "unidade_medida": produto["unidade_medida"],
                        "preco_tabela": preco_tabela,
                        "preco": preco_venda,
                        "subtotal": item_subtotal,
                        "estoque_anterior": estoque_atual,
                    }
                )

            subtotal = q2(subtotal)
            totais = calcular_totais(
                subtotal,
                desconto_tipo,
                desconto_valor,
                acrescimo_tipo,
                acrescimo_valor,
            )
            total = totais["total"]

            if forma_pagamento == "DINHEIRO":
                recebido = q2(
                    decimal_nao_negativo(valor_recebido, "Valor recebido")
                )
                if recebido < total:
                    raise ValueError(
                        "Valor recebido é menor que o total da venda."
                    )
                troco = q2(recebido - total)
            else:
                recebido = None
                troco = Decimal("0.00")

            cursor.execute(
                """
                INSERT INTO venda
                    (
                        id_cliente,
                        id_funcionario,
                        id_caixa,
                        subtotal,
                        desconto_tipo,
                        desconto_valor,
                        desconto_percentual,
                        acrescimo_tipo,
                        acrescimo_valor,
                        acrescimo_percentual,
                        total,
                        observacao,
                        status,
                        tipo_retirada
                    )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    'FINALIZADA', %s
                )
                """,
                (
                    id_cliente or None,
                    id_funcionario,
                    id_caixa,
                    subtotal,
                    totais["desconto_tipo"],
                    totais["desconto"],
                    totais["desconto_percentual"],
                    totais["acrescimo_tipo"],
                    totais["acrescimo"],
                    totais["acrescimo_percentual"],
                    total,
                    vazio_para_none(observacao_venda),
                    tipo_retirada,
                ),
            )
            id_venda = cursor.lastrowid

            for item in itens_processados:
                cursor.execute(
                    """
                    INSERT INTO item_venda
                        (
                            id_venda,
                            id_produto,
                            quantidade,
                            unidade_medida,
                            preco_tabela,
                            preco_unitario,
                            subtotal
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_venda,
                        item["id_produto"],
                        item["quantidade"],
                        item["unidade_medida"],
                        item["preco_tabela"],
                        item["preco"],
                        item["subtotal"],
                    ),
                )

                novo_estoque = (
                    item["estoque_anterior"] - item["quantidade"]
                )
                cursor.execute(
                    """
                    UPDATE produto
                    SET quantidade_estoque=%s
                    WHERE id_produto=%s
                    """,
                    (novo_estoque, item["id_produto"]),
                )
                cursor.execute(
                    """
                    INSERT INTO movimentacao_estoque
                        (
                            id_produto,
                            id_funcionario,
                            tipo,
                            quantidade,
                            quantidade_anterior,
                            quantidade_nova,
                            motivo
                        )
                    VALUES (%s, %s, 'SAIDA', %s, %s, %s, %s)
                    """,
                    (
                        item["id_produto"],
                        id_funcionario,
                        item["quantidade"],
                        item["estoque_anterior"],
                        novo_estoque,
                        f"Venda #{id_venda}",
                    ),
                )

            cursor.execute(
                """
                INSERT INTO pagamento
                    (
                        id_venda,
                        forma,
                        valor,
                        valor_recebido,
                        troco,
                        parcelas
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    id_venda,
                    forma_pagamento,
                    total,
                    recebido,
                    troco,
                    parcelas,
                ),
            )
            id_pagamento = cursor.lastrowid

            if forma_pagamento == "CREDIARIO":
                valor_base = q2(total / parcelas)
                soma = Decimal("0.00")
                hoje = date.today()

                for numero in range(1, parcelas + 1):
                    if numero == parcelas:
                        valor_parcela = q2(total - soma)
                    else:
                        valor_parcela = valor_base
                        soma += valor_parcela

                    vencimento = hoje + timedelta(days=30 * numero)
                    cursor.execute(
                        """
                        INSERT INTO parcela
                            (
                                id_pagamento,
                                id_cliente,
                                numero,
                                valor,
                                data_vencimento,
                                status
                            )
                        VALUES (%s, %s, %s, %s, %s, 'PENDENTE')
                        """,
                        (
                            id_pagamento,
                            id_cliente,
                            numero,
                            valor_parcela,
                            vencimento,
                        ),
                    )

            if tipo_retirada == "ENTREGA":
                cursor.execute(
                    """
                    INSERT INTO entrega
                        (
                            id_venda,
                            endereco,
                            data_prevista,
                            status,
                            observacao
                        )
                    VALUES (%s, %s, %s, 'AGUARDANDO', %s)
                    """,
                    (
                        id_venda,
                        endereco_entrega.strip(),
                        data_prevista or None,
                        vazio_para_none(observacao_entrega),
                    ),
                )

            conexao.commit()
            return {
                "id_venda": id_venda,
                "id_caixa": id_caixa,
                "subtotal": subtotal,
                "desconto": totais["desconto"],
                "acrescimo": totais["acrescimo"],
                "total": total,
                "troco": troco,
                "forma_pagamento": forma_pagamento,
            }

        except Exception:
            conexao.rollback()
            raise


def obter_venda_completa(id_venda):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT v.*, c.nome AS cliente, f.nome AS funcionario
            FROM venda v
            LEFT JOIN cliente c
              ON c.id_cliente = v.id_cliente
            JOIN funcionario f
              ON f.id_funcionario = v.id_funcionario
            WHERE v.id_venda=%s
            """,
            (id_venda,),
        )
        venda = cursor.fetchone()
        if not venda:
            return None

        cursor.execute(
            """
            SELECT i.*, p.nome AS produto
            FROM item_venda i
            JOIN produto p
              ON p.id_produto = i.id_produto
            WHERE i.id_venda=%s
            ORDER BY i.id_item_venda
            """,
            (id_venda,),
        )
        venda["itens"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT *
            FROM pagamento
            WHERE id_venda=%s
            ORDER BY id_pagamento
            """,
            (id_venda,),
        )
        venda["pagamentos"] = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM entrega WHERE id_venda=%s",
            (id_venda,),
        )
        venda["entrega"] = cursor.fetchone()
        return venda
