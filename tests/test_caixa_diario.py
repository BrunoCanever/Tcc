import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from decimal import Decimal

from funcoes.calculos_caixa import (
    calcular_diferenca,
    calcular_saldo_esperado,
)

# Permite testar a regra do Caixa Diário mesmo em um ambiente de CI sem o
# mysql-connector instalado. A conexão real é substituída nos testes abaixo.
if "mysql.connector" not in sys.modules:
    mysql_mod = types.ModuleType("mysql")
    connector_mod = types.ModuleType("mysql.connector")
    connector_mod.Error = Exception
    connector_mod.connect = lambda *args, **kwargs: None
    mysql_mod.connector = connector_mod
    sys.modules.setdefault("mysql", mysql_mod)
    sys.modules.setdefault("mysql.connector", connector_mod)

from funcoes.caixa_diario_funcoes import abrir_caixa


class TestCaixaDiario(unittest.TestCase):
    def test_saldo_esperado(self):
        saldo = calcular_saldo_esperado(
            valor_abertura="100",
            vendas_dinheiro="350",
            acrescimos="50",
            sangrias="80",
        )
        self.assertEqual(saldo, Decimal("420.00"))

    def test_diferenca_sobra(self):
        diferenca = calcular_diferenca("425", "420")
        self.assertEqual(diferenca, Decimal("5.00"))

    def test_diferenca_falta(self):
        diferenca = calcular_diferenca("410", "420")
        self.assertEqual(diferenca, Decimal("-10.00"))


class _ConexaoFake:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.transacoes = 0

    def start_transaction(self):
        self.transacoes += 1

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _CursorFake:
    def __init__(self, estado):
        self.estado = estado
        self.lastrowid = 99
        self.comandos = []

    def execute(self, sql, params=None):
        normalizado = " ".join(sql.split())
        self.comandos.append((normalizado, params))
        if normalizado.startswith("UPDATE caixa_diario"):
            self.estado["status"] = "ABERTO"

    def fetchone(self):
        if self.estado.get("existe", True):
            return {
                "id_caixa": self.estado["id_caixa"],
                "status": self.estado["status"],
            }
        return None


class TestReaberturaCaixa(unittest.TestCase):
    def _contexto(self, estado):
        conexao = _ConexaoFake()
        cursor = _CursorFake(estado)

        @contextmanager
        def falso_cursor_banco():
            yield conexao, cursor

        return conexao, cursor, falso_cursor_banco

    def test_caixa_fechado_pode_ser_reaberto_sem_criar_novo_registro(self):
        estado = {"existe": True, "id_caixa": 7, "status": "FECHADO"}
        conexao, cursor, falso = self._contexto(estado)

        with patch(
            "funcoes.caixa_diario_funcoes.cursor_banco",
            falso,
        ):
            id_caixa = abrir_caixa(3, "150")

        self.assertEqual(id_caixa, 7)
        self.assertEqual(estado["status"], "ABERTO")
        self.assertEqual(conexao.commits, 1)
        self.assertTrue(
            any(
                comando.startswith("UPDATE caixa_diario")
                for comando, _ in cursor.comandos
            )
        )
        self.assertFalse(
            any(
                comando.startswith("INSERT INTO caixa_diario")
                for comando, _ in cursor.comandos
            )
        )

    def test_caixa_pode_ser_reaberto_mais_de_uma_vez_no_mesmo_dia(self):
        estado = {"existe": True, "id_caixa": 12, "status": "FECHADO"}

        for _ in range(3):
            conexao, _, falso = self._contexto(estado)
            with patch(
                "funcoes.caixa_diario_funcoes.cursor_banco",
                falso,
            ):
                self.assertEqual(abrir_caixa(4, "80"), 12)
            self.assertEqual(estado["status"], "ABERTO")
            self.assertEqual(conexao.commits, 1)

            # Simula um novo fechamento antes da próxima reabertura.
            estado["status"] = "FECHADO"

    def test_caixa_ja_aberto_continua_bloqueando_abertura_duplicada(self):
        estado = {"existe": True, "id_caixa": 5, "status": "ABERTO"}
        conexao, _, falso = self._contexto(estado)

        with patch(
            "funcoes.caixa_diario_funcoes.cursor_banco",
            falso,
        ):
            with self.assertRaisesRegex(ValueError, "já está aberto"):
                abrir_caixa(2, "100")

        self.assertEqual(conexao.rollbacks, 1)


if __name__ == "__main__":
    unittest.main()
