import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.fornecedor_funcoes import (
    cadastrar_fornecedor, listar_fornecedores, buscar_fornecedor,
    atualizar_fornecedor, excluir_fornecedor
)
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro,
    vincular_fluxo_enter, vincular_enter_acao, confirmar_com_enter,
)


class TelaFornecedores(ttk.Frame):
    CAMPOS = ["razao_social", "nome_fantasia", "cnpj", "telefone", "email", "endereco"]

    def __init__(self, master):
        super().__init__(master)
        self.id_selecionado = None
        self.vars = {c: tk.StringVar() for c in self.CAMPOS}

        form = ttk.LabelFrame(self, text="Cadastro", padding=10)
        form.pack(fill="x", padx=10, pady=10)
        labels = ["Razão social*", "Nome fantasia", "CNPJ", "Telefone", "E-mail", "Endereço"]
        for i, (campo, label) in enumerate(zip(self.CAMPOS, labels)):
            r, c = divmod(i, 3)
            ttk.Label(form, text=label).grid(row=r*2, column=c, sticky="w", padx=5)
            ttk.Entry(form, textvariable=self.vars[campo]).grid(
                row=r*2+1, column=c, sticky="ew", padx=5, pady=(0, 8)
            )
            form.columnconfigure(c, weight=1)

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10)
        ttk.Button(barra, text="Novo", command=self.limpar).pack(side="left")
        self.btn_salvar = ttk.Button(barra, text="Salvar", style="Primario.TButton", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ttk.Button(barra, text="Excluir", command=self.excluir).pack(side="left")

        self.busca = tk.StringVar()
        self.entry_busca = ttk.Entry(barra, textvariable=self.busca, width=35)
        self.entry_busca.pack(side="right")
        vincular_enter_acao(self.entry_busca, self.carregar)
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="right", padx=5)

        self.tree = criar_tree(self, [
            ("id", "ID", 50), ("razao", "Razão social", 200),
            ("fantasia", "Nome fantasia", 180), ("cnpj", "CNPJ", 130),
            ("telefone", "Telefone", 120), ("email", "E-mail", 180)
        ])
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        vincular_fluxo_enter(form, self.btn_salvar)
        self.carregar()

    def carregar(self):
        try:
            dados = buscar_fornecedor(self.busca.get()) if self.busca.get().strip() else listar_fornecedores()
            limpar_tree(self.tree)
            for f in dados:
                self.tree.insert("", "end", values=(
                    f["id_fornecedor"], f["razao_social"], f["nome_fantasia"] or "",
                    f["cnpj"] or "", f["telefone"] or "", f["email"] or ""
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.id_selecionado = int(self.tree.item(sel[0], "values")[0])
        try:
            dados = next(f for f in listar_fornecedores() if f["id_fornecedor"] == self.id_selecionado)
            for c in self.CAMPOS:
                self.vars[c].set(dados.get(c) or "")
        except Exception as erro:
            mostrar_erro(erro)

    def salvar(self):
        try:
            args = [self.vars[c].get() for c in self.CAMPOS]
            if self.id_selecionado:
                atualizar_fornecedor(self.id_selecionado, *args)
            else:
                cadastrar_fornecedor(*args)
            self.limpar()
            self.carregar()
            messagebox.showinfo("Fornecedores", "Fornecedor salvo com sucesso.")
        except Exception as erro:
            mostrar_erro(erro)

    def excluir(self):
        if not self.id_selecionado:
            return
        if not confirmar_com_enter(self, "Excluir", "Excluir o fornecedor selecionado?"):
            return
        try:
            excluir_fornecedor(self.id_selecionado)
            self.limpar()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def limpar(self):
        self.id_selecionado = None
        for var in self.vars.values():
            var.set("")
