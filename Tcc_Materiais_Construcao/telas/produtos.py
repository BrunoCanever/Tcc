import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.produto_funcoes import (
    cadastrar_produto, listar_produtos, buscar_produto,
    atualizar_produto, excluir_produto, UNIDADES
)
from funcoes.categoria_funcoes import listar_categorias
from funcoes.fornecedor_funcoes import listar_fornecedores
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro, parse_combo_id,
    vincular_fluxo_enter, vincular_enter_acao, confirmar_com_enter,
)


class TelaProdutos(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.id_selecionado = None

        nomes = [
            "nome", "descricao", "preco", "estoque", "minimo",
            "corredor", "prateleira", "descricao_localizacao"
        ]
        self.vars = {n: tk.StringVar() for n in nomes}
        self.unidade = tk.StringVar(value="UN")
        self.tipo_localizacao = tk.StringVar(value="INTERNA")
        self.ativo = tk.BooleanVar(value=True)
        self.busca = tk.StringVar()

        form = ttk.LabelFrame(self, text="Produto", padding=12)
        form.pack(fill="x", padx=10, pady=10)
        for c in range(4):
            form.columnconfigure(c, weight=1)

        campos = [
            ("Nome*", "nome", 0, 0),
            ("Descrição", "descricao", 0, 1),
            ("Preço*", "preco", 0, 2),
            ("Estoque*", "estoque", 0, 3),
            ("Estoque mínimo*", "minimo", 2, 0),
        ]
        for label, chave, linha, coluna in campos:
            ttk.Label(form, text=label).grid(row=linha, column=coluna, sticky="w", padx=5)
            entrada = ttk.Entry(form, textvariable=self.vars[chave])
            entrada.grid(row=linha + 1, column=coluna, sticky="ew", padx=5, pady=(0, 8))
            if chave == "estoque":
                self.entry_estoque = entrada

        ttk.Label(form, text="Unidade*").grid(row=2, column=1, sticky="w", padx=5)
        ttk.Combobox(
            form, textvariable=self.unidade, values=UNIDADES, state="readonly"
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=(0, 8))
        ttk.Label(
            form,
            text="UN unidade • PC peça • CX caixa • SC saco • KG quilograma • L litro • M metro • M2 metro quadrado • MC3 metro cúbico • RL rolo",
            style="Subtitulo.TLabel",
        ).grid(row=4, column=0, columnspan=4, sticky="w", padx=5, pady=(0, 4))

        ttk.Label(form, text="Categoria*").grid(row=2, column=2, sticky="w", padx=5)
        self.combo_categoria = ttk.Combobox(form, state="readonly")
        self.combo_categoria.grid(row=3, column=2, sticky="ew", padx=5, pady=(0, 8))

        ttk.Label(form, text="Fornecedor").grid(row=2, column=3, sticky="w", padx=5)
        self.combo_fornecedor = ttk.Combobox(form, state="readonly")
        self.combo_fornecedor.grid(row=3, column=3, sticky="ew", padx=5, pady=(0, 8))

        # Localização
        local = ttk.LabelFrame(form, text="Localização do produto", padding=10)
        local.grid(row=5, column=0, columnspan=4, sticky="ew", padx=5, pady=(6, 8))
        for c in range(4):
            local.columnconfigure(c, weight=1)

        ttk.Label(local, text="Tipo de localização*").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_tipo_local = ttk.Combobox(
            local,
            textvariable=self.tipo_localizacao,
            values=["INTERNA", "EXTERNA"],
            state="readonly",
        )
        self.combo_tipo_local.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.combo_tipo_local.bind("<<ComboboxSelected>>", lambda _: self.atualizar_campos_localizacao())

        ttk.Label(local, text="Corredor").grid(row=0, column=1, sticky="w", padx=5)
        self.entry_corredor = ttk.Entry(local, textvariable=self.vars["corredor"])
        self.entry_corredor.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 5))

        ttk.Label(local, text="Prateleira").grid(row=0, column=2, sticky="w", padx=5)
        self.entry_prateleira = ttk.Entry(local, textvariable=self.vars["prateleira"])
        self.entry_prateleira.grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 5))

        ttk.Label(local, text="Descrição do local externo").grid(row=0, column=3, sticky="w", padx=5)
        self.entry_descricao_local = ttk.Entry(local, textvariable=self.vars["descricao_localizacao"])
        self.entry_descricao_local.grid(row=1, column=3, sticky="ew", padx=5, pady=(0, 5))

        ttk.Label(
            local,
            text=(
                "Use INTERNA para produtos em corredor/prateleira. "
                "Use EXTERNA para areia, brita e outros materiais do pátio ou área externa."
            ),
            style="Subtitulo.TLabel",
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 0))

        ttk.Checkbutton(form, text="Produto ativo", variable=self.ativo).grid(
            row=6, column=0, sticky="w", padx=5, pady=(3, 0)
        )

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10)
        ttk.Button(barra, text="Novo", command=self.limpar).pack(side="left")
        self.btn_salvar = ttk.Button(barra, text="Salvar", style="Primario.TButton", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ttk.Button(barra, text="Desativar", command=self.excluir).pack(side="left")
        self.entry_busca = ttk.Entry(barra, textvariable=self.busca, width=35)
        self.entry_busca.pack(side="right")
        vincular_enter_acao(self.entry_busca, self.carregar)
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="right", padx=5)

        self.tree = criar_tree(self, [
            ("id", "ID", 45), ("codigo", "Código", 90), ("nome", "Produto", 190), ("categoria", "Categoria", 110),
            ("preco", "Preço", 80), ("estoque", "Estoque", 80), ("un", "Un.", 45),
            ("tipo", "Local", 75), ("localizacao", "Descrição da localização", 260),
            ("fornecedor", "Fornecedor", 135), ("ativo", "Ativo", 55)
        ])
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        vincular_fluxo_enter(form, self.btn_salvar)
        self.carregar_combos()
        self.atualizar_campos_localizacao()
        self.carregar()

    def atualizar_campos_localizacao(self):
        externa = self.tipo_localizacao.get() == "EXTERNA"
        estado_interno = "disabled" if externa else "normal"
        estado_externo = "normal" if externa else "disabled"

        self.entry_corredor.config(state=estado_interno)
        self.entry_prateleira.config(state=estado_interno)
        self.entry_descricao_local.config(state=estado_externo)

        if externa:
            self.vars["corredor"].set("")
            self.vars["prateleira"].set("")
        else:
            self.vars["descricao_localizacao"].set("")

    def carregar_combos(self):
        self.categorias = listar_categorias()
        self.fornecedores = listar_fornecedores()
        self.combo_categoria["values"] = [
            f"{c['id_categoria']} - {c['nome']}" for c in self.categorias
        ]
        self.combo_fornecedor["values"] = [""] + [
            f"{f['id_fornecedor']} - {f['nome_fantasia'] or f['razao_social']}"
            for f in self.fornecedores
        ]

    @staticmethod
    def texto_localizacao(produto):
        if produto.get("tipo_localizacao") == "EXTERNA":
            return produto.get("descricao_localizacao") or "Área externa sem descrição"

        partes = []
        if produto.get("corredor"):
            partes.append(f"Corredor {produto['corredor']}")
        if produto.get("prateleira"):
            partes.append(f"Prateleira {produto['prateleira']}")
        return " - ".join(partes) if partes else "Local interno não informado"

    def carregar(self):
        try:
            dados = buscar_produto(self.busca.get(), apenas_ativos=False) if self.busca.get().strip() else listar_produtos()
            limpar_tree(self.tree)
            for p in dados:
                self.tree.insert("", "end", values=(
                    p["id_produto"], p.get("codigo") or "", p["nome"], p["categoria"], f"{p['preco']:.2f}",
                    p["quantidade_estoque"], p["unidade_medida"],
                    "Fora" if p.get("tipo_localizacao") == "EXTERNA" else "Dentro",
                    self.texto_localizacao(p), p["fornecedor"] or "",
                    "Sim" if p["ativo"] else "Não"
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.id_selecionado = int(self.tree.item(sel[0], "values")[0])
        try:
            p = next(x for x in listar_produtos() if x["id_produto"] == self.id_selecionado)
            self.vars["nome"].set(p["nome"])
            self.vars["descricao"].set(p["descricao"] or "")
            self.vars["preco"].set(str(p["preco"]))
            self.vars["estoque"].set(str(p["quantidade_estoque"]))
            self.entry_estoque.config(state="disabled")
            self.vars["minimo"].set(str(p["estoque_minimo"]))
            self.vars["corredor"].set(p.get("corredor") or "")
            self.vars["prateleira"].set(p.get("prateleira") or "")
            self.vars["descricao_localizacao"].set(p.get("descricao_localizacao") or "")
            self.tipo_localizacao.set(p.get("tipo_localizacao") or "INTERNA")
            self.unidade.set(p["unidade_medida"])
            self.ativo.set(bool(p["ativo"]))
            self.combo_categoria.set(f"{p['id_categoria']} - {p['categoria']}")
            if p["id_fornecedor"]:
                self.combo_fornecedor.set(f"{p['id_fornecedor']} - {p['fornecedor']}")
            else:
                self.combo_fornecedor.set("")
            self.atualizar_campos_localizacao()
        except Exception as erro:
            mostrar_erro(erro)

    def salvar(self):
        try:
            id_categoria = parse_combo_id(self.combo_categoria.get())
            if not id_categoria:
                raise ValueError("Selecione uma categoria.")
            id_fornecedor = parse_combo_id(self.combo_fornecedor.get())

            args = (
                self.vars["nome"].get(), self.vars["descricao"].get(),
                self.vars["preco"].get(), self.vars["estoque"].get(),
                self.vars["minimo"].get(), self.unidade.get(), id_categoria,
                id_fornecedor, self.tipo_localizacao.get(),
                self.vars["corredor"].get(), self.vars["prateleira"].get(),
                self.vars["descricao_localizacao"].get(), self.ativo.get()
            )
            if self.id_selecionado:
                atualizar_produto(self.id_selecionado, *args)
            else:
                cadastrar_produto(*args)
            self.limpar()
            self.carregar()
            messagebox.showinfo("Produtos", "Produto salvo com sucesso.")
        except Exception as erro:
            mostrar_erro(erro)

    def excluir(self):
        if not self.id_selecionado:
            return
        if not confirmar_com_enter(self, "Desativar", "Desativar o produto selecionado?"):
            return
        try:
            excluir_produto(self.id_selecionado)
            self.limpar()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def limpar(self):
        self.id_selecionado = None
        self.entry_estoque.config(state="normal")
        for var in self.vars.values():
            var.set("")
        self.unidade.set("UN")
        self.tipo_localizacao.set("INTERNA")
        self.ativo.set(True)
        self.combo_categoria.set("")
        self.combo_fornecedor.set("")
        self.atualizar_campos_localizacao()
