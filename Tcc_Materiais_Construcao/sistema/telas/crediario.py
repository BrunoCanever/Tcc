"""Fluxo de crediário: cliente -> vendas -> conferência -> pagamento -> recibo."""
import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import ttk, messagebox

from funcoes.crediario_funcoes import (
    FORMAS_QUITACAO, JUROS_MENSAL, listar_clientes_crediario, listar_recebimentos_cliente,
    listar_vendas_cliente, calcular_totais_baixa, liquidar_crediario,
    receber_parcial_crediario, dinheiro,
)
from funcoes.utils import moeda
from telas.helpers import mostrar_erro
from relatorios.recibo_crediario import (
    gerar_recibo_crediario, gerar_extrato_pendente, gerar_nota_saldo,
)


class TelaCrediario(ttk.Frame):
    def __init__(self, master, funcionario=None):
        super().__init__(master, padding=14)
        self.funcionario = funcionario or {}
        self.cliente_atual = None
        self.vendas = []
        self.selecionadas = set()
        self.etapa = 'LISTA'
        self._traces_ajustes = []
        self.busca = tk.StringVar()
        self.modo = tk.StringVar(value='NOME')
        self.valor_proposto = tk.StringVar(value='0.00')
        self.desconto = tk.StringVar(value='0.00')
        self.acrescimo = tk.StringVar(value='0.00')
        self.forma = tk.StringVar(value='PIX')
        self.modo_baixa = tk.StringVar(value='QUITACAO')
        self.recebido = tk.StringVar()
        self._montar_lista()

    def ao_exibir(self):
        if self.etapa == 'LISTA':
            self.carregar_clientes()

    def _limpar(self):
        for var, trace_id in self._traces_ajustes:
            try:
                var.trace_remove('write', trace_id)
            except tk.TclError:
                pass
        self._traces_ajustes.clear()
        for filho in list(self.winfo_children()):
            filho.destroy()

    def _titulo(self, titulo, subtitulo=''):
        ttk.Label(self, text=titulo, style='Titulo.TLabel').pack(anchor='w', pady=(0, 4))
        if subtitulo:
            ttk.Label(self, text=subtitulo, style='Subtitulo.TLabel').pack(anchor='w', pady=(0, 10))

    def _arvore(self, pai, colunas, altura=10):
        corpo = ttk.Frame(pai)
        corpo.pack(fill='both', expand=True)
        tree = ttk.Treeview(corpo, columns=[c[0] for c in colunas], show='headings',
                            selectmode='browse', height=altura)
        for col, titulo, largura in colunas:
            tree.heading(col, text=titulo)
            tree.column(col, width=largura, minwidth=60, stretch=True)
        ys = ttk.Scrollbar(corpo, command=tree.yview)
        xs = ttk.Scrollbar(corpo, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        tree.grid(row=0, column=0, sticky='nsew')
        ys.grid(row=0, column=1, sticky='ns')
        xs.grid(row=1, column=0, sticky='ew')
        corpo.columnconfigure(0, weight=1)
        corpo.rowconfigure(0, weight=1)
        return tree

    def _montar_lista(self):
        self.etapa = 'LISTA'
        self._limpar()
        self._titulo(
            'Crediário dos clientes',
            'Selecione um cliente e marque as vendas a quitar. Juros simples de 1% ao mês (dias/30), apenas após o vencimento.',
        )

        # O rodapé é posicionado ANTES das listas expansíveis, para que
        # os comandos de seleção e de baixa nunca fiquem fora da tela.
        rodape = ttk.Frame(self, padding=(4, 8, 4, 2))
        rodape.pack(side='bottom', fill='x')

        resumo = ttk.Notebook(rodape)
        resumo.pack(fill='x', pady=(0, 6))
        aba_valor = ttk.Frame(resumo, padding=(12, 7))
        aba_juros = ttk.Frame(resumo, padding=(12, 7))
        resumo.add(aba_valor, text='Vendas selecionadas')
        resumo.add(aba_juros, text='Total com juros')
        self.lbl_principal = ttk.Label(
            aba_valor, text='Valor das vendas: R$ 0,00',
            font=('Segoe UI Semibold', 13),
        )
        self.lbl_principal.pack(side='left', padx=(0, 20))
        self.lbl_contagem = ttk.Label(aba_valor, text='0 venda(s) marcada(s)')
        self.lbl_contagem.pack(side='left')
        self.lbl_juros = ttk.Label(
            aba_juros, text='Juros simples: R$ 0,00',
            font=('Segoe UI Semibold', 11),
        )
        self.lbl_juros.pack(side='left', padx=(0, 25))
        self.lbl_total = ttk.Label(
            aba_juros, text='TOTAL COM JUROS: R$ 0,00',
            font=('Segoe UI Semibold', 13),
        )
        self.lbl_total.pack(side='left')

        # Divisão em duas linhas evita que a ação principal seja comprimida
        # ou cortada em janelas menores.
        acoes = ttk.Frame(rodape)
        acoes.pack(fill='x')
        extras = ttk.Frame(acoes)
        extras.pack(fill='x', pady=(0, 4))
        ttk.Button(
            extras, text='Selecionar atrasadas', command=self.selecionar_atrasadas,
        ).pack(side='left', padx=(0, 5))
        ttk.Button(
            extras, text='Histórico de baixas', command=self._historico,
        ).pack(side='left', padx=(0, 5))

        principais = ttk.Frame(acoes)
        principais.pack(fill='x')
        ttk.Button(
            principais, text='Marcar / desmarcar', command=self.alternar_venda,
        ).pack(side='left', padx=(0, 5))
        ttk.Button(
            principais, text='Selecionar todas', command=self.selecionar_todas,
        ).pack(side='left', padx=(0, 5))
        ttk.Button(
            principais, text='Limpar seleção', command=self.limpar_selecao,
        ).pack(side='left', padx=(0, 5))
        self.btn_baixar = ttk.Button(
            principais, text='Continuar para baixa →', style='Primario.TButton',
            command=self._informar_valor,
        )
        self.btn_baixar.pack(side='right')

        busca = ttk.Frame(self)
        busca.pack(fill='x', pady=(0, 8))
        ttk.Label(busca, text='Buscar por').pack(side='left')
        ttk.Combobox(
            busca, textvariable=self.modo, width=13, state='readonly',
            values=['NOME', 'DOCUMENTO', 'TELEFONE', 'ID'],
        ).pack(side='left', padx=6)
        entry = ttk.Entry(busca, textvariable=self.busca, width=33)
        entry.pack(side='left', fill='x', expand=True)
        entry.bind('<Return>', lambda _: self.carregar_clientes())
        ttk.Button(busca, text='Pesquisar', command=self.carregar_clientes).pack(side='left', padx=5)

        div = ttk.Panedwindow(self, orient='horizontal')
        div.pack(fill='both', expand=True)
        esq = ttk.LabelFrame(div, text='Clientes', padding=8)
        dir = ttk.Frame(div)
        div.add(esq, weight=2)
        div.add(dir, weight=5)
        self.tree_clientes = self._arvore(esq, [
            ('id', 'ID', 55), ('nome', 'Nome', 185),
            ('documento', 'CPF/CNPJ', 120), ('saldo', 'Aberto (sem juros)', 125),
        ], 13)
        self.tree_clientes.bind('<<TreeviewSelect>>', self._selecionar_cliente)

        ttk.Label(
            dir, text='Compras a prazo do cliente',
            font=('Segoe UI Semibold', 11),
        ).pack(anchor='w')
        self.lbl_cliente = ttk.Label(dir, text='Escolha um cliente à esquerda.')
        self.lbl_cliente.pack(anchor='w', pady=(3, 5))
        self.tree_vendas = self._arvore(dir, [
            ('sel', '✓', 35), ('venda', 'Venda', 60), ('data', 'Data', 105),
            ('parcelas', 'Parcelas em aberto', 100),
            ('original', 'Valor aberto', 112),
            ('juros', 'Juros', 90), ('total', 'Total', 112),
        ], 11)
        # Um clique na linha já marca/desmarca a compra.
        self.tree_vendas.bind('<ButtonRelease-1>', self._clique_venda)
        self.tree_vendas.bind('<Return>', lambda _: self.alternar_venda())
        self.tree_vendas.bind('<space>', lambda _: self.alternar_venda())

        self.carregar_clientes()
        # Ao voltar da etapa de valor/conferência, o cliente ainda é o mesmo.
        # O evento de seleção não dispara uma nova consulta nesse caso,
        # portanto restauramos a listagem e suas marcações explicitamente.
        if self.cliente_atual is not None:
            self._recarregar_vendas()

    def _clique_venda(self, evento):
        """Marca exatamente a linha clicada, sem depender do foco anterior."""
        linha = self.tree_vendas.identify_row(evento.y)
        if linha and self.tree_vendas.identify_region(evento.x, evento.y) in {'cell', 'tree'}:
            self.alternar_venda(id_venda=int(linha))

    def carregar_clientes(self):
        try:
            clientes = listar_clientes_crediario(self.busca.get(), self.modo.get())
            atual = self.cliente_atual['id_cliente'] if self.cliente_atual else None
            for row in self.tree_clientes.get_children():
                self.tree_clientes.delete(row)
            for c in clientes:
                self.tree_clientes.insert('', 'end', iid=str(c['id_cliente']), values=(
                    c['id_cliente'], c['nome'], c['cpf_cnpj'] or '', moeda(c['saldo_aberto'] or 0)))
            if atual is not None and self.tree_clientes.exists(str(atual)):
                self.tree_clientes.selection_set(str(atual))
            elif clientes:
                self.tree_clientes.selection_set(str(clientes[0]['id_cliente']))
            else:
                self.cliente_atual = None
                self.vendas = []
                self.selecionadas.clear()
                self.lbl_cliente.config(text='Nenhum cliente encontrado.')
                self._desenhar_vendas()
        except Exception as erro:
            mostrar_erro(erro)

    def _selecionar_cliente(self, _evento=None):
        sel = self.tree_clientes.selection()
        if not sel:
            return
        id_cliente = int(sel[0])
        if self.cliente_atual and self.cliente_atual['id_cliente'] == id_cliente:
            return
        dados = self.tree_clientes.item(sel[0], 'values')
        self.cliente_atual = {'id_cliente': id_cliente, 'nome': dados[1]}
        self.selecionadas.clear()
        self._recarregar_vendas()

    def _recarregar_vendas(self):
        if not self.cliente_atual:
            return
        try:
            self.vendas = listar_vendas_cliente(self.cliente_atual['id_cliente'])
            self.selecionadas.intersection_update({v['id_venda'] for v in self.vendas
                                                   if any(p['status'] != 'PAGA' for p in v['parcelas'])})
            self.lbl_cliente.config(text=self.cliente_atual['nome'])
            self._desenhar_vendas()
        except Exception as erro:
            mostrar_erro(erro)

    def _desenhar_vendas(self):
        for row in self.tree_vendas.get_children():
            self.tree_vendas.delete(row)
        for v in self.vendas:
            pendentes = [p for p in v['parcelas'] if p['status'] != 'PAGA']
            if not pendentes:
                continue
            identificador = v['id_venda']
            self.tree_vendas.insert('', 'end', iid=str(identificador), values=(
                '', f"#{identificador}", str(v['data_venda'])[:10],
                len(pendentes), moeda(v['principal']),
                moeda(v['juros']), moeda(v['total_atual']),
            ))
        self._atualizar_marcacoes()

    def _vendas_selecionadas(self):
        return [v for v in self.vendas if v['id_venda'] in self.selecionadas]

    def _parcelas_selecionadas(self):
        return [p for v in self._vendas_selecionadas()
                for p in v['parcelas'] if p['status'] != 'PAGA']

    def _atualizar_resumo(self):
        vendas = self._vendas_selecionadas()
        principal = sum((v['principal'] for v in vendas), Decimal('0'))
        juros = sum((v['juros'] for v in vendas), Decimal('0'))
        self.lbl_principal.config(text=f'Valor das vendas: {moeda(principal)}')
        self.lbl_contagem.config(text=f'{len(vendas)} venda(s) marcada(s)')
        self.lbl_juros.config(text=f'Juros: {moeda(juros)}')
        self.lbl_total.config(text=f'TOTAL COM JUROS: {moeda(principal + juros)}')
        # O botão sempre aparece, inclusive sem seleção, quando explica o
        # que falta para avançar. Com uma única venda já é possível continuar.

    def _atualizar_marcacoes(self):
        """Altera só as marcas: não reconstrói o Treeview nem muda o cliente."""
        for item in self.tree_vendas.get_children():
            self.tree_vendas.set(item, 'sel', '✓' if int(item) in self.selecionadas else '')
        self._atualizar_resumo()

    def alternar_venda(self, id_venda=None):
        if id_venda is None:
            selecionados = self.tree_vendas.selection()
            if not selecionados:
                foco = self.tree_vendas.focus()
                selecionados = (foco,) if foco else ()
            if not selecionados:
                return 'break'
            id_venda = int(selecionados[0])

        if str(id_venda) not in self.tree_vendas.get_children():
            return 'break'
        if id_venda in self.selecionadas:
            self.selecionadas.remove(id_venda)
        else:
            self.selecionadas.add(id_venda)
        self._atualizar_marcacoes()
        return 'break'

    def selecionar_todas(self):
        self.selecionadas = {
            v['id_venda'] for v in self.vendas
            if any(p['status'] != 'PAGA' for p in v['parcelas'])
        }
        self._atualizar_marcacoes()

    def limpar_selecao(self):
        self.selecionadas.clear()
        # O destaque azul da linha também é removido, evitando a impressão
        # de que ainda existem vendas selecionadas.
        self.tree_vendas.selection_remove(self.tree_vendas.selection())
        self.tree_vendas.focus('')
        self._atualizar_marcacoes()

    def selecionar_atrasadas(self):
        self.selecionadas = {
            v['id_venda'] for v in self.vendas
            if any(p['status'] != 'PAGA' and p['dias_atraso'] > 0
                   for p in v['parcelas'])
        }
        self._atualizar_marcacoes()

    def _historico(self):
        if not self.cliente_atual:
            messagebox.showinfo('Crediário', 'Escolha um cliente primeiro.')
            return
        try:
            historico = listar_recebimentos_cliente(self.cliente_atual['id_cliente'])
            self._limpar()
            self.etapa = 'HISTORICO'
            self._titulo('Histórico de baixas', self.cliente_atual['nome'])
            quadro = ttk.LabelFrame(self, text='Pagamentos realizados', padding=10)
            quadro.pack(fill='both', expand=True)
            tree = self._arvore(quadro, [
                ('id','Recibo',75), ('data','Data',150), ('principal','Principal',120),
                ('juros','Juros',110), ('desconto','Desconto',110),
                ('acrescimo','Acréscimo',110), ('total','Pago',130), ('forma','Forma',135)], 13)
            for r in historico:
                tree.insert('', 'end', iid=str(r['id_recebimento']), values=(
                    r['id_recebimento'], str(r['data_recebimento'])[:19],
                    moeda(r['principal']), moeda(r['juros']), moeda(r['desconto']),
                    moeda(r['acrescimo']), moeda(r['total_pago']), r['forma']))
            actions = ttk.Frame(self)
            actions.pack(fill='x', pady=10)
            ttk.Button(actions, text='Voltar aos clientes', command=self._montar_lista).pack(side='left')
            def emitir():
                sel = tree.selection()
                if sel:
                    self._recibo(int(sel[0]))
            ttk.Button(actions, text='Abrir recibo selecionado', command=emitir).pack(side='right')
            def nota():
                sel = tree.selection()
                if sel:
                    self._nota_parcial(int(sel[0]))
            ttk.Button(actions, text='Nota do saldo (pagamento parcial)',
                       command=nota).pack(side='right', padx=8)
        except Exception as erro:
            mostrar_erro(erro)

    def _informar_valor(self):
        if not self.selecionadas:
            messagebox.showwarning('Crediário', 'Selecione uma ou mais vendas.'); return
        try:
            resumo = calcular_totais_baixa(self._parcelas_selecionadas())
        except Exception as erro:
            mostrar_erro(erro); return
        self.valor_proposto.set(f"{resumo['total']:.2f}")
        self.desconto.set('0.00')
        self.acrescimo.set('0.00')
        self.modo_baixa.set('QUITACAO')
        self._limpar()
        self.etapa = 'VALOR'
        self._titulo('Valor do recebimento', 'Informe o valor recebido. Uma quantia menor pode virar pagamento parcial com uma nova nota do saldo.')
        quadro = ttk.LabelFrame(self, text='Quanto será pago?', padding=22)
        quadro.pack(fill='x', pady=14)
        ttk.Label(quadro, text=f"Valor original: {moeda(resumo['principal'])}").pack(anchor='w', pady=5)
        ttk.Label(quadro, text=f"Juros simples: {moeda(resumo['juros'])}").pack(anchor='w', pady=5)
        ttk.Label(quadro, text='Valor a receber (R$)').pack(anchor='w', pady=(12, 2))
        entry = ttk.Entry(quadro, textvariable=self.valor_proposto, width=22, font=('Segoe UI', 14))
        entry.pack(anchor='w', pady=(0, 15))
        entry.bind('<Return>', lambda _: self._montar_conferencia())
        ttk.Button(quadro, text='Voltar', command=self._montar_lista).pack(side='left')
        ttk.Button(quadro, text='Confirmar valor →', style='Primario.TButton',
                   command=self._montar_conferencia).pack(side='right')
        entry.focus_set(); entry.selection_range(0, 'end')

    def _montar_conferencia(self):
        try:
            dinheiro(self.valor_proposto.get(), 'Valor pago')
            self._desenhar_conferencia()
        except Exception as erro:
            mostrar_erro(erro)

    def _desenhar_conferencia(self):
        """Conferência com barra inferior fixa e tabela que ocupa o espaço restante.

        A barra é criada e posicionada ANTES da lista expansível. Com isso,
        nenhuma quantidade de parcelas esconde os campos ou botões de baixa.
        """
        self.etapa = 'CONFERENCIA'
        self._limpar()
        self._titulo(
            'Conferência do crediário',
            'Confira cada venda e seus juros. Descontos e acréscimos são registrados no recibo.',
        )
        parcelas = self._parcelas_selecionadas()
        resumo = calcular_totais_baixa(parcelas)

        # A barra inferior é fixa. O Treeview receberá somente a altura
        # disponível entre o cabeçalho e esta barra, sem empurrá-la para fora.
        rodape = ttk.Frame(self, padding=(2, 6, 2, 2))
        rodape.pack(side='bottom', fill='x')

        # A ação principal fica na ÚLTIMA linha e sempre permanece visível.
        botoes = ttk.Frame(rodape)
        botoes.pack(side='bottom', fill='x', pady=(6, 0))
        ttk.Button(
            botoes, text='← Corrigir valor', command=self._informar_valor,
        ).pack(side='left')
        ttk.Button(
            botoes, text='Aplicar desconto da diferença',
            command=self._aplicar_desconto_diferenca,
        ).pack(side='left', padx=8)
        self.btn_continuar_pagamento = ttk.Button(
            botoes, text='Continuar para pagamento →',
            style='Primario.TButton', command=self._continuar,
        )
        self.btn_continuar_pagamento.pack(side='right')

        self.lbl_validacao = ttk.Label(
            rodape, text='', foreground='#A13232', justify='left',
        )
        self.lbl_validacao.pack(side='bottom', fill='x', pady=(3, 0))

        self.lbl_ajuste = ttk.Label(
            rodape, text='', font=('Segoe UI Semibold', 11), justify='left',
        )
        self.lbl_ajuste.pack(side='bottom', fill='x', pady=(6, 0))

        # Não confundir desconto (perdão da diferença) com pagamento parcial.
        # As duas ações ficam visíveis independentemente do número de parcelas.
        opcoes = ttk.Frame(rodape)
        opcoes.pack(side='bottom', fill='x', pady=(3, 0))
        ttk.Radiobutton(
            opcoes, text='Quitar vendas (total ou com desconto)',
            variable=self.modo_baixa, value='QUITACAO', command=self._prever_total,
        ).pack(side='left', padx=(0, 16))
        ttk.Radiobutton(
            opcoes, text='Pagar uma parte e GERAR NOVA NOTA do saldo restante',
            variable=self.modo_baixa, value='PARCIAL', command=self._prever_total,
        ).pack(side='left')

        ajustes = ttk.Frame(rodape)
        ajustes.pack(side='bottom', fill='x', pady=(2, 0))
        ttk.Label(ajustes, text='Desconto (R$)').grid(row=0, column=0, sticky='w')
        ttk.Entry(
            ajustes, textvariable=self.desconto, width=17,
        ).grid(row=1, column=0, sticky='w', padx=(0, 15))
        ttk.Label(ajustes, text='Acréscimo (R$)').grid(row=0, column=1, sticky='w')
        ttk.Entry(
            ajustes, textvariable=self.acrescimo, width=17,
        ).grid(row=1, column=1, sticky='w', padx=(0, 15))

        def ajustar_quebra(_evento=None):
            # Mesmo com a janela reduzida, os textos explicativos não
            # ultrapassam a largura do conteúdo principal.
            largura = max(250, rodape.winfo_width() - 20)
            self.lbl_ajuste.configure(wraplength=largura)
            self.lbl_validacao.configure(wraplength=largura)

        rodape.bind('<Configure>', ajustar_quebra)
        self._traces_ajustes.append((
            self.desconto,
            self.desconto.trace_add('write', lambda *_: self._prever_total()),
        ))
        self._traces_ajustes.append((
            self.acrescimo,
            self.acrescimo.trace_add('write', lambda *_: self._prever_total()),
        ))

        # A lista com scrollbar usa apenas o espaço restante acima do rodapé.
        quadro = ttk.LabelFrame(
            self, text='Vendas e parcelas selecionadas', padding=8,
        )
        quadro.pack(fill='both', expand=True, pady=(4, 0))
        self.tree_conferencia = self._arvore(quadro, [
            ('venda', 'Venda', 70), ('parcela', 'Parcela', 70),
            ('venc', 'Vencimento', 120), ('dias', 'Atraso (dias)', 95),
            ('valor', 'Original', 125), ('juros', 'Juros simples', 135),
            ('total', 'Total', 135),
        ], 7)
        for p in resumo['linhas']:
            self.tree_conferencia.insert('', 'end', values=(
                f"#{p['id_venda']}", p['numero'], p['data_vencimento'],
                p['dias_atraso'], moeda(p['principal']),
                moeda(p['juros']), moeda(p['total']),
            ))
        self._prever_total()

    def _prever_total(self):
        try:
            resumo = calcular_totais_baixa(self._parcelas_selecionadas(),
                                            self.desconto.get(), self.acrescimo.get())
            proposto = dinheiro(self.valor_proposto.get())
            self.lbl_ajuste.configure(text=(
                f"Original: {moeda(resumo['principal'])}   |   "
                f"Juros: {moeda(resumo['juros'])}   |   "
                f"Desconto: {moeda(resumo['desconto'])}\n"
                f"Acréscimo: {moeda(resumo['acrescimo'])}   |   "
                f"TOTAL: {moeda(resumo['total'])}"
            ))
            parcial = self.modo_baixa.get() == 'PARCIAL'
            if parcial:
                saldo = resumo['total'] - proposto
                if resumo['desconto'] or resumo['acrescimo']:
                    msg = 'Para pagamento parcial, mantenha desconto e acréscimo em zero. Eles valem apenas para quitação.'
                    valido = False
                elif proposto <= 0 or saldo <= 0:
                    msg = 'Para gerar nova nota, o pagamento deve ser maior que zero e menor que o total.'
                    valido = False
                else:
                    msg = (f'PAGAMENTO PARCIAL: receber {moeda(proposto)} agora e emitir NOVA NOTA '
                           f'de {moeda(saldo)} em aberto (juros futuros podem variar).')
                    valido = True
            elif proposto < resumo['total']:
                msg = (f"Faltam {moeda(resumo['total']-proposto)}. "
                       'Escolha pagamento parcial para gerar nova nota, ou registre desconto para quitar.')
                valido = False
            elif proposto > resumo['total']:
                msg = (f"Sobram {moeda(proposto-resumo['total'])}. "
                       'Registre um acréscimo ou corrija o valor informado.')
                valido = False
            else:
                msg = 'Valores conferidos para quitação integral. Pode continuar.'
                valido = True
            self.lbl_validacao.configure(
                text=msg, foreground='#286442' if valido else '#A13232',
            )
            return valido
        except Exception as erro:
            self.lbl_validacao.configure(text=str(erro))
            return False

    def _aplicar_desconto_diferenca(self):
        try:
            base = calcular_totais_baixa(self._parcelas_selecionadas(), '0', self.acrescimo.get())
            pago = dinheiro(self.valor_proposto.get())
            if pago > base['total']:
                raise ValueError('O valor informado excede o total. Use acréscimo ou corrija.')
            self.modo_baixa.set('QUITACAO')
            self.desconto.set(f"{base['total'] - pago:.2f}")
        except Exception as erro:
            mostrar_erro(erro)

    def _continuar(self):
        if not self._prever_total():
            messagebox.showwarning('Conferência', 'Confira o valor e escolha quitação ou pagamento parcial com nova nota.'); return
        self._montar_pagamento()

    def _montar_pagamento(self):
        self.etapa = 'PAGAMENTO'
        self._limpar()
        self._titulo('Forma de pagamento',
            ('Pagamento parcial: o saldo será mantido em aberto e uma nova nota será emitida.'
             if self.modo_baixa.get() == 'PARCIAL'
             else 'Quitação das vendas selecionadas.'))
        total = dinheiro(self.valor_proposto.get())
        quadro = ttk.LabelFrame(self, text='Pagamento', padding=24)
        quadro.pack(fill='x', pady=10)
        ttk.Label(quadro, text=f'Total confirmado: {moeda(total)}',
                  font=('Segoe UI Semibold', 16)).pack(anchor='w', pady=10)
        for forma in FORMAS_QUITACAO:
            ttk.Radiobutton(quadro, text=forma.replace('_', ' ').title(), variable=self.forma,
                            value=forma, command=self._forma_alterada).pack(anchor='w', pady=3)
        ttk.Label(quadro, text='Valor entregue em dinheiro (para troco):').pack(anchor='w', pady=(12, 3))
        self.entry_recebido = ttk.Entry(quadro, textvariable=self.recebido, width=20)
        self.entry_recebido.pack(anchor='w')
        self.recebido.set(f'{total:.2f}')
        self._forma_alterada()
        comandos = ttk.Frame(self)
        comandos.pack(fill='x', pady=12)
        ttk.Button(comandos, text='← Voltar à conferência', command=self._desenhar_conferencia).pack(side='left')
        ttk.Button(comandos, text='Confirmar pagamento e baixar', style='Primario.TButton',
                   command=self._finalizar).pack(side='right')

    def _forma_alterada(self):
        self.entry_recebido.configure(state='normal' if self.forma.get() == 'DINHEIRO' else 'disabled')

    def _finalizar(self):
        try:
            if not self.funcionario.get('id_funcionario'):
                raise ValueError('Funcionário da sessão não identificado.')
            parcial = self.modo_baixa.get() == 'PARCIAL'
            if not self._previsao_valida_antes_de_salvar():
                return
            descricao = ('O restante continuará em aberto e receberá uma nova nota.'
                         if parcial else 'As parcelas selecionadas serão quitadas.')
            if not messagebox.askyesno('Confirmar baixa',
                 f"Confirmar recebimento de {moeda(dinheiro(self.valor_proposto.get()))} "
                 f"em {self.forma.get()}?\n\n{descricao}"):
                return
            args = (self.cliente_atual['id_cliente'],
                    [p['id_parcela'] for p in self._parcelas_selecionadas()],
                    self.funcionario['id_funcionario'], self.forma.get(),
                    self.valor_proposto.get())
            recebido = self.recebido.get() if self.forma.get() == 'DINHEIRO' else None
            if parcial:
                id_recebimento = receber_parcial_crediario(*args, valor_recebido=recebido)
            else:
                id_recebimento = liquidar_crediario(*args, self.desconto.get(),
                                                    self.acrescimo.get(), recebido)
            self._exibir_conclusao(id_recebimento, parcial=parcial)
        except Exception as erro:
            mostrar_erro(erro)

    def _previsao_valida_antes_de_salvar(self):
        try:
            resumo = calcular_totais_baixa(self._parcelas_selecionadas(),
                                            self.desconto.get(), self.acrescimo.get())
            pago = dinheiro(self.valor_proposto.get())
            if self.modo_baixa.get() == 'PARCIAL':
                valido = (pago > 0 and pago < resumo['total']
                          and resumo['desconto'] == 0 and resumo['acrescimo'] == 0)
            else:
                valido = pago == resumo['total']
            if not valido:
                messagebox.showwarning('Conferência', 'Volte e confira os valores e o tipo de baixa.')
            return valido
        except Exception as erro:
            mostrar_erro(erro)
            return False

    def _exibir_conclusao(self, id_recebimento, parcial=False):
        self.etapa = 'CONCLUIDO'
        self._limpar()
        self._titulo('Pagamento parcial registrado' if parcial else 'Pagamento registrado',
                     f'Recebimento #{id_recebimento} concluído com sucesso.')
        ttk.Label(self, text=f"Total recebido: {moeda(dinheiro(self.valor_proposto.get()))}",
                  font=('Segoe UI Semibold', 17)).pack(anchor='w', pady=15)
        ttk.Label(self, text=(
            'Uma NOVA NOTA foi registrada com os saldos restantes das vendas selecionadas. '
            'As parcelas parcialmente pagas continuam abertas.' if parcial else
            'As parcelas quitadas não aparecem mais como pendentes.'
        ), wraplength=820).pack(anchor='w')
        acoes = ttk.Frame(self)
        acoes.pack(fill='x', pady=16)
        ttk.Button(acoes, text='Gerar recibo', command=lambda: self._recibo(id_recebimento)).pack(side='left')
        if parcial:
            ttk.Button(
                acoes, text='Abrir NOVA NOTA do saldo restante', style='Primario.TButton',
                command=lambda: self._nota_parcial(id_recebimento),
            ).pack(side='left', padx=8)
        else:
            ttk.Button(acoes, text='Extrato das pendências', command=self._extrato_restante).pack(side='left', padx=8)
        ttk.Button(acoes, text='Voltar aos clientes', style='Primario.TButton',
                   command=self._montar_lista).pack(side='right')
        if parcial:
            # Gerar automaticamente os dois documentos, mesmo que não queira abrir.
            # Falha no PDF não desfaz o recebimento já confirmado no banco.
            try:
                gerar_recibo_crediario(id_recebimento)
                gerar_nota_saldo(id_recebimento)
            except Exception as erro:
                mostrar_erro(erro)
            if messagebox.askyesno('Nova nota de saldo',
                                  'Deseja abrir a NOVA NOTA do saldo restante para imprimir?'):
                self._nota_parcial(id_recebimento)
            if messagebox.askyesno('Recibo', 'Deseja abrir o recibo do pagamento realizado?'):
                self._recibo(id_recebimento)
        elif messagebox.askyesno('Recibo', 'Deseja gerar/imprimir o recibo deste pagamento?'):
            self._recibo(id_recebimento)


    def _nota_parcial(self, id_recebimento):
        try:
            caminho = gerar_nota_saldo(id_recebimento)
            messagebox.showinfo('Nova nota criada',
                                f'Nota de saldo restante salva em:\n{caminho}\n\n'
                                'Documento informativo, não é uma nova venda.')
            import os
            if os.name == 'nt':
                os.startfile(str(caminho.resolve()))
        except Exception as erro:
            mostrar_erro(erro)

    def _recibo(self, id_recebimento):
        try:
            caminho = gerar_recibo_crediario(id_recebimento)
            messagebox.showinfo('Recibo criado', f'Recibo salvo em:\n{caminho}\n\nO PDF será aberto para impressão.')
            import os
            if os.name == 'nt':
                os.startfile(str(caminho.resolve()))
        except Exception as erro:
            mostrar_erro(erro)

    def _extrato_restante(self):
        try:
            caminho = gerar_extrato_pendente(self.cliente_atual['id_cliente'])
            messagebox.showinfo('Nota de pendências', f'Extrato salvo em:\n{caminho}\n\n'
                'Este documento não cria nem duplica uma venda.')
        except Exception as erro:
            mostrar_erro(erro)
