"""Regras de juros, descontos e baixa transacional (sem MySQL real)."""
import importlib
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

# Permite testar as regras sem depender de um MySQL instalado no ambiente.
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
    def close(self):
        pass


class FakeCursor:
    def __init__(self, parcelas):
        self.parcelas = parcelas
        self.statements = []
        self.lastrowid = 23
        self.rowcount = 1
        self.last = ''
    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        self.last = sql
        self.rowcount = 1
    def fetchone(self):
        if 'FROM caixa_diario' in self.last:
            return {'id_caixa': 11, 'status': 'ABERTO'}
        return None
    def fetchall(self):
        return self.parcelas
    def close(self):
        pass


class TestCrediarioAvancado(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 29)
        self.parcela = {
            'id_parcela': 1, 'id_cliente': 3, 'numero': 1,
            'id_venda': 7, 'valor': Decimal('300.00'),
            'data_vencimento': self.today - timedelta(days=60),
            'status': 'ATRASADA',
        }

    def test_juros_simples_1_porcento_mes(self):
        dias, juros = credit.juros_simples('300', self.parcela['data_vencimento'], self.today)
        self.assertEqual((dias, juros), (60, Decimal('6.00')))

    def test_nao_cobrar_antes_vencimento(self):
        dias, juros = credit.juros_simples('100', self.today + timedelta(days=7), self.today)
        self.assertEqual((dias, juros), (0, Decimal('0.00')))

    def test_desconto_abate_juros_e_principal(self):
        total = credit.calcular_totais_baixa([self.parcela], '10', '2', self.today)
        self.assertEqual(total['principal'], Decimal('300.00'))
        self.assertEqual(total['juros'], Decimal('6.00'))
        self.assertEqual(total['total'], Decimal('298.00'))

    def test_desconto_maior_que_divida_proibido(self):
        with self.assertRaises(ValueError):
            credit.calcular_totais_baixa([self.parcela], '500', '0', self.today)

    def test_valor_nao_finito_invalido(self):
        for val in ('NaN', 'Infinity', '-10', 'abc'):
            with self.subTest(val=val), self.assertRaises(ValueError):
                credit.dinheiro(val)

    def test_duplicatas_de_ids_sao_eliminadas(self):
        conn, cur = FakeConn(), FakeCursor([self.parcela])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        # Teste de parcela quitada, nenhum commit.
        cur.parcelas = [dict(self.parcela, status='PAGA')]
        with patch.object(credit, 'cursor_banco', fake_cursor), self.assertRaises(ValueError):
            credit.liquidar_crediario(3, [1, 1], 2, 'PIX', '306.00')
        self.assertEqual(conn.commits, 0)
        self.assertEqual(conn.rollbacks, 1)

    def test_nao_baixa_outro_cliente(self):
        conn, cur = FakeConn(), FakeCursor([dict(self.parcela, id_cliente=5)])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        with patch.object(credit, 'cursor_banco', fake_cursor), self.assertRaises(ValueError):
            credit.liquidar_crediario(3, [1], 2, 'PIX', '306.00')
        self.assertEqual(conn.commits, 0)

    def test_subpagamento_exige_desconto_explicito(self):
        conn, cur = FakeConn(), FakeCursor([self.parcela])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        # Não usa juros estáticos: baixa real usa date.today() atual.
        valor = credit.calcular_totais_baixa([self.parcela])['total']
        with patch.object(credit, 'cursor_banco', fake_cursor), self.assertRaises(ValueError):
            credit.liquidar_crediario(3, [1], 2, 'PIX', str(valor - 1))
        self.assertEqual(conn.commits, 0)
        self.assertEqual(conn.rollbacks, 1)

    def test_quitacao_em_dinheiro_lanca_caixa_uma_vez(self):
        conn, cur = FakeConn(), FakeCursor([self.parcela])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        total = credit.calcular_totais_baixa([self.parcela])['total']
        with patch.object(credit, 'cursor_banco', fake_cursor):
            receipt = credit.liquidar_crediario(3, [1], 2, 'DINHEIRO',
                                                str(total), valor_recebido=str(total+20))
        self.assertEqual(receipt, 23)
        self.assertEqual(conn.commits, 1)
        self.assertEqual(sum('INSERT INTO movimentacao_caixa' in sql for sql, _ in cur.statements), 1)
        self.assertEqual(sum('UPDATE parcela' in sql for sql, _ in cur.statements), 1)

    def test_pix_nao_soma_caixa_fisico(self):
        conn, cur = FakeConn(), FakeCursor([self.parcela])
        @contextmanager
        def fake_cursor():
            yield conn, cur
        total = credit.calcular_totais_baixa([self.parcela])['total']
        with patch.object(credit, 'cursor_banco', fake_cursor):
            credit.liquidar_crediario(3, [1], 2, 'PIX', str(total))
        self.assertFalse(any('INSERT INTO movimentacao_caixa' in sql for sql, _ in cur.statements))

    def test_id_cliente_forma_e_lista_validos(self):
        with self.assertRaises(ValueError):
            credit.liquidar_crediario(3, [], 2, 'PIX', 20)
        with self.assertRaises(ValueError):
            credit.liquidar_crediario(3, [1], 2, 'CREDIARIO', 20)


if __name__ == '__main__':
    unittest.main()
