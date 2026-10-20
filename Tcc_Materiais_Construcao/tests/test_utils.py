import unittest
from decimal import Decimal
from funcoes.utils import decimal_nao_negativo, decimal_positivo, somente_digitos


class TestUtils(unittest.TestCase):
    def test_decimal_virgula(self):
        self.assertEqual(decimal_nao_negativo("12,50", "Preço"), Decimal("12.50"))

    def test_decimal_negativo(self):
        with self.assertRaises(ValueError):
            decimal_nao_negativo("-1", "Preço")

    def test_decimal_positivo_zero(self):
        with self.assertRaises(ValueError):
            decimal_positivo("0", "Quantidade")

    def test_somente_digitos(self):
        self.assertEqual(somente_digitos("123.456.789-00"), "12345678900")


if __name__ == "__main__":
    unittest.main()
