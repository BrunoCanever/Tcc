import unittest

from funcoes.busca_produtos import filtrar_produtos


PRODUTOS = [
    {"id_produto": 1, "codigo": "AGR-001", "nome": "Areia Média", "categoria": "Areia e Brita"},
    {"id_produto": 2, "codigo": "CIM-001", "nome": "Cimento CP II", "categoria": "Cimentos"},
    {"id_produto": 3, "codigo": "PIS-010", "nome": "Porcelanato Acetinado", "categoria": "Pisos"},
]


class TestBuscaProdutos(unittest.TestCase):
    def test_por_nome(self):
        resultado = filtrar_produtos(PRODUTOS, "cimento", "NOME")
        self.assertEqual([p["codigo"] for p in resultado], ["CIM-001"])

    def test_por_codigo(self):
        resultado = filtrar_produtos(PRODUTOS, "AGR-001", "CODIGO")
        self.assertEqual([p["nome"] for p in resultado], ["Areia Média"])

    def test_codigo_aceita_id_antigo(self):
        resultado = filtrar_produtos(PRODUTOS, "3", "CODIGO")
        self.assertEqual([p["codigo"] for p in resultado], ["PIS-010"])

    def test_por_categoria(self):
        resultado = filtrar_produtos(PRODUTOS, "pisos", "CATEGORIA")
        self.assertEqual([p["codigo"] for p in resultado], ["PIS-010"])

    def test_sem_termo_mostra_todos(self):
        self.assertEqual(len(filtrar_produtos(PRODUTOS, "", "NOME")), 3)


if __name__ == "__main__":
    unittest.main()
