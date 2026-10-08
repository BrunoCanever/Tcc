import unittest
from collections import Counter
from decimal import Decimal

from funcoes.dados_demo import CATEGORIAS_DEMO, gerar_produtos_demo


class TestDadosDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.produtos = gerar_produtos_demo()

    def test_50_produtos_por_categoria(self):
        totais = Counter(p["categoria"] for p in self.produtos)
        self.assertEqual(len(CATEGORIAS_DEMO), 9)
        self.assertEqual(len(self.produtos), 450)
        self.assertTrue(all(totais[categoria] == 50 for categoria in CATEGORIAS_DEMO))

    def test_codigos_unicos(self):
        codigos = [p["codigo"] for p in self.produtos]
        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertTrue(all("-" in codigo for codigo in codigos))

    def test_nomes_unicos_dentro_da_categoria(self):
        pares = [(p["categoria"], p["nome"]) for p in self.produtos]
        self.assertEqual(len(pares), len(set(pares)))

    def test_areia_e_brita_em_metros_cubicos(self):
        produtos = [p for p in self.produtos if p["categoria"] == "Areia e Brita"]
        self.assertEqual(len(produtos), 50)
        self.assertTrue(all(p["unidade_medida"] == "MC3" for p in produtos))
        self.assertTrue(all(p["tipo_localizacao"] == "EXTERNA" for p in produtos))

    def test_pisos_em_metros_quadrados(self):
        produtos = [p for p in self.produtos if p["categoria"] == "Pisos"]
        self.assertTrue(all(p["unidade_medida"] == "M2" for p in produtos))

    def test_hidraulica_tem_metro_e_unidade(self):
        unidades = {p["unidade_medida"] for p in self.produtos if p["categoria"] == "Hidráulica"}
        self.assertEqual(unidades, {"M", "UN"})

    def test_eletrica_tem_medidas_corretas(self):
        unidades = {p["unidade_medida"] for p in self.produtos if p["categoria"] == "Elétrica"}
        self.assertEqual(unidades, {"M", "UN", "RL"})

    def test_tintas_usam_litro_ou_quilo(self):
        unidades = {p["unidade_medida"] for p in self.produtos if p["categoria"] == "Tintas"}
        self.assertEqual(unidades, {"L", "KG"})

    def test_madeiras_usam_metro_ou_metro_quadrado(self):
        unidades = {p["unidade_medida"] for p in self.produtos if p["categoria"] == "Madeiras"}
        self.assertEqual(unidades, {"M", "M2"})


    def test_todas_unidades_estao_padronizadas(self):
        permitidas = {
            "UN", "PC", "CX", "SC", "KG", "G",
            "L", "ML", "M", "M2", "MC3", "RL",
        }
        unidades = {p["unidade_medida"] for p in self.produtos}
        self.assertTrue(unidades.issubset(permitidas))

    def test_precos_positivos(self):
        self.assertTrue(all(p["preco"] > Decimal("0") for p in self.produtos))


if __name__ == "__main__":
    unittest.main()
