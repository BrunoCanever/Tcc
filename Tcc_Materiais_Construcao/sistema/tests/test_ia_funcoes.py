import unittest

from funcoes.ia_texto import normalizar, extrair_termo_local


class TestIAFuncoes(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar("Onde está a BRITA?"), "onde esta a brita")

    def test_extrair_termo(self):
        termo = extrair_termo_local("Onde está o cimento no estoque?")
        self.assertIn("cimento", termo)
        self.assertNotIn("estoque", termo)


if __name__ == "__main__":
    unittest.main()
