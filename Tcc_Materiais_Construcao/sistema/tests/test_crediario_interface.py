"""Regressão visual do crediário (usa Xvfb no Linux ou desktop com Tk)."""
import sys
import types
import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

# Banco simulado: os testes não acessam o MySQL real.
if 'conexao' not in sys.modules:
    conexao = types.ModuleType('conexao')
    conexao.conectar_banco = lambda: None
    sys.modules['conexao'] = conexao

import tkinter as tk
from tkinter import ttk
from telas import crediario as ui


def _venda(n):
    return {
        'id_venda': n,
        'data_venda': date.today() - timedelta(days=n),
        'parcelas': [{
            'id_parcela': n, 'numero': 1, 'status': 'ATRASADA',
            'dias_atraso': 30, 'id_venda': n,
            'data_vencimento': date.today() - timedelta(days=30),
            'valor': Decimal('100'),
        }],
        'principal': Decimal('100'),
        'juros': Decimal('1'),
        'total_atual': Decimal('101'),
    }


class TestCrediarioInterface(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f'Tk sem ambiente gráfico: {erro}')

        self.root.geometry('850x550')
        estilo = ttk.Style(self.root)
        estilo.theme_use('clam')
        estilo.configure('Titulo.TLabel', font=('Arial', 17, 'bold'))
        estilo.configure('Subtitulo.TLabel', font=('Arial', 10))

        self.mocks = [
            patch.object(ui, 'listar_clientes_crediario', return_value=[
                {'id_cliente': 1, 'nome': 'Teste', 'cpf_cnpj': None,
                 'telefone': '', 'saldo_aberto': Decimal('3000')},
            ]),
            patch.object(ui, 'listar_vendas_cliente', return_value=[
                _venda(n) for n in range(1, 31)
            ]),
        ]
        for mock in self.mocks:
            mock.start()
        self.frame = ui.TelaCrediario(self.root, {'id_funcionario': 1})
        self.frame.pack(fill='both', expand=True)
        self.root.update()

    def tearDown(self):
        for mock in reversed(getattr(self, 'mocks', [])):
            mock.stop()
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_continuar_sempre_visivel_com_30_vendas(self):
        botao = self.frame.btn_baixar
        self.assertTrue(botao.winfo_ismapped())
        self.assertGreaterEqual(botao.winfo_width(), 160)
        self.assertLessEqual(
            botao.winfo_rooty() + botao.winfo_height(),
            self.root.winfo_rooty() + self.root.winfo_height(),
        )
        self.assertLessEqual(
            botao.winfo_rootx() + botao.winfo_width(),
            self.root.winfo_rootx() + self.root.winfo_width(),
        )
        self.assertEqual(len(self.frame.tree_vendas.get_children()), 30)

    def test_limpar_desmarca_todas_e_remove_destaque(self):
        self.frame.selecionar_todas()
        self.assertEqual(len(self.frame.selecionadas), 30)
        self.assertEqual(self.frame.tree_vendas.set('1', 'sel'), '✓')
        self.frame.tree_vendas.selection_set('1')
        self.frame.limpar_selecao()
        self.assertEqual(self.frame.selecionadas, set())
        self.assertFalse(self.frame.tree_vendas.selection())
        self.assertTrue(all(
            self.frame.tree_vendas.set(str(n), 'sel') == ''
            for n in range(1, 31)
        ))
        self.assertIn('0 venda(s)', self.frame.lbl_contagem.cget('text'))

    def test_uma_venda_pode_continuar_e_voltar(self):
        self.frame.alternar_venda(id_venda=2)
        self.assertEqual(self.frame.selecionadas, {2})
        self.frame.btn_baixar.invoke()
        self.root.update()
        self.assertEqual(self.frame.etapa, 'VALOR')
        self.frame._montar_lista()
        self.root.update()
        self.assertEqual(len(self.frame.tree_vendas.get_children()), 30)
        self.assertEqual(self.frame.tree_vendas.set('2', 'sel'), '✓')

    def _verificar_botao_na_area_visivel(self, botao):
        self.root.update()
        self.assertTrue(botao.winfo_ismapped())
        self.assertGreater(botao.winfo_width(), 100)
        self.assertGreater(botao.winfo_height(), 15)
        self.assertGreaterEqual(botao.winfo_rooty(), self.frame.winfo_rooty())
        self.assertLessEqual(
            botao.winfo_rooty() + botao.winfo_height(),
            self.frame.winfo_rooty() + self.frame.winfo_height(),
        )
        self.assertLessEqual(
            botao.winfo_rootx() + botao.winfo_width(),
            self.frame.winfo_rootx() + self.frame.winfo_width(),
        )

    def test_conferencia_rodape_fixo_com_30_vendas(self):
        self.frame.selecionar_todas()
        self.frame._informar_valor()
        self.frame._montar_conferencia()
        self.root.update()

        self.assertEqual(self.frame.etapa, 'CONFERENCIA')
        self.assertEqual(len(self.frame.tree_conferencia.get_children()), 30)
        self.assertGreater(self.frame.tree_conferencia.winfo_height(), 50)
        self._verificar_botao_na_area_visivel(
            self.frame.btn_continuar_pagamento
        )
        self.assertTrue(self.frame.lbl_validacao.winfo_ismapped())
        self.assertTrue(self.frame.lbl_ajuste.winfo_ismapped())

        # O total e as ações continuam visíveis após um desconto.
        self.frame.valor_proposto.set('3000.00')
        self.frame._aplicar_desconto_diferenca()
        self.root.update()
        self.assertTrue(self.frame._prever_total())
        self._verificar_botao_na_area_visivel(
            self.frame.btn_continuar_pagamento
        )

    def test_conferencia_em_janela_menor_uma_venda(self):
        self.root.geometry('780x480')
        self.root.update()
        self.frame.alternar_venda(id_venda=1)
        self.frame._informar_valor()
        self.frame._montar_conferencia()
        self.root.update()
        self.assertEqual(len(self.frame.tree_conferencia.get_children()), 1)
        self.assertGreater(self.frame.tree_conferencia.winfo_height(), 30)
        self._verificar_botao_na_area_visivel(
            self.frame.btn_continuar_pagamento
        )

    def test_pagamento_parcial_nova_nota_fica_visivel_e_valido(self):
        self.root.geometry('780x480')
        self.root.update()
        self.frame.selecionar_todas()
        self.frame._informar_valor()
        self.frame.valor_proposto.set('1200.00')
        self.frame._montar_conferencia()
        self.root.update()
        self.assertFalse(self.frame._prever_total())  # não concede desconto implícito
        self.frame.modo_baixa.set('PARCIAL')
        self.root.update()
        self.assertTrue(self.frame._prever_total())
        self.assertIn('NOVA NOTA', self.frame.lbl_validacao.cget('text'))
        self._verificar_botao_na_area_visivel(self.frame.btn_continuar_pagamento)
        self.frame.btn_continuar_pagamento.invoke()
        self.root.update()
        self.assertEqual(self.frame.etapa, 'PAGAMENTO')
        self.assertEqual(self.frame.modo_baixa.get(), 'PARCIAL')

    def test_desconto_diferenca_eh_quitacao_e_nao_parcial(self):
        self.frame.alternar_venda(id_venda=1)
        self.frame._informar_valor()
        self.frame.valor_proposto.set('60.00')
        self.frame._montar_conferencia()
        self.frame.modo_baixa.set('PARCIAL')
        self.frame._aplicar_desconto_diferenca()
        self.root.update()
        self.assertEqual(self.frame.modo_baixa.get(), 'QUITACAO')
        self.assertTrue(self.frame._prever_total())

    def test_clique_unico_alterna_a_marcacao(self):
        arvore = self.frame.tree_vendas
        arvore.see('1')
        self.root.update()
        x, y, _, altura = arvore.bbox('1')
        y += max(2, altura // 2)
        x += 8
        arvore.event_generate('<ButtonPress-1>', x=x, y=y)
        arvore.event_generate('<ButtonRelease-1>', x=x, y=y)
        self.root.update()
        self.assertIn(1, self.frame.selecionadas)
        arvore.event_generate('<ButtonPress-1>', x=x, y=y)
        arvore.event_generate('<ButtonRelease-1>', x=x, y=y)
        self.root.update()
        self.assertNotIn(1, self.frame.selecionadas)


if __name__ == '__main__':
    unittest.main()
