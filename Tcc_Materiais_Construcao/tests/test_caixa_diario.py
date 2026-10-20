import unittest
from decimal import Decimal

from funcoes.calculos_caixa import (
    calcular_diferenca,
    calcular_saldo_esperado,
)


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


if __name__ == "__main__":
    unittest.main()
