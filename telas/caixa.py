import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import ttk, messagebox

from funcoes.caixa_diario_funcoes import obter_caixa_hoje
from funcoes.busca_produtos import filtrar_produtos
from funcoes.calculos_venda import calcular_totais
from funcoes.cliente_funcoes import listar_clientes, obter_cliente
from funcoes.pagamento_funcoes import FORMAS_PAGAMENTO
from funcoes.produto_funcoes import listar_produtos, obter_produto
from funcoes.utils import moeda
from funcoes.venda_funcoes import finalizar_venda
from relatorios.comprovante import gerar_comprovante
from telas.helpers import (
    limpar_tree, mostrar_erro, parse_combo_id,
    confirmar_com_enter, solicitar_texto_enter,
)


ORDENACOES = [
    "Nome A-Z",
    "Nome Z-A",
    "Menor preço",
    "Maior preço",
    "Maior estoque",
    "Menor estoque",
    "Categoria",
]


class TelaCaixa(ttk.Frame):
    """
    Frente de caixa em três etapas:

    1. Produtos e confirmação do preço de cada item.
    2. Cliente, observações e retirada/entrega.
    3. Desconto/acréscimo geral e forma de pagamento.
    """

    def __init__(self, master, funcionario):
        super().__init__(master)

        self.funcionario = funcionario
        self.carrinho = []
        self.produtos_cache = []
        self.clientes_cache = []
        self.etapa_atual = "INICIO"
        self.produto_selecionado_id = None

        # Produtos.
        self.busca_produto = tk.StringVar()
        self.modo_pesquisa = tk.StringVar(value="NOME")
        self.ordenacao = tk.StringVar(value="Nome A-Z")
        self.qtd_produto = tk.StringVar(value="1")
        self.preco_venda = tk.StringVar()

        # Dados da venda.
        self.cliente = tk.StringVar(value="Consumidor não identificado")
        self.observacao = tk.StringVar()
        self.tipo_retirada = tk.StringVar(value="RETIRADA")
        self.endereco_entrega = tk.StringVar()
        self.data_prevista = tk.StringVar()
        self.observacao_entrega = tk.StringVar()

        # Ajustes gerais.
        self.desconto_tipo = tk.StringVar(value="NENHUM")
        self.desconto_valor = tk.StringVar(value="0")
        self.acrescimo_tipo = tk.StringVar(value="NENHUM")
        self.acrescimo_valor = tk.StringVar(value="0")

        # Pagamento.
        self.pagamento = tk.StringVar(value="PIX")
        self.valor_recebido = tk.StringVar()
        self.parcelas = tk.StringVar(value="1")

        self._montar_cabecalho()

        self.area = ttk.Frame(self, padding=(16, 8, 16, 14))
        self.area.pack(fill="both", expand=True)

        self.desconto_tipo.trace_add(
            "write",
            lambda *_: self._atualizar_preview_ajustes(),
        )
        self.desconto_valor.trace_add(
            "write",
            lambda *_: self._atualizar_preview_ajustes(),
        )
        self.acrescimo_tipo.trace_add(
            "write",
            lambda *_: self._atualizar_preview_ajustes(),
        )
        self.acrescimo_valor.trace_add(
            "write",
            lambda *_: self._atualizar_preview_ajustes(),
        )
        self.pagamento.trace_add(
            "write",
            lambda *_: self._atualizar_campos_pagamento(),
        )
        self.tipo_retirada.trace_add(
            "write",
            lambda *_: self._atualizar_campos_entrega(),
        )

        self.carregar_clientes()
        self.mostrar_inicio()

    # ============================================================
    # Integração com o menu / atalhos
    # ============================================================
    def ao_exibir(self):
        self.carregar_clientes()
        self._atualizar_status_caixa_diario()

        if (
            self.etapa_atual == "PRODUTOS"
            and hasattr(self, "tree_produtos")
        ):
            try:
                if self.tree_produtos.winfo_exists():
                    self.carregar_produtos()
            except Exception:
                pass

    def atalho_f2(self):
        self.mostrar_produtos()
        self._focar(getattr(self, "entry_busca", None))
        return "break"

    def atalho_f4(self):
        if self.etapa_atual == "INICIO":
            self.mostrar_produtos()
        elif self.etapa_atual == "PRODUTOS":
            if (
                getattr(self, "popup_confirmacao_visivel", False)
                and self.produto_selecionado_id
            ):
                self.adicionar_produto()
            else:
                self.ir_dados()
        elif self.etapa_atual == "DADOS":
            self.ir_pagamento()
        elif self.etapa_atual == "PAGAMENTO":
            self.confirmar_venda()
        return "break"

    def atalho_f5(self):
        self.cancelar_venda()
        return "break"

    # ============================================================
    # Cabeçalho
    # ============================================================
    def _montar_cabecalho(self):
        topo = ttk.Frame(self, padding=(18, 14, 18, 6))
        topo.pack(fill="x")

        ttk.Label(
            topo,
            text="Frente de Caixa",
            style="Titulo.TLabel",
        ).pack(side="left")

        self.lbl_caixa_diario = ttk.Label(
            topo,
            text="Caixa Diário: verificando...",
            style="Subtitulo.TLabel",
        )
        self.lbl_caixa_diario.pack(side="left", padx=18)

        ttk.Label(
            topo,
            text=(
                "F2 Produtos  •  F3 Caixa Diário  •  "
                "F4 Avançar/Finalizar  •  F5 Cancelar"
            ),
            style="Subtitulo.TLabel",
        ).pack(side="right")

        self.progresso = ttk.Frame(
            self,
            padding=(18, 0, 18, 8),
        )
        self.progresso.pack(fill="x")

        self.labels_etapa = []
        for texto in [
            "1  Produtos e preços",
            "2  Cliente e dados",
            "3  Pagamento e ajustes",
        ]:
            label = ttk.Label(
                self.progresso,
                text=texto,
                padding=(14, 8),
            )
            label.pack(side="left", padx=(0, 6))
            self.labels_etapa.append(label)

        self._atualizar_status_caixa_diario()

    def _marcar_etapa(self, indice):
        for i, label in enumerate(self.labels_etapa):
            label.configure(
                font=(
                    ("Segoe UI Semibold", 11)
                    if i == indice
                    else ("Segoe UI", 10)
                )
            )

    def _limpar_area(self):
        for widget in self.area.winfo_children():
            widget.destroy()

    def _focar(self, widget):
        if widget is None:
            return
        try:
            if widget.winfo_exists():
                widget.focus_set()
        except Exception:
            pass

    # ============================================================
    # Início
    # ============================================================
    def mostrar_inicio(self):
        self.etapa_atual = "INICIO"
        self._limpar_area()

        for label in self.labels_etapa:
            label.configure(font=("Segoe UI", 10))

        card = ttk.LabelFrame(
            self.area,
            text="Nova venda",
            padding=32,
        )
        card.pack(fill="x", padx=180, pady=(90, 20))

        ttk.Label(
            card,
            text="Comece procurando os produtos da venda.",
            font=("Segoe UI Semibold", 16),
        ).pack(pady=(0, 10))

        ttk.Label(
            card,
            text=(
                "Selecione cada produto, confira o preço de tabela e confirme "
                "o preço que será usado na venda. O preço pode ser aumentado "
                "ou reduzido antes de adicionar o item."
            ),
            justify="center",
            wraplength=760,
        ).pack(pady=(0, 22))

        ttk.Button(
            card,
            text="Procurar produtos (F2)",
            style="Primario.TButton",
            command=self.mostrar_produtos,
        ).pack(ipadx=35, ipady=8)

        ttk.Label(
            self.area,
            text=(
                "F3 abre o Caixa Diário  •  "
                "F4 avança a venda  •  F5 cancela"
            ),
            style="Subtitulo.TLabel",
        ).pack()

    # ============================================================
    # Etapa 1 — Produtos e preço confirmado
    # ============================================================
    def mostrar_produtos(self):
        self.etapa_atual = "PRODUTOS"
        self._marcar_etapa(0)
        self._limpar_area()

        self.popup_confirmacao_visivel = False

        filtros = ttk.LabelFrame(
            self.area,
            text="1 — Procurar produtos",
            padding=12,
        )
        filtros.pack(fill="x")
        filtros.columnconfigure(0, weight=2)
        filtros.columnconfigure(1, weight=1)

        ttk.Label(
            filtros,
            text="Pesquisar por",
        ).grid(row=0, column=0, sticky="w")

        modos = ttk.Frame(filtros)
        modos.grid(row=1, column=0, sticky="w", pady=(0, 6))

        self.botoes_pesquisa = {}

        for texto, modo in (
            ("Pesquisar por nome", "NOME"),
            ("Pesquisar por código", "CODIGO"),
            ("Pesquisar por categoria", "CATEGORIA"),
        ):
            botao = ttk.Button(
                modos,
                text=texto,
                width=19,
                style=(
                    "Primario.TButton"
                    if modo == self.modo_pesquisa.get()
                    else "Secundario.TButton"
                ),
                command=lambda m=modo: self.definir_modo_pesquisa(m),
            )
            botao.pack(side="left", padx=(0, 5))
            self.botoes_pesquisa[modo] = botao

        self.lbl_modo_pesquisa = ttk.Label(
            filtros,
            text="Pesquisa atual: Nome",
            style="Subtitulo.TLabel",
        )
        self.lbl_modo_pesquisa.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 0),
        )

        ttk.Label(
            filtros,
            text="Ordenar",
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=(8, 0),
        )

        self.entry_busca = ttk.Entry(
            filtros,
            textvariable=self.busca_produto,
        )
        self.entry_busca.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(0, 8),
        )
        self.entry_busca.bind(
            "<KeyRelease>",
            self._ao_digitando_busca,
        )
        self.entry_busca.bind(
            "<Down>",
            lambda _e: self.mover_selecao_produto(1),
        )
        self.entry_busca.bind(
            "<Up>",
            lambda _e: self.mover_selecao_produto(-1),
        )
        self.entry_busca.bind(
            "<Return>",
            lambda _e: self.selecionar_produto_atual(),
        )
        self.entry_busca.bind(
            "<KP_Enter>",
            lambda _e: self.selecionar_produto_atual(),
        )

        combo_ordem = ttk.Combobox(
            filtros,
            textvariable=self.ordenacao,
            values=ORDENACOES,
            state="readonly",
            width=18,
        )
        combo_ordem.grid(
            row=2,
            column=2,
            sticky="ew",
        )
        combo_ordem.bind(
            "<<ComboboxSelected>>",
            lambda _: self.carregar_produtos(),
        )

        self.conteudo_produtos = ttk.Frame(self.area)
        self.conteudo_produtos.pack(
            fill="both",
            expand=True,
            pady=(10, 0),
        )

        painel = ttk.Panedwindow(
            self.conteudo_produtos,
            orient="horizontal",
        )
        painel.pack(
            fill="both",
            expand=True,
        )

        esquerda = ttk.LabelFrame(
            painel,
            text="Todos os produtos",
            padding=8,
        )
        direita = ttk.LabelFrame(
            painel,
            text="Itens da venda",
            padding=8,
        )

        painel.add(esquerda, weight=3)
        painel.add(direita, weight=2)

        self.tree_produtos = self._tree(
            esquerda,
            [
                ("id", "ID", 40),
                ("codigo", "Código", 85),
                ("nome", "Produto", 190),
                ("categoria", "Categoria", 110),
                ("preco", "Preço tabela", 95),
                ("estoque", "Estoque", 80),
                ("un", "Un.", 55),
                ("local", "Localização", 180),
            ],
        )

        self.tree_produtos.bind(
            "<ButtonRelease-1>",
            self._clicar_produto_e_abrir,
        )
        self.tree_produtos.bind(
            "<Double-1>",
            self._clicar_produto_e_abrir,
        )
        self.tree_produtos.bind(
            "<Return>",
            lambda _: self.selecionar_produto_atual(),
        )

        legenda = ttk.Frame(esquerda)
        legenda.pack(fill="x", pady=(7, 0))

        ttk.Label(
            legenda,
            text="Digite para filtrar • ↑ ↓ navegam • Enter seleciona o produto",
            style="Subtitulo.TLabel",
        ).pack(side="left")

        ttk.Button(
            legenda,
            text="Selecionar produto",
            style="Primario.TButton",
            command=self.selecionar_produto_atual,
        ).pack(side="right")

        self.tree_carrinho = self._tree(
            direita,
            [
                ("id", "ID", 42),
                ("produto", "Produto", 145),
                ("qtd", "Qtd.", 55),
                ("tabela", "Tabela", 78),
                ("venda", "Venda", 78),
                ("ajuste", "Diferença", 82),
                ("subtotal", "Subtotal", 90),
            ],
        )
        self.tree_carrinho.bind(
            "<Delete>",
            lambda _: self.remover_item(),
        )
        self.tree_carrinho.bind(
            "<Double-1>",
            lambda _: self.editar_preco_item(),
        )

        acoes = ttk.Frame(direita)
        acoes.pack(fill="x", pady=(6, 0))

        ttk.Button(
            acoes,
            text="+ 1",
            command=lambda: self.alterar_quantidade(Decimal("1")),
        ).pack(side="left")

        ttk.Button(
            acoes,
            text="- 1",
            command=lambda: self.alterar_quantidade(Decimal("-1")),
        ).pack(side="left", padx=4)

        ttk.Button(
            acoes,
            text="Editar preço",
            command=self.editar_preco_item,
        ).pack(side="left", padx=(8, 4))

        ttk.Button(
            acoes,
            text="Remover (Del)",
            command=self.remover_item,
        ).pack(side="left")

        rodape = ttk.Frame(
            self.area,
            padding=(0, 10, 0, 0),
        )
        rodape.pack(fill="x")

        self.lbl_total_produtos = ttk.Label(
            rodape,
            font=("Segoe UI Semibold", 14),
        )
        self.lbl_total_produtos.pack(side="right", padx=(10, 0))

        ttk.Button(
            rodape,
            text="Avançar — Cliente e dados (F4)",
            style="Primario.TButton",
            command=self.ir_dados,
        ).pack(side="right")

        ttk.Button(
            rodape,
            text="Cancelar venda (F5)",
            style="Secundario.TButton",
            command=self.cancelar_venda,
        ).pack(side="left")

        # Pequena telinha flutuante sobre a própria aba do Caixa.
        # Continua existindo somente uma janela Tk no sistema.
        self.popup_confirmacao = ttk.LabelFrame(
            self.conteudo_produtos,
            text="Confirmar produto",
            padding=14,
        )
        self.popup_confirmacao.columnconfigure(1, weight=1)

        ttk.Label(
            self.popup_confirmacao,
            text="Preço:",
            font=("Segoe UI Semibold", 11),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=(4, 10),
        )

        self.entry_preco_venda = ttk.Entry(
            self.popup_confirmacao,
            textvariable=self.preco_venda,
            width=18,
            font=("Segoe UI", 12),
        )
        self.entry_preco_venda.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(4, 10),
        )
        self.entry_preco_venda.bind(
            "<Return>",
            lambda _: self._focar(self.entry_qtd),
        )

        ttk.Label(
            self.popup_confirmacao,
            text="Quantidade:",
            font=("Segoe UI Semibold", 11),
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=(0, 12),
        )

        self.entry_qtd = ttk.Entry(
            self.popup_confirmacao,
            textvariable=self.qtd_produto,
            width=18,
            font=("Segoe UI", 12),
        )
        self.entry_qtd.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(0, 12),
        )
        self.entry_qtd.bind(
            "<Return>",
            lambda _: self.adicionar_produto(),
        )

        botoes_popup = ttk.Frame(self.popup_confirmacao)
        botoes_popup.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(2, 0),
        )

        ttk.Button(
            botoes_popup,
            text="Cancelar",
            style="Secundario.TButton",
            command=self.fechar_confirmacao_produto,
        ).pack(side="left")

        ttk.Button(
            botoes_popup,
            text="Adicionar",
            style="Primario.TButton",
            command=self.adicionar_produto,
        ).pack(side="right")

        self.produto_selecionado_id = None
        self.preco_venda.set("")
        self.qtd_produto.set("1")

        self.carregar_produtos()
        self.atualizar_carrinho()
        self._focar(self.entry_busca)

    def fechar_confirmacao_produto(self):
        self.produto_selecionado_id = None
        self.preco_venda.set("")
        self.qtd_produto.set("1")
        self.popup_confirmacao_visivel = False

        if hasattr(self, "popup_confirmacao"):
            self.popup_confirmacao.place_forget()

        self._focar(getattr(self, "entry_busca", None))

    def _tree(self, parent, colunas):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            frame,
            columns=[c[0] for c in colunas],
            show="headings",
            selectmode="browse",
            takefocus=True,
        )

        for nome, titulo, largura in colunas:
            tree.heading(nome, text=titulo)
            tree.column(
                nome,
                width=largura,
                minwidth=40,
                anchor="w",
                stretch=True,
            )

        sy = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview,
        )
        sx = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=tree.xview,
        )

        tree.configure(
            yscrollcommand=sy.set,
            xscrollcommand=sx.set,
        )

        tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        return tree

    def definir_modo_pesquisa(self, modo):
        self.modo_pesquisa.set(modo)

        nomes = {
            "NOME": "Nome",
            "CODIGO": "Código",
            "CATEGORIA": "Categoria",
        }

        if hasattr(self, "botoes_pesquisa"):
            for chave, botao in self.botoes_pesquisa.items():
                botao.configure(
                    style=(
                        "Primario.TButton"
                        if chave == modo
                        else "Secundario.TButton"
                    )
                )

        if hasattr(self, "lbl_modo_pesquisa"):
            self.lbl_modo_pesquisa.config(
                text=f"Pesquisa atual: {nomes.get(modo, 'Nome')}"
            )

        self.produto_selecionado_id = None
        self.preco_venda.set("")

        self.busca_produto.set("")
        self.carregar_produtos()
        self._focar(getattr(self, "entry_busca", None))

    def _ao_digitando_busca(self, evento=None):
        """
        Filtra a lista imediatamente enquanto o usuário digita.

        As teclas de navegação são tratadas separadamente para não recarregar
        toda a lista ao usar as setas.
        """
        if evento is not None and evento.keysym in {
            "Up",
            "Down",
            "Return",
            "KP_Enter",
            "Left",
            "Right",
            "Home",
            "End",
            "Page_Up",
            "Page_Down",
        }:
            return

        self.carregar_produtos(
            selecionar_primeiro=True,
        )

    def _marcar_item_produto(self, item_tree):
        if not item_tree:
            return None

        self.tree_produtos.selection_set(item_tree)
        self.tree_produtos.focus(item_tree)
        self.tree_produtos.see(item_tree)
        return item_tree

    def marcar_primeiro_produto(self):
        itens = self.tree_produtos.get_children()
        if not itens:
            self.tree_produtos.selection_remove(
                self.tree_produtos.selection()
            )
            return None
        return self._marcar_item_produto(itens[0])

    def mover_selecao_produto(self, direcao):
        """
        Move somente o destaque da lista com ↑/↓.

        O foco de digitação continua no campo de pesquisa, então é possível
        alternar entre digitar e navegar sem usar o mouse.
        """
        itens = list(self.tree_produtos.get_children())
        if not itens:
            return "break"

        atual = self.tree_produtos.focus()
        if atual not in itens:
            selecionados = self.tree_produtos.selection()
            atual = selecionados[0] if selecionados else None

        if atual in itens:
            indice = itens.index(atual)
            indice = max(
                0,
                min(len(itens) - 1, indice + int(direcao)),
            )
        else:
            indice = 0 if direcao >= 0 else len(itens) - 1

        self._marcar_item_produto(itens[indice])

        # Mantém o cursor no campo de pesquisa.
        self._focar(self.entry_busca)
        return "break"

    def selecionar_primeiro_resultado(self):
        itens = self.tree_produtos.get_children()
        if not itens:
            messagebox.showinfo(
                "Produtos",
                "Nenhum produto encontrado para a pesquisa atual.",
            )
            return

        self._abrir_confirmacao_por_item_tree(itens[0])

    def _clicar_produto_e_abrir(self, evento):
        """
        Seleciona usando a linha identificada pelo próprio clique.

        Não dependemos de Treeview.selection(), que era o ponto que estava
        falhando em alguns computadores.
        """
        linha = self.tree_produtos.identify_row(evento.y)
        regiao = self.tree_produtos.identify_region(evento.x, evento.y)

        if not linha or regiao not in {"cell", "tree"}:
            return

        self._abrir_confirmacao_por_item_tree(linha)

    # Compatibilidade com código/atalhos das versões anteriores.
    def _clicar_produto(self, evento):
        self._clicar_produto_e_abrir(evento)

    def _duplo_clique_produto(self, evento):
        self._clicar_produto_e_abrir(evento)

    def selecionar_produto_atual(self):
        linha = self.tree_produtos.focus()

        if not linha:
            selecionados = self.tree_produtos.selection()
            linha = selecionados[0] if selecionados else None

        if not linha:
            self.selecionar_primeiro_resultado()
            return

        self._abrir_confirmacao_por_item_tree(linha)

    def _abrir_confirmacao_por_item_tree(self, item_tree):
        try:
            valores = self.tree_produtos.item(
                item_tree,
                "values",
            )

            if not valores:
                return

            id_produto = int(valores[0])

            self.tree_produtos.selection_set(item_tree)
            self.tree_produtos.focus(item_tree)
            self.tree_produtos.see(item_tree)

            self._abrir_confirmacao_produto(id_produto)

        except Exception as erro:
            mostrar_erro(erro)

    def _abrir_confirmacao_produto(self, id_produto):
        try:
            produto = next(
                (
                    p
                    for p in self.produtos_cache
                    if int(p["id_produto"]) == int(id_produto)
                ),
                None,
            )

            if produto is None:
                produto = obter_produto(id_produto)

            if not produto:
                raise ValueError("Produto não encontrado.")

            estoque = Decimal(produto["quantidade_estoque"])

            if estoque <= 0:
                raise ValueError(
                    f"{produto['nome']} está sem estoque disponível."
                )

            self.produto_selecionado_id = int(id_produto)

            preco_tabela = Decimal(produto["preco"])
            self.preco_venda.set(f"{preco_tabela:.2f}")
            self.qtd_produto.set("1")

            # A telinha permanece propositalmente simples: só preço e quantidade.
            self.popup_confirmacao.place(
                relx=0.5,
                rely=0.46,
                anchor="center",
                width=340,
                height=175,
            )
            self.popup_confirmacao.lift()
            self.popup_confirmacao_visivel = True

            self._focar(self.entry_preco_venda)
            self.entry_preco_venda.selection_range(0, "end")

        except Exception as erro:
            mostrar_erro(erro)

    def carregar_produtos(self, selecionar_primeiro=True):
        if not hasattr(self, "tree_produtos"):
            return

        try:
            if not self.tree_produtos.winfo_exists():
                return
        except Exception:
            return

        try:
            termo = self.busca_produto.get().strip().lower()
            produtos = listar_produtos(apenas_ativos=True)

            produtos = filtrar_produtos(
                produtos,
                termo,
                self.modo_pesquisa.get(),
            )

            ordem = self.ordenacao.get()

            if ordem == "Nome Z-A":
                produtos.sort(
                    key=lambda p: (p["nome"] or "").lower(),
                    reverse=True,
                )
            elif ordem == "Menor preço":
                produtos.sort(
                    key=lambda p: Decimal(p["preco"]),
                )
            elif ordem == "Maior preço":
                produtos.sort(
                    key=lambda p: Decimal(p["preco"]),
                    reverse=True,
                )
            elif ordem == "Maior estoque":
                produtos.sort(
                    key=lambda p: Decimal(p["quantidade_estoque"]),
                    reverse=True,
                )
            elif ordem == "Menor estoque":
                produtos.sort(
                    key=lambda p: Decimal(p["quantidade_estoque"]),
                )
            elif ordem == "Categoria":
                produtos.sort(
                    key=lambda p: (
                        (p.get("categoria") or "").lower(),
                        (p["nome"] or "").lower(),
                    )
                )
            else:
                produtos.sort(
                    key=lambda p: (p["nome"] or "").lower(),
                )

            self.produtos_cache = produtos
            limpar_tree(self.tree_produtos)

            for p in produtos:
                if p.get("tipo_localizacao") == "EXTERNA":
                    local = (
                        p.get("descricao_localizacao")
                        or "Fora da loja"
                    )
                else:
                    partes = []

                    if p.get("corredor"):
                        partes.append(f"C.{p['corredor']}")

                    if p.get("prateleira"):
                        partes.append(f"P.{p['prateleira']}")

                    local = " / ".join(partes) or "-"

                self.tree_produtos.insert(
                    "",
                    "end",
                    values=(
                        p["id_produto"],
                        p.get("codigo") or f"PRD-{int(p['id_produto']):06d}",
                        p["nome"],
                        p.get("categoria") or "",
                        moeda(p["preco"]),
                        p["quantidade_estoque"],
                        p["unidade_medida"],
                        local,
                    ),
                )

            if selecionar_primeiro:
                self.marcar_primeiro_produto()

        except Exception as erro:
            mostrar_erro(erro)

    def _produto_selecionado(self, _evento=None):
        """Compatibilidade: abre a confirmação do item atualmente focado."""
        self.selecionar_produto_atual()

    def _decimal_positivo(self, valor, campo):
        try:
            numero = Decimal(str(valor).replace(",", "."))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{campo} deve ser um número válido.")

        if numero <= 0:
            raise ValueError(f"{campo} deve ser maior que zero.")

        return numero

    def adicionar_produto(self):
        if not self.produto_selecionado_id:
            messagebox.showinfo(
                "Produtos",
                "Selecione um produto e confirme o preço da venda.",
            )
            return

        try:
            id_produto = self.produto_selecionado_id
            quantidade = self._decimal_positivo(
                self.qtd_produto.get(),
                "Quantidade",
            )
            preco_venda = self._decimal_positivo(
                self.preco_venda.get(),
                "Preço da venda",
            )

            produto = obter_produto(id_produto)
            preco_tabela = Decimal(produto["preco"])
            estoque = Decimal(produto["quantidade_estoque"])

            existente = next(
                (
                    i
                    for i in self.carrinho
                    if i["id_produto"] == id_produto
                ),
                None,
            )

            total_qtd = (
                quantidade
                + (
                    existente["quantidade"]
                    if existente
                    else Decimal("0")
                )
            )

            if total_qtd > estoque:
                raise ValueError(
                    f"Estoque insuficiente. Disponível: "
                    f"{estoque} {produto['unidade_medida']}."
                )

            if existente:
                existente["quantidade"] = total_qtd
                existente["preco_tabela"] = preco_tabela
                existente["preco"] = preco_venda
            else:
                self.carrinho.append(
                    {
                        "id_produto": id_produto,
                        "nome": produto["nome"],
                        "quantidade": quantidade,
                        "preco_tabela": preco_tabela,
                        "preco": preco_venda,
                        "unidade_medida": produto["unidade_medida"],
                    }
                )

            self.qtd_produto.set("1")
            self.produto_selecionado_id = None
            self.preco_venda.set("")

            self.atualizar_carrinho()

            self.popup_confirmacao_visivel = False
            if hasattr(self, "popup_confirmacao"):
                self.popup_confirmacao.place_forget()

            self._focar(self.entry_busca)

        except Exception as erro:
            mostrar_erro(erro)

    def editar_preco_item(self):
        selecionado = self.tree_carrinho.selection()
        if not selecionado:
            messagebox.showinfo(
                "Preço do item",
                "Selecione um item do carrinho.",
            )
            return

        try:
            id_produto = int(
                self.tree_carrinho.item(
                    selecionado[0],
                    "values",
                )[0]
            )
            item = next(
                i
                for i in self.carrinho
                if i["id_produto"] == id_produto
            )

            novo = solicitar_texto_enter(
                self,
                "Confirmar preço do item",
                (
                    f"{item['nome']}\n\n"
                    f"Preço de tabela: {moeda(item['preco_tabela'])}\n"
                    f"Preço atual da venda: {moeda(item['preco'])}\n\n"
                    "Digite o novo preço da venda:"
                ),
                valor_inicial=f"{item['preco']:.2f}",
            )

            if novo is None:
                return

            item["preco"] = self._decimal_positivo(
                novo,
                "Preço da venda",
            )
            self.atualizar_carrinho()

        except Exception as erro:
            mostrar_erro(erro)

    def alterar_quantidade(self, delta):
        selecionado = self.tree_carrinho.selection()
        if not selecionado:
            return

        try:
            id_produto = int(
                self.tree_carrinho.item(
                    selecionado[0],
                    "values",
                )[0]
            )
            item = next(
                i
                for i in self.carrinho
                if i["id_produto"] == id_produto
            )

            nova = item["quantidade"] + delta

            if nova <= 0:
                self.carrinho.remove(item)
            else:
                produto = obter_produto(id_produto)

                if nova > Decimal(produto["quantidade_estoque"]):
                    raise ValueError(
                        "Quantidade maior que o estoque disponível."
                    )

                item["quantidade"] = nova

            self.atualizar_carrinho()

        except Exception as erro:
            mostrar_erro(erro)

    def remover_item(self):
        selecionado = self.tree_carrinho.selection()
        if not selecionado:
            return

        id_produto = int(
            self.tree_carrinho.item(
                selecionado[0],
                "values",
            )[0]
        )

        self.carrinho = [
            i
            for i in self.carrinho
            if i["id_produto"] != id_produto
        ]
        self.atualizar_carrinho()

    def subtotal_tabela(self):
        return sum(
            (
                i["preco_tabela"] * i["quantidade"]
                for i in self.carrinho
            ),
            Decimal("0.00"),
        )

    def subtotal(self):
        return sum(
            (
                i["preco"] * i["quantidade"]
                for i in self.carrinho
            ),
            Decimal("0.00"),
        )

    def atualizar_carrinho(self):
        if not hasattr(self, "tree_carrinho"):
            return

        try:
            if not self.tree_carrinho.winfo_exists():
                return
        except Exception:
            return

        limpar_tree(self.tree_carrinho)

        for item in self.carrinho:
            subtotal = item["preco"] * item["quantidade"]
            diferenca = item["preco"] - item["preco_tabela"]

            if diferenca > 0:
                texto_diferenca = f"+{moeda(diferenca)}"
            elif diferenca < 0:
                texto_diferenca = f"-{moeda(abs(diferenca))}"
            else:
                texto_diferenca = "Sem ajuste"

            self.tree_carrinho.insert(
                "",
                "end",
                values=(
                    item["id_produto"],
                    item["nome"],
                    item["quantidade"],
                    moeda(item["preco_tabela"]),
                    moeda(item["preco"]),
                    texto_diferenca,
                    moeda(subtotal),
                ),
            )

        if hasattr(self, "lbl_total_produtos"):
            tabela = self.subtotal_tabela()
            negociado = self.subtotal()

            self.lbl_total_produtos.config(
                text=(
                    f"Tabela: {moeda(tabela)}   •   "
                    f"Subtotal negociado: {moeda(negociado)}"
                )
            )

    # ============================================================
    # Etapa 2 — Cliente e observações
    # ============================================================
    def ir_dados(self):
        if not self.carrinho:
            messagebox.showwarning(
                "Venda",
                "Adicione pelo menos um produto antes de avançar.",
            )
            return

        self.etapa_atual = "DADOS"
        self._marcar_etapa(1)
        self._limpar_area()

        quadro = ttk.LabelFrame(
            self.area,
            text="2 — Cliente, observações e entrega",
            padding=20,
        )
        quadro.pack(
            fill="x",
            padx=80,
            pady=(30, 10),
        )
        quadro.columnconfigure(1, weight=1)

        ttk.Label(
            quadro,
            text="Cliente",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=8,
        )

        self.combo_cliente = ttk.Combobox(
            quadro,
            textvariable=self.cliente,
            state="readonly",
        )
        self.combo_cliente.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=8,
        )
        self.combo_cliente.bind(
            "<<ComboboxSelected>>",
            lambda _: self._cliente_selecionado(),
        )
        self.combo_cliente.bind(
            "<Return>",
            lambda _: self._focar(self.entry_observacao),
        )

        ttk.Label(
            quadro,
            text="Observações da venda",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=8,
        )

        self.entry_observacao = ttk.Entry(
            quadro,
            textvariable=self.observacao,
        )
        self.entry_observacao.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=8,
        )
        self.entry_observacao.bind(
            "<Return>",
            lambda _: self.ir_pagamento(),
        )

        ttk.Label(
            quadro,
            text="Retirada / entrega",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=8,
        )

        escolha = ttk.Frame(quadro)
        escolha.grid(
            row=2,
            column=1,
            sticky="w",
            pady=8,
        )

        ttk.Radiobutton(
            escolha,
            text="Retirada na loja",
            variable=self.tipo_retirada,
            value="RETIRADA",
        ).pack(side="left")

        ttk.Radiobutton(
            escolha,
            text="Entrega",
            variable=self.tipo_retirada,
            value="ENTREGA",
        ).pack(side="left", padx=16)

        self.entrega_frame = ttk.LabelFrame(
            quadro,
            text="Dados da entrega",
            padding=12,
        )
        self.entrega_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )
        self.entrega_frame.columnconfigure(1, weight=1)

        ttk.Label(
            self.entrega_frame,
            text="Endereço",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=5,
        )

        self.entry_endereco = ttk.Entry(
            self.entrega_frame,
            textvariable=self.endereco_entrega,
        )
        self.entry_endereco.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=5,
        )

        ttk.Label(
            self.entrega_frame,
            text="Data prevista (AAAA-MM-DD)",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=5,
        )

        ttk.Entry(
            self.entrega_frame,
            textvariable=self.data_prevista,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=5,
        )

        ttk.Label(
            self.entrega_frame,
            text="Observação da entrega",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=5,
        )

        entry_obs_entrega = ttk.Entry(
            self.entrega_frame,
            textvariable=self.observacao_entrega,
        )
        entry_obs_entrega.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=5,
        )
        entry_obs_entrega.bind(
            "<Return>",
            lambda _: self.ir_pagamento(),
        )

        ttk.Label(
            self.area,
            text=(
                f"Subtotal de tabela: {moeda(self.subtotal_tabela())}   •   "
                f"Subtotal negociado: {moeda(self.subtotal())}"
            ),
            font=("Segoe UI Semibold", 14),
        ).pack(pady=12)

        botoes = ttk.Frame(self.area)
        botoes.pack(fill="x", padx=80)

        ttk.Button(
            botoes,
            text="← Voltar aos produtos",
            command=self.mostrar_produtos,
        ).pack(side="left")

        ttk.Button(
            botoes,
            text="Continuar para pagamento (Enter / F4)",
            style="Primario.TButton",
            command=self.ir_pagamento,
        ).pack(side="right")

        self.carregar_clientes()
        self._atualizar_campos_entrega()
        self._focar(self.combo_cliente)

    def carregar_clientes(self):
        try:
            clientes = listar_clientes()
            self.clientes_cache = clientes

            valores = ["Consumidor não identificado"] + [
                f"{c['id_cliente']} - {c['nome']}"
                for c in clientes
            ]

            if hasattr(self, "combo_cliente"):
                self.combo_cliente["values"] = valores

                if not self.cliente.get():
                    self.cliente.set(
                        "Consumidor não identificado"
                    )

        except Exception as erro:
            mostrar_erro(erro)

    def _cliente_selecionado(self):
        if self.tipo_retirada.get() != "ENTREGA":
            return

        id_cliente = self._id_cliente()
        if not id_cliente:
            return

        try:
            cliente = obter_cliente(id_cliente)

            if cliente and not self.endereco_entrega.get().strip():
                partes = [
                    cliente.get("endereco"),
                    cliente.get("cidade"),
                    cliente.get("uf"),
                    cliente.get("cep"),
                ]

                self.endereco_entrega.set(
                    " - ".join(
                        str(p)
                        for p in partes
                        if p
                    )
                )
        except Exception:
            pass

    def _id_cliente(self):
        valor = self.cliente.get()

        if (
            not valor
            or valor == "Consumidor não identificado"
        ):
            return None

        return parse_combo_id(valor)

    def _atualizar_campos_entrega(self):
        if not hasattr(self, "entrega_frame"):
            return

        try:
            if not self.entrega_frame.winfo_exists():
                return
        except Exception:
            return

        estado = (
            "normal"
            if self.tipo_retirada.get() == "ENTREGA"
            else "disabled"
        )

        for widget in self.entrega_frame.winfo_children():
            if isinstance(
                widget,
                (ttk.Entry, ttk.Combobox),
            ):
                widget.configure(state=estado)

        if estado == "normal":
            self._cliente_selecionado()

    # Compatibilidade com versões anteriores que chamavam esta etapa.
    def ir_desconto(self):
        self.ir_pagamento()

    # ============================================================
    # Etapa 3 — Ajustes gerais + pagamento
    # ============================================================
    def ir_pagamento(self):
        if (
            self.tipo_retirada.get() == "ENTREGA"
            and not self.endereco_entrega.get().strip()
        ):
            messagebox.showwarning(
                "Entrega",
                "Informe o endereço da entrega antes de continuar.",
            )
            return

        self.etapa_atual = "PAGAMENTO"
        self._marcar_etapa(2)
        self._limpar_area()

        quadro = ttk.LabelFrame(
            self.area,
            text="3 — Pagamento e ajustes gerais da venda",
            padding=18,
        )
        quadro.pack(
            fill="x",
            padx=55,
            pady=(18, 10),
        )
        quadro.columnconfigure(0, weight=1)
        quadro.columnconfigure(1, weight=1)

        ttk.Label(
            quadro,
            text=(
                f"Subtotal de tabela: {moeda(self.subtotal_tabela())}     "
                f"Subtotal com preços confirmados: {moeda(self.subtotal())}"
            ),
            font=("Segoe UI Semibold", 14),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 14),
        )

        ajustes = ttk.LabelFrame(
            quadro,
            text="Desconto ou acréscimo geral",
            padding=12,
        )
        ajustes.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 12),
        )
        ajustes.columnconfigure(0, weight=1)
        ajustes.columnconfigure(1, weight=1)

        desconto = ttk.LabelFrame(
            ajustes,
            text="Desconto geral",
            padding=10,
        )
        desconto.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6),
        )
        desconto.columnconfigure(0, weight=1)

        ttk.Radiobutton(
            desconto,
            text="Sem desconto",
            variable=self.desconto_tipo,
            value="NENHUM",
        ).grid(row=0, column=0, sticky="w")

        ttk.Radiobutton(
            desconto,
            text="Valor em R$",
            variable=self.desconto_tipo,
            value="VALOR",
        ).grid(row=1, column=0, sticky="w")

        ttk.Radiobutton(
            desconto,
            text="Porcentagem %",
            variable=self.desconto_tipo,
            value="PERCENTUAL",
        ).grid(row=2, column=0, sticky="w")

        self.entry_desconto_geral = ttk.Entry(
            desconto,
            textvariable=self.desconto_valor,
        )
        self.entry_desconto_geral.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        self.entry_desconto_geral.bind(
            "<Return>",
            lambda _: self._focar(self.entry_acrescimo_geral),
        )

        acrescimo = ttk.LabelFrame(
            ajustes,
            text="Acréscimo geral",
            padding=10,
        )
        acrescimo.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0),
        )
        acrescimo.columnconfigure(0, weight=1)

        ttk.Radiobutton(
            acrescimo,
            text="Sem acréscimo",
            variable=self.acrescimo_tipo,
            value="NENHUM",
        ).grid(row=0, column=0, sticky="w")

        ttk.Radiobutton(
            acrescimo,
            text="Valor em R$",
            variable=self.acrescimo_tipo,
            value="VALOR",
        ).grid(row=1, column=0, sticky="w")

        ttk.Radiobutton(
            acrescimo,
            text="Porcentagem %",
            variable=self.acrescimo_tipo,
            value="PERCENTUAL",
        ).grid(row=2, column=0, sticky="w")

        self.entry_acrescimo_geral = ttk.Entry(
            acrescimo,
            textvariable=self.acrescimo_valor,
        )
        self.entry_acrescimo_geral.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        self.entry_acrescimo_geral.bind(
            "<Return>",
            lambda _: self._focar(self.combo_pagamento),
        )

        self.lbl_preview_ajustes = ttk.Label(
            quadro,
            font=("Segoe UI Semibold", 14),
        )
        self.lbl_preview_ajustes.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 4),
        )

        self.lbl_erro_ajustes = ttk.Label(quadro)
        self.lbl_erro_ajustes.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        pagamento = ttk.LabelFrame(
            quadro,
            text="Forma de pagamento",
            padding=12,
        )
        pagamento.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        pagamento.columnconfigure(1, weight=1)

        ttk.Label(
            pagamento,
            text="Pagamento",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=7,
        )

        self.combo_pagamento = ttk.Combobox(
            pagamento,
            textvariable=self.pagamento,
            values=FORMAS_PAGAMENTO,
            state="readonly",
        )
        self.combo_pagamento.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=7,
        )
        self.combo_pagamento.bind(
            "<<ComboboxSelected>>",
            lambda _: self._pagamento_selecionado(),
        )
        self.combo_pagamento.bind(
            "<Return>",
            lambda _: self._avancar_pagamento_teclado(),
        )

        ttk.Label(
            pagamento,
            text="Valor recebido",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=7,
        )

        self.entry_recebido = ttk.Entry(
            pagamento,
            textvariable=self.valor_recebido,
        )
        self.entry_recebido.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=7,
        )
        self.entry_recebido.bind(
            "<Return>",
            lambda _: self.confirmar_venda(),
        )

        ttk.Label(
            pagamento,
            text="Parcelas do crediário",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=7,
        )

        self.combo_parcelas = ttk.Combobox(
            pagamento,
            textvariable=self.parcelas,
            values=["1", "2"],
            state="readonly",
        )
        self.combo_parcelas.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=7,
        )
        self.combo_parcelas.bind(
            "<Return>",
            lambda _: self.confirmar_venda(),
        )

        cliente_nome = (
            self.cliente.get()
            or "Consumidor não identificado"
        )

        ttk.Label(
            quadro,
            text=(
                f"Cliente: {cliente_nome}\n"
                f"Observação: {self.observacao.get() or '-'}"
            ),
            justify="left",
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 0),
        )

        botoes = ttk.Frame(self.area)
        botoes.pack(fill="x", padx=55)

        ttk.Button(
            botoes,
            text="← Voltar aos dados",
            command=self.ir_dados,
        ).pack(side="left")

        ttk.Button(
            botoes,
            text="FINALIZAR VENDA (Enter / F4)",
            style="Primario.TButton",
            command=self.confirmar_venda,
        ).pack(side="right")

        self._atualizar_preview_ajustes()
        self._atualizar_campos_pagamento()

        if self.desconto_tipo.get() != "NENHUM":
            self._focar(self.entry_desconto_geral)
        elif self.acrescimo_tipo.get() != "NENHUM":
            self._focar(self.entry_acrescimo_geral)
        else:
            self._focar(self.combo_pagamento)

    def _totais_calculados(self):
        desconto_valor = (
            self.desconto_valor.get().strip()
            or "0"
        )
        acrescimo_valor = (
            self.acrescimo_valor.get().strip()
            or "0"
        )

        return calcular_totais(
            self.subtotal(),
            self.desconto_tipo.get(),
            desconto_valor,
            self.acrescimo_tipo.get(),
            acrescimo_valor,
        )

    def _atualizar_preview_ajustes(self):
        if not hasattr(self, "lbl_preview_ajustes"):
            return

        try:
            if not self.lbl_preview_ajustes.winfo_exists():
                return
        except Exception:
            return

        try:
            dados = self._totais_calculados()

            self.lbl_preview_ajustes.config(
                text=(
                    f"Subtotal: {moeda(dados['subtotal'])}   •   "
                    f"Desconto geral: {moeda(dados['desconto'])}   •   "
                    f"Acréscimo geral: {moeda(dados['acrescimo'])}   •   "
                    f"TOTAL FINAL: {moeda(dados['total'])}"
                )
            )
            self.lbl_erro_ajustes.config(text="")

            estado_desconto = (
                "disabled"
                if self.desconto_tipo.get() == "NENHUM"
                else "normal"
            )
            estado_acrescimo = (
                "disabled"
                if self.acrescimo_tipo.get() == "NENHUM"
                else "normal"
            )

            self.entry_desconto_geral.configure(
                state=estado_desconto
            )
            self.entry_acrescimo_geral.configure(
                state=estado_acrescimo
            )

        except Exception as erro:
            self.lbl_erro_ajustes.config(text=str(erro))

    # Compatibilidade com chamadas antigas.
    def _atualizar_preview_desconto(self):
        self._atualizar_preview_ajustes()

    def _atualizar_preview_acrescimo(self):
        self._atualizar_preview_ajustes()

    def _atualizar_campos_pagamento(self):
        if not hasattr(self, "entry_recebido"):
            return

        try:
            if not self.entry_recebido.winfo_exists():
                return
        except Exception:
            return

        forma = self.pagamento.get()

        self.entry_recebido.configure(
            state=(
                "normal"
                if forma == "DINHEIRO"
                else "disabled"
            )
        )

        self.combo_parcelas.configure(
            state=(
                "readonly"
                if forma == "CREDIARIO"
                else "disabled"
            )
        )

    def _pagamento_selecionado(self):
        self._atualizar_campos_pagamento()

        try:
            total = self._totais_calculados()["total"]
        except Exception:
            total = None

        if self.pagamento.get() == "DINHEIRO":
            if (
                total is not None
                and not self.valor_recebido.get().strip()
            ):
                self.valor_recebido.set(f"{total:.2f}")

            self._focar(self.entry_recebido)

        elif self.pagamento.get() == "CREDIARIO":
            self._focar(self.combo_parcelas)

    def _avancar_pagamento_teclado(self):
        forma = self.pagamento.get()

        if forma == "DINHEIRO":
            self._focar(self.entry_recebido)
        elif forma == "CREDIARIO":
            self._focar(self.combo_parcelas)
        else:
            self.confirmar_venda()

    def confirmar_venda(self):
        try:
            totais = self._totais_calculados()
            forma = self.pagamento.get()
            id_cliente = self._id_cliente()

            if forma == "CREDIARIO" and not id_cliente:
                raise ValueError(
                    "Selecione um cliente identificado "
                    "para usar o crediário."
                )

            itens = [
                {
                    "id_produto": item["id_produto"],
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco"],
                }
                for item in self.carrinho
            ]

            resultado = finalizar_venda(
                self.funcionario["id_funcionario"],
                itens,
                forma,
                id_cliente=id_cliente,
                valor_recebido=(
                    self.valor_recebido.get()
                    if forma == "DINHEIRO"
                    else None
                ),
                parcelas=int(
                    self.parcelas.get()
                    or 1
                ),
                tipo_retirada=self.tipo_retirada.get(),
                endereco_entrega=self.endereco_entrega.get(),
                data_prevista=(
                    self.data_prevista.get().strip()
                    or None
                ),
                observacao_entrega=self.observacao_entrega.get(),
                observacao_venda=self.observacao.get(),
                desconto_tipo=totais["desconto_tipo"],
                desconto_valor=totais["desconto_referencia"],
                acrescimo_tipo=totais["acrescimo_tipo"],
                acrescimo_valor=totais["acrescimo_referencia"],
            )

            mensagem = (
                f"Venda #{resultado['id_venda']} finalizada "
                f"com sucesso.\n\n"
                f"Subtotal negociado: "
                f"{moeda(resultado['subtotal'])}\n"
                f"Desconto geral: "
                f"{moeda(resultado['desconto'])}\n"
                f"Acréscimo geral: "
                f"{moeda(resultado['acrescimo'])}\n"
                f"Total: {moeda(resultado['total'])}"
            )

            if forma == "DINHEIRO":
                mensagem += (
                    f"\nTroco: {moeda(resultado['troco'])}"
                )

            gerar = confirmar_com_enter(
                self,
                "Venda finalizada",
                mensagem + "\n\nGerar comprovante em PDF?",
            )

            if gerar:
                caminho = gerar_comprovante(
                    resultado["id_venda"]
                )
                messagebox.showinfo(
                    "Comprovante",
                    f"Arquivo criado em:\n{caminho.resolve()}",
                )

            self._resetar_estado()
            self._atualizar_status_caixa_diario()
            self.mostrar_produtos()

        except Exception as erro:
            mostrar_erro(erro)

    def _atualizar_status_caixa_diario(self):
        if not hasattr(self, "lbl_caixa_diario"):
            return

        try:
            caixa = obter_caixa_hoje()

            if not caixa:
                texto = "Caixa Diário: NÃO ABERTO (F3)"
            elif caixa["status"] == "ABERTO":
                texto = (
                    "Caixa Diário: ABERTO • "
                    f"Abertura {moeda(caixa['valor_abertura'])}"
                )
            else:
                texto = "Caixa Diário: FECHADO"

            self.lbl_caixa_diario.config(text=texto)

        except Exception:
            self.lbl_caixa_diario.config(
                text="Caixa Diário: indisponível"
            )

    # ============================================================
    # Cancelamento / fechamento
    # ============================================================
    def cancelar_venda(self):
        if (
            not self.carrinho
            and self.etapa_atual in {"INICIO", "PRODUTOS"}
        ):
            self._resetar_estado()
            self.mostrar_inicio()
            return

        if not confirmar_com_enter(
            self,
            "Cancelar venda",
            "Apagar todos os itens e dados da venda atual?",
        ):
            return

        self._resetar_estado()
        self.mostrar_produtos()

    def limpar_venda(self):
        self.cancelar_venda()

    def pode_fechar(self):
        if (
            self.carrinho
            or self.etapa_atual not in {"INICIO", "PRODUTOS"}
        ):
            return confirmar_com_enter(
                self,
                "Venda em andamento",
                (
                    "Existe uma venda em andamento. "
                    "Fechar a aba e descartar essa venda?"
                ),
            )

        return True

    def _resetar_estado(self):
        self.carrinho.clear()
        self.produto_selecionado_id = None

        self.busca_produto.set("")
        self.modo_pesquisa.set("NOME")
        self.ordenacao.set("Nome A-Z")
        self.qtd_produto.set("1")
        self.preco_venda.set("")

        self.cliente.set("Consumidor não identificado")
        self.observacao.set("")
        self.tipo_retirada.set("RETIRADA")
        self.endereco_entrega.set("")
        self.data_prevista.set("")
        self.observacao_entrega.set("")

        self.desconto_tipo.set("NENHUM")
        self.desconto_valor.set("0")
        self.acrescimo_tipo.set("NENHUM")
        self.acrescimo_valor.set("0")

        self.pagamento.set("PIX")
        self.valor_recebido.set("")
        self.parcelas.set("1")
