"""Pagamentos parciais, nota residual e atualização de saldos (sem MySQL real)."""
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

if 'conexao' not in sys.modules:
    conexao = types.ModuleType('conexao')
    conexao.conectar_banco = lambda: None
    sys.modules['conexao'] = conexao

from funcoes import crediario_funcoes as credit


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
    def start_transaction(self):
        pass
    def commit(self):
        self.commits += 1
    def rollback(self):
        self.rollbacks += 1


class FakeCursor:
    def __init__(self, parcelas):
        self.parcelas = parcelas
        self.statements = []
        self.lastrowid = 20
        self.rowcount = 1
    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        self.lastrowid += 1
        self.rowcount = 1
    def fetchall(self):
        return self.parcelas


class TestCrediarioParcial(unittest.TestCase):
    def setUp(self):
        self.hoje = date.today()
        self.parcela = {
            'id_parcela': 4, 'id_cliente': 2, 'id_venda': 18,
            'numero': 1, 'valor': Decimal('300.00'), 'valor_pago_principal': 0,
            'juros_pendente': 0, 'juros_ultimo_calculo_ate': None,
            'data_vencimento': self.hoje - timedelta(days=60), 'status': 'ATRASADA',
        }

    def test_juros_nao_duplicam_apos_recebimento_parcial(self):
        aloc = credit.distribuir_pagamento_parcial([self.parcela], '106.00', self.hoje)[0]
        self.assertEqual(aloc['juros_pagos'], Decimal('6.00'))
        self.assertEqual(aloc['principal_pago'], Decimal('100.00'))
        self.assertEqual(aloc['saldo_principal'], Decimal('200.00'))
        nova = {**self.parcela,
                'valor_pago_principal': Decimal('100.00'),
                'juros_pendente': aloc['juros_restantes'],
                'juros_ultimo_calculo_ate': self.hoje}
        hoje = credit.calcular_parcela_em_aberto(nova, self.hoje)
        self.assertEqual(hoje['total'], Decimal('200.00'))
        futuro = credit.calcular_parcela_em_aberto(nova, self.hoje + timedelta(days=30))
        self.assertEqual(futuro['juros'], Decimal('2.00'))
        self.assertEqual(futuro['total'], Decimal('202.00'))

    def test_pagamento_menor_que_juros_mantem_juros_pendentes(self):
        aloc = credit.distribuir_pagamento_parcial([self.parcela], '2.00', self.hoje)[0]
        self.assertEqual(aloc['juros_pagos'], Decimal('2.00'))
        self.assertEqual(aloc['principal_pago'], Decimal('0.00'))
        self.assertEqual(aloc['juros_restantes'], Decimal('4.00'))

    def test_rejeita_zero_ou_quitacao_integral_como_parcial(self):
        for valor in ('0', '306', '400'):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                credit.distribuir_pagamento_parcial([self.parcela], valor, self.hoje)

    def test_fila_prioriza_vencimento_antigo_e_distribui_cada_centavo(self):
        outra = {**self.parcela, 'id_parcela': 5, 'id_venda': 19,
                 'data_vencimento': self.hoje, 'valor': Decimal('100.00')}
        aloc = credit.distribuir_pagamento_parcial([outra, self.parcela], '350.00', self.hoje)
        self.assertEqual(aloc[0]['id_parcela'], 4)
        self.assertEqual(aloc[0]['principal_pago'], Decimal('300.00'))
        self.assertEqual(aloc[1]['principal_pago'], Decimal('44.00'))
        self.assertEqual(sum((a['principal_pago'] + a['juros_pagos'] for a in aloc), Decimal('0')),
                         Decimal('350.00'))

    def test_registra_nota_e_uma_entrada_caixa_dinheiro(self):
        conn, cur = FakeConn(), FakeCursor([self.parcela])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        with patch.object(credit, 'cursor_banco', fake_cursor), patch.object(
            credit, 'exigir_caixa_aberto', return_value={'id_caixa': 10}
        ):
            res = credit.receber_parcial_crediario(
                2, [4], 1, 'DINHEIRO', '106.00', valor_recebido='120')
        self.assertIsInstance(res, int)
        self.assertEqual(conn.commits, 1)
        self.assertEqual(conn.rollbacks, 0)
        stmts = [sql for sql, _ in cur.statements]
        self.assertEqual(sum('INSERT INTO movimentacao_caixa' in sql for sql in stmts), 1)
        self.assertEqual(sum('INSERT INTO crediario_nota_saldo\n' in sql for sql in stmts), 1)
        self.assertEqual(sum('UPDATE parcela' in sql for sql in stmts), 1)
        self.assertEqual(sum('INSERT INTO crediario_recebimento_parcial_item' in sql for sql in stmts), 1)

    def test_seguranca_nao_da_baixa_em_parcela_de_outro_cliente(self):
        conn, cur = FakeConn(), FakeCursor([dict(self.parcela, id_cliente=5)])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        with patch.object(credit, 'cursor_banco', fake_cursor), patch.object(
            credit, 'exigir_caixa_aberto', return_value={'id_caixa': 10}
        ), self.assertRaises(ValueError):
            credit.receber_parcial_crediario(2, [4], 1, 'PIX', '50')
        self.assertEqual(conn.commits, 0)
        self.assertEqual(conn.rollbacks, 1)


if __name__ == '__main__':
    unittest.main()
