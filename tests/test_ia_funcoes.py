import unittest
from pathlib import Path
from unittest.mock import patch
from decimal import Decimal

from funcoes.ia_funcoes import (
    consultar_catalogo_inteligente,
    responder_pergunta,
    status_ia,
)


PRODUTOS = [
    {
        "id_produto": 1,
        "codigo": "CIM-001",
        "nome": "Cimento CP II 50 kg",
        "descricao": "Cimento para uso geral",
        "preco": Decimal("36.60"),
        "quantidade_estoque": Decimal("30"),
        "estoque_minimo": Decimal("10"),
        "unidade_medida": "SC",
        "categoria": "Cimentos",
        "fornecedor": "Fornecedor A",
        "id_fornecedor": 1,
        "tipo_localizacao": "INTERNA",
        "corredor": "01",
        "prateleira": "A",
        "descricao_localizacao": None,
    },
    {
        "id_produto": 2,
        "codigo": "AGR-007",
        "nome": "Areia Média Lavada",
        "descricao": "Agregado vendido por metro cúbico",
        "preco": Decimal("219.90"),
        "quantidade_estoque": Decimal("3"),
        "estoque_minimo": Decimal("5"),
        "unidade_medida": "MC3",
        "categoria": "Areia e Brita",
        "fornecedor": "Fornecedor B",
        "id_fornecedor": 2,
        "tipo_localizacao": "EXTERNA",
        "corredor": None,
        "prateleira": None,
        "descricao_localizacao": "Pátio externo — setor 2, baia 7",
    },
]


class TestAssistenteLocal(unittest.TestCase):
    def test_consulta_fornecedor_usa_campos_reais_do_banco(self):
        fonte = Path(__file__).resolve().parents[1] / "funcoes" / "ia_funcoes.py"
        codigo = fonte.read_text(encoding="utf-8")
        self.assertIn(
            "COALESCE(f.nome_fantasia, f.razao_social) AS fornecedor",
            codigo,
        )
        self.assertNotIn(
            "c.nome AS categoria, f.nome AS fornecedor",
            codigo,
        )

    def test_status_nao_usa_api(self):
        status = status_ia()
        self.assertEqual(status["modo"], "LOCAL")
        self.assertFalse(status["online"])
        self.assertIn("sem custo", status["texto"].lower())

    @patch("funcoes.ia_funcoes._carregar_produtos", return_value=PRODUTOS)
    def test_busca_produto_por_nome(self, _mock):
        dados = consultar_catalogo_inteligente(termos=["cimento cp ii"])
        self.assertEqual(dados["produtos"][0]["codigo"], "CIM-001")

    @patch("funcoes.ia_funcoes._carregar_produtos", return_value=PRODUTOS)
    def test_responde_localizacao(self, _mock):
        texto, modo = responder_pergunta("Onde fica o cimento CP II?")
        self.assertEqual(modo, "LOCAL")
        self.assertIn("Corredor 01", texto)
        self.assertIn("Prateleira A", texto)

    @patch("funcoes.ia_funcoes._carregar_produtos", return_value=PRODUTOS)
    def test_quantidade_suficiente(self, _mock):
        texto, _ = responder_pergunta("Temos 20 sacos de cimento?")
        self.assertIn("suficiente", texto.lower())
        self.assertIn("20", texto)

    @patch("funcoes.ia_funcoes.consultar_catalogo_inteligente")
    def test_estoque_baixo(self, mock_consulta):
        mock_consulta.return_value = {
            "produtos": [{
                "codigo": "AGR-007",
                "nome": "Areia Média Lavada",
                "preco": "219.90",
                "quantidade_estoque": "3",
                "estoque_minimo": "5",
                "unidade_medida": "MC3",
                "localizacao": "Pátio externo — setor 2, baia 7",
            }]
        }
        texto, _ = responder_pergunta("Quais produtos estão com estoque baixo?")
        self.assertIn("reposição", texto.lower())
        self.assertIn("Areia Média Lavada", texto)

    def test_ajuda_explica_modo_local(self):
        texto, modo = responder_pergunta("ajuda")
        self.assertEqual(modo, "LOCAL")
        self.assertIn("sem internet", texto.lower())
        self.assertIn("somente leitura", texto.lower())


if __name__ == "__main__":
    unittest.main()
