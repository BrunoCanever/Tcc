import unittest
from decimal import Decimal

from funcoes.calculos_venda import calcular_item_venda, calcular_totais


class TestPrecoItemVenda(unittest.TestCase):
    def test_preco_reduzido(self):
        item = calcular_item_venda("100", "90", "2")
        self.assertEqual(item["preco_tabela"], Decimal("100.00"))
        self.assertEqual(item["preco_venda"], Decimal("90.00"))
        self.assertEqual(item["diferenca_unitaria"], Decimal("-10.00"))
        self.assertEqual(item["subtotal"], Decimal("180.00"))

    def test_preco_aumentado(self):
        item = calcular_item_venda("100", "115", "3")
        self.assertEqual(item["diferenca_unitaria"], Decimal("15.00"))
        self.assertEqual(item["subtotal_tabela"], Decimal("300.00"))
        self.assertEqual(item["subtotal"], Decimal("345.00"))

    def test_preco_zero_nao_permitido(self):
        with self.assertRaises(ValueError):
            calcular_item_venda("100", "0", "1")

    def test_desconto_e_acrescimo_gerais(self):
        totais = calcular_totais(
            "200",
            desconto_tipo="PERCENTUAL",
            desconto_valor="10",
            acrescimo_tipo="VALOR",
            acrescimo_valor="15",
        )
        self.assertEqual(totais["desconto"], Decimal("20.00"))
        self.assertEqual(totais["acrescimo"], Decimal("15.00"))
        self.assertEqual(totais["total"], Decimal("195.00"))


if __name__ == "__main__":
    unittest.main()
