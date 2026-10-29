import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.categoria_funcoes import (
    cadastrar_categoria, listar_categorias, buscar_categoria,
    atualizar_categoria, excluir_categoria
)
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro,
    vincular_fluxo_enter, vincular_enter_acao, confirmar_com_enter,
)


class TelaCategorias(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.id_selecionado = None
        self.nome = tk.StringVar()
        self.descricao = tk.StringVar()
        self.busca = tk.StringVar()

        form = ttk.LabelFrame(self, text="Categoria", padding=10)
        form.pack(fill="x", padx=10, pady=10)
        ttk.Label(form, text="Nome*").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.nome).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(form, text="Descrição").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.descricao).grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=2)

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10)
        ttk.Button(barra, text="Novo", command=self.limpar).pack(side="left")
        self.btn_salvar = ttk.Button(barra, text="Salvar", style="Primario.TButton", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ttk.Button(barra, text="Excluir", command=self.excluir).pack(side="left")
        self.entry_busca = ttk.Entry(barra, textvariable=self.busca, width=25)
        self.entry_busca.pack(side="right")
        vincular_enter_acao(self.entry_busca, self.carregar)
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="right", padx=5)

        self.tree = criar_tree(self, [
            ("id", "ID", 60), ("nome", "Nome", 180), ("descricao", "Descrição", 420)
        ])
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        vincular_fluxo_enter(form, self.btn_salvar)
        self.carregar()

    def carregar(self):
        try:
            dados = buscar_categoria(self.busca.get()) if self.busca.get().strip() else listar_categorias()
            limpar_tree(self.tree)
            for c in dados:
                self.tree.insert("", "end", values=(c["id_categoria"], c["nome"], c["descricao"] or ""))
        except Exception as erro:
            mostrar_erro(erro)

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0], "values")
        self.id_selecionado = int(valores[0])
        self.nome.set(valores[1])
        self.descricao.set(valores[2])

    def salvar(self):
        try:
            if self.id_selecionado:
                atualizar_categoria(self.id_selecionado, self.nome.get(), self.descricao.get())
            else:
                cadastrar_categoria(self.nome.get(), self.descricao.get())
            self.limpar()
            self.carregar()
            messagebox.showinfo("Categorias", "Categoria salva com sucesso.")
        except Exception as erro:
            mostrar_erro(erro)

    def excluir(self):
        if not self.id_selecionado:
            return
        if not confirmar_com_enter(self, "Excluir", "Excluir categoria selecionada?"):
            return
        try:
            excluir_categoria(self.id_selecionado)
            self.limpar()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def limpar(self):
        self.id_selecionado = None
        self.nome.set("")
        self.descricao.set("")
