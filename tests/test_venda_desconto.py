import unittest
from decimal import Decimal

from funcoes.calculos_venda import calcular_acrescimo, calcular_desconto, calcular_totais


class TestDescontos(unittest.TestCase):
    def test_sem_desconto(self):
        r = calcular_desconto("100", "NENHUM", "0")
        self.assertEqual(r["total"], Decimal("100.00"))
        self.assertEqual(r["desconto"], Decimal("0.00"))

    def test_desconto_valor(self):
        r = calcular_desconto("100", "VALOR", "12,50")
        self.assertEqual(r["desconto"], Decimal("12.50"))
        self.assertEqual(r["total"], Decimal("87.50"))

    def test_desconto_percentual(self):
        r = calcular_desconto("250", "PERCENTUAL", "10")
        self.assertEqual(r["desconto"], Decimal("25.00"))
        self.assertEqual(r["total"], Decimal("225.00"))
        self.assertEqual(r["percentual"], Decimal("10.00"))

    def test_desconto_valor_maior_que_total(self):
        with self.assertRaises(ValueError):
            calcular_desconto("20", "VALOR", "30")

    def test_percentual_maior_que_100(self):
        with self.assertRaises(ValueError):
            calcular_desconto("20", "PERCENTUAL", "101")


    def test_acrescimo_valor(self):
        r = calcular_acrescimo("90", "VALOR", "10")
        self.assertEqual(r["acrescimo"], Decimal("10.00"))
        self.assertEqual(r["total"], Decimal("100.00"))

    def test_acrescimo_percentual_sobre_valor_pos_desconto(self):
        r = calcular_totais(
            "100",
            desconto_tipo="PERCENTUAL",
            desconto_valor="10",
            acrescimo_tipo="PERCENTUAL",
            acrescimo_valor="10",
        )
        self.assertEqual(r["desconto"], Decimal("10.00"))
        self.assertEqual(r["base_acrescimo"], Decimal("90.00"))
        self.assertEqual(r["acrescimo"], Decimal("9.00"))
        self.assertEqual(r["total"], Decimal("99.00"))


if __name__ == "__main__":
    unittest.main()
