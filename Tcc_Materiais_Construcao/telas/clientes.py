import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.cliente_funcoes import (
    cadastrar_cliente, listar_clientes, buscar_cliente,
    atualizar_cliente, excluir_cliente
)
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro,
    vincular_fluxo_enter, vincular_enter_acao, confirmar_com_enter,
)


class TelaClientes(ttk.Frame):
    CAMPOS = ["nome", "cpf_cnpj", "telefone", "email", "endereco", "cidade", "uf", "cep"]

    def __init__(self, master):
        super().__init__(master)
        self.id_selecionado = None
        self.vars = {campo: tk.StringVar() for campo in self.CAMPOS}

        form = ttk.LabelFrame(self, text="Cadastro", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        labels = {
            "nome": "Nome*", "cpf_cnpj": "CPF/CNPJ", "telefone": "Telefone",
            "email": "E-mail", "endereco": "Endereço", "cidade": "Cidade",
            "uf": "UF", "cep": "CEP"
        }
        for i, campo in enumerate(self.CAMPOS):
            r, c = divmod(i, 4)
            ttk.Label(form, text=labels[campo]).grid(row=r*2, column=c, sticky="w", padx=5)
            ttk.Entry(form, textvariable=self.vars[campo]).grid(
                row=r*2+1, column=c, sticky="ew", padx=5, pady=(0, 8)
            )
            form.columnconfigure(c, weight=1)

        botoes = ttk.Frame(self)
        botoes.pack(fill="x", padx=10)
        ttk.Button(botoes, text="Novo", command=self.limpar).pack(side="left")
        self.btn_salvar = ttk.Button(botoes, text="Salvar", style="Primario.TButton", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ttk.Button(botoes, text="Excluir", command=self.excluir).pack(side="left")

        self.busca = tk.StringVar()
        self.entry_busca = ttk.Entry(botoes, textvariable=self.busca, width=35)
        self.entry_busca.pack(side="right")
        vincular_enter_acao(self.entry_busca, self.carregar)
        ttk.Button(botoes, text="Buscar", command=self.carregar).pack(side="right", padx=5)

        self.tree = criar_tree(self, [
            ("id", "ID", 50), ("nome", "Nome", 180), ("cpf", "CPF/CNPJ", 120),
            ("telefone", "Telefone", 110), ("email", "E-mail", 160),
            ("cidade", "Cidade", 120), ("uf", "UF", 45)
        ])
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        vincular_fluxo_enter(form, self.btn_salvar)
        self.carregar()

    def carregar(self):
        try:
            dados = buscar_cliente(self.busca.get()) if self.busca.get().strip() else listar_clientes()
            limpar_tree(self.tree)
            for c in dados:
                self.tree.insert("", "end", values=(
                    c["id_cliente"], c["nome"], c["cpf_cnpj"] or "",
                    c["telefone"] or "", c["email"] or "",
                    c["cidade"] or "", c["uf"] or ""
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        id_cliente = int(self.tree.item(sel[0], "values")[0])
        try:
            dados = next(c for c in listar_clientes() if c["id_cliente"] == id_cliente)
            self.id_selecionado = id_cliente
            for campo in self.CAMPOS:
                self.vars[campo].set(dados.get(campo) or "")
        except Exception as erro:
            mostrar_erro(erro)

    def salvar(self):
        try:
            args = [self.vars[c].get() for c in self.CAMPOS]
            if self.id_selecionado:
                atualizar_cliente(self.id_selecionado, *args)
            else:
                cadastrar_cliente(*args)
            self.limpar()
            self.carregar()
            messagebox.showinfo("Clientes", "Cliente salvo com sucesso.")
        except Exception as erro:
            mostrar_erro(erro)

    def excluir(self):
        if not self.id_selecionado:
            return
        if not confirmar_com_enter(self, "Excluir", "Excluir o cliente selecionado?"):
            return
        try:
            excluir_cliente(self.id_selecionado)
            self.limpar()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def limpar(self):
        self.id_selecionado = None
        for var in self.vars.values():
            var.set("")
