"""Cadastros e compras fictícios, idempotentes, exclusivos para demonstração."""
from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256

from funcoes._db import cursor_banco

MARCADOR = '[DEMO_CRED_V1:'
CLIENTES = [
    'Ana Souza (DEMO)', 'Carlos Lima (DEMO)', 'Fernanda Rocha (DEMO)',
    'Marcos Pereira (DEMO)', 'Juliana Alves (DEMO)', 'Rafael Martins (DEMO)',
    'Beatriz Costa (DEMO)', 'Lucas Ribeiro (DEMO)', 'Patricia Gomes (DEMO)',
    'Eduardo Santos (DEMO)', 'Mariana Oliveira (DEMO)', 'Gabriel Ferreira (DEMO)',
]
FORNECEDORES = [
    'Depósito Serra Azul (DEMO)', 'Madeireira Horizonte (DEMO)',
    'Tintas Vale Verde (DEMO)', 'Elétrica Bons Fios (DEMO)',
    'Hidráulica Modelo (DEMO)', 'Argamassas Exemplo (DEMO)',
    'Ferragens do Sul (DEMO)', 'Cerâmicas Amostra (DEMO)',
]


def popular_crediario_demo():
    """Preserva os dados reais e não duplica registros a cada instalação.

    As vendas simuladas são vinculadas a caixas históricos FECHADOS; não afetam
    o caixa aberto de hoje. Produtos vendidos têm o estoque baixado com histórico.
    """
    resultado = {'clientes': 0, 'fornecedores': 0, 'funcionarios': 0, 'vendas': 0}
    with cursor_banco() as (conexao, cur):
        try:
            conexao.start_transaction()
            cur.execute("SELECT id_funcionario FROM funcionario WHERE login='q' LIMIT 1")
            admin = cur.fetchone()
            if not admin:
                raise ValueError('Cadastre o administrador antes de carregar a demonstração.')
            id_admin = admin['id_funcionario']
            cur.execute('SELECT id_cargo FROM cargo WHERE nome=%s', ('Vendedor',))
            cargo = cur.fetchone()
            cargo = cargo['id_cargo'] if cargo else None
            if cargo:
                for i, nome in enumerate(('Vendedor Exemplo', 'Estoquista Exemplo', 'Auxiliar Exemplo'), 1):
                    login = f'demo_cadastro_{i}'
                    cur.execute('SELECT id_funcionario FROM funcionario WHERE login=%s', (login,))
                    if not cur.fetchone():
                        cur.execute('''INSERT INTO funcionario
                            (nome,login,senha_hash,id_cargo,ativo) VALUES (%s,%s,%s,%s,FALSE)''',
                            (nome, login, sha256(f'demo-bloqueado-{i}'.encode()).hexdigest(), cargo))
                        resultado['funcionarios'] += 1
            clientes = []
            for i, nome in enumerate(CLIENTES):
                cur.execute('SELECT id_cliente FROM cliente WHERE nome=%s LIMIT 1', (nome,))
                reg = cur.fetchone()
                if not reg:
                    cur.execute('''INSERT INTO cliente (nome, telefone, cidade, uf)
                                   VALUES (%s,%s,%s,%s)''',
                                (nome, f'(48) 99990-{i:04d}', 'Cidade Exemplo', 'SC'))
                    cid = cur.lastrowid
                    resultado['clientes'] += 1
                else:
                    cid = reg['id_cliente']
                clientes.append(cid)
            for nome in FORNECEDORES:
                cur.execute('SELECT id_fornecedor FROM fornecedor WHERE razao_social=%s LIMIT 1', (nome,))
                if not cur.fetchone():
                    cur.execute('''INSERT INTO fornecedor (razao_social,nome_fantasia)
                                   VALUES (%s,%s)''', (nome, nome))
                    resultado['fornecedores'] += 1
            cur.execute("""SELECT id_produto,nome,preco,quantidade_estoque,unidade_medida
                           FROM produto WHERE ativo=TRUE AND preco>0
                             AND descricao LIKE '[DEMO_CAT_V4]%'
                             AND quantidade_estoque>=20 ORDER BY id_produto LIMIT 45""")
            produtos = cur.fetchall()
            if not produtos:
                conexao.commit()
                return resultado
            hoje = date.today()
            offsets = (92, 78, 65, 47, 34, 18)
            caixas = {}
            for dias in offsets:
                dia = hoje - timedelta(days=dias)
                cur.execute('SELECT id_caixa FROM caixa_diario WHERE data_caixa=%s', (dia,))
                registro = cur.fetchone()
                if registro:
                    caixas[dias] = registro['id_caixa']
                else:
                    cur.execute("""INSERT INTO caixa_diario
                        (data_caixa,id_funcionario_abertura,valor_abertura,status,
                         id_funcionario_fechamento,data_fechamento,valor_contado,saldo_esperado_fechamento,diferenca)
                         VALUES (%s,%s,0,'FECHADO',%s,%s,0,0,0)""",
                        (dia, id_admin, id_admin, dia))
                    caixas[dias] = cur.lastrowid
            # Dois ou três crediários por cliente, com parcelas vencidas e futuras.
            for i, id_cliente in enumerate(clientes):
                for n in range(3 if i < 6 else 2):
                    tag = f'{MARCADOR}{i}:{n}]'
                    cur.execute('SELECT id_venda FROM venda WHERE observacao=%s', (tag,))
                    if cur.fetchone():
                        continue
                    dias = offsets[(i + n) % len(offsets)]
                    dia = hoje - timedelta(days=dias)
                    produto = produtos[(i * 3 + n * 4) % len(produtos)]
                    qtd = Decimal('2') if n == 1 else Decimal('1')
                    cur.execute('''SELECT quantidade_estoque FROM produto WHERE id_produto=%s FOR UPDATE''',
                                (produto['id_produto'],))
                    estoque = Decimal(str(cur.fetchone()['quantidade_estoque']))
                    if estoque < qtd:
                        continue
                    preco = Decimal(str(produto['preco']))
                    total = (qtd * preco).quantize(Decimal('.01'))
                    cur.execute('''INSERT INTO venda
                        (id_cliente,id_funcionario,id_caixa,subtotal,total,observacao,status,data_venda)
                        VALUES (%s,%s,%s,%s,%s,%s,'FINALIZADA',%s)''',
                        (id_cliente,id_admin,caixas[dias],total,total,tag, dia))
                    venda = cur.lastrowid
                    cur.execute('''INSERT INTO item_venda
                        (id_venda,id_produto,quantidade,unidade_medida,preco_tabela,preco_unitario,subtotal)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                        (venda,produto['id_produto'],qtd,produto['unidade_medida'],preco,preco,total))
                    cur.execute('UPDATE produto SET quantidade_estoque=quantidade_estoque-%s WHERE id_produto=%s',
                                (qtd,produto['id_produto']))
                    cur.execute('''INSERT INTO movimentacao_estoque
                        (id_produto,id_funcionario,tipo,quantidade,quantidade_anterior,quantidade_nova,motivo)
                        VALUES (%s,%s,'SAIDA',%s,%s,%s,%s)''',
                        (produto['id_produto'],id_admin,qtd,estoque,estoque-qtd,f'Venda demonstrativa #{venda}'))
                    partes = 2 if n == 1 else 1
                    cur.execute('''INSERT INTO pagamento
                        (id_venda,forma,valor,parcelas) VALUES (%s,'CREDIARIO',%s,%s)''',
                        (venda,total,partes))
                    pag = cur.lastrowid
                    parcial = (total / partes).quantize(Decimal('.01'))
                    for numero in range(1, partes+1):
                        valor = total - parcial if numero == 2 else parcial
                        vencimento = dia + timedelta(days=30*numero)
                        cur.execute('''INSERT INTO parcela
                            (id_pagamento,id_cliente,numero,valor,data_vencimento,status)
                            VALUES (%s,%s,%s,%s,%s,%s)''',
                            (pag,id_cliente,numero,valor,vencimento,
                             'ATRASADA' if vencimento < hoje else 'PENDENTE'))
                    resultado['vendas'] += 1
            conexao.commit()
            return resultado
        except Exception:
            conexao.rollback()
            raise


if __name__ == '__main__':
    print(popular_crediario_demo())
