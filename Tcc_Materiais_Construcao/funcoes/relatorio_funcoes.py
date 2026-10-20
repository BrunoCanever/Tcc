from funcoes._db import cursor_banco


def vendas_por_periodo(data_inicio, data_fim):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT v.id_venda, v.data_venda,
                   COALESCE(c.nome, 'Não identificado') AS cliente,
                   f.nome AS funcionario, v.total, v.tipo_retirada
            FROM venda v
            LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
            JOIN funcionario f ON f.id_funcionario = v.id_funcionario
            WHERE DATE(v.data_venda) BETWEEN %s AND %s
              AND v.status='FINALIZADA'
            ORDER BY v.data_venda DESC
            """,
            (data_inicio, data_fim),
        )
        return cursor.fetchall()


def produtos_mais_vendidos(limite=20):
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT p.nome, p.unidade_medida,
                   SUM(i.quantidade) AS quantidade_vendida,
                   SUM(i.subtotal) AS faturamento
            FROM item_venda i
            JOIN venda v ON v.id_venda = i.id_venda
            JOIN produto p ON p.id_produto = i.id_produto
            WHERE v.status='FINALIZADA'
            GROUP BY p.id_produto, p.nome, p.unidade_medida
            ORDER BY quantidade_vendida DESC
            LIMIT %s
            """,
            (limite,),
        )
        return cursor.fetchall()


def estoque_atual():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT p.id_produto, p.nome, c.nome AS categoria,
                   p.quantidade_estoque, p.estoque_minimo,
                   p.unidade_medida, p.tipo_localizacao, p.corredor,
                   p.prateleira, p.descricao_localizacao
            FROM produto p
            JOIN categoria c ON c.id_categoria = p.id_categoria
            WHERE p.ativo=TRUE
            ORDER BY p.nome
            """
        )
        return cursor.fetchall()


def estoque_baixo():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT nome, quantidade_estoque, estoque_minimo, unidade_medida
            FROM produto
            WHERE ativo=TRUE AND quantidade_estoque <= estoque_minimo
            ORDER BY quantidade_estoque
            """
        )
        return cursor.fetchall()


def clientes_crediario_pendente():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT c.id_cliente, c.nome,
                   COUNT(p.id_parcela) AS parcelas_abertas,
                   SUM(p.valor) AS valor_aberto
            FROM parcela p
            JOIN cliente c ON c.id_cliente = p.id_cliente
            WHERE p.status IN ('PENDENTE', 'ATRASADA')
            GROUP BY c.id_cliente, c.nome
            ORDER BY valor_aberto DESC
            """
        )
        return cursor.fetchall()


def entregas_pendentes():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT e.id_entrega, e.id_venda,
                   COALESCE(c.nome, 'Não identificado') AS cliente,
                   e.endereco, e.data_prevista, e.status
            FROM entrega e
            JOIN venda v ON v.id_venda = e.id_venda
            LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
            WHERE e.status IN ('AGUARDANDO', 'EM ROTA')
            ORDER BY e.data_prevista
            """
        )
        return cursor.fetchall()
