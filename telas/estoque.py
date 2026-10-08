import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.produto_funcoes import listar_produtos
from funcoes.estoque_funcoes import movimentar_estoque, listar_movimentacoes
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro, parse_combo_id,
    vincular_fluxo_enter,
)


class TelaEstoque(ttk.Frame):
    def __init__(self, master, funcionario):
        super().__init__(master)
        self.funcionario = funcionario

        form = ttk.LabelFrame(self, text="Movimentação", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Produto*").grid(row=0, column=0, sticky="w")
        self.combo_produto = ttk.Combobox(form, state="readonly", width=45)
        self.combo_produto.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Tipo*").grid(row=0, column=1, sticky="w")
        self.tipo = tk.StringVar(value="ENTRADA")
        ttk.Combobox(
            form, textvariable=self.tipo,
            values=["ENTRADA", "SAIDA", "AJUSTE"], state="readonly", width=14
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Quantidade / saldo final*").grid(row=0, column=2, sticky="w")
        self.quantidade = tk.StringVar()
        ttk.Entry(form, textvariable=self.quantidade).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Motivo").grid(row=0, column=3, sticky="w")
        self.motivo = tk.StringVar()
        ttk.Entry(form, textvariable=self.motivo).grid(row=1, column=3, sticky="ew", padx=(0, 8))

        self.btn_registrar = ttk.Button(form, text="Registrar", style="Primario.TButton", command=self.registrar)
        self.btn_registrar.grid(row=1, column=4)
        form.columnconfigure(0, weight=2)
        form.columnconfigure(3, weight=1)

        self.tree = criar_tree(self, [
            ("data", "Data", 145), ("produto", "Produto", 190), ("tipo", "Tipo", 80),
            ("qtd", "Quantidade", 85), ("antes", "Antes", 75), ("depois", "Depois", 75),
            ("motivo", "Motivo", 220), ("funcionario", "Funcionário", 150)
        ])
        vincular_fluxo_enter(form, self.btn_registrar)
        self.carregar_produtos()
        self.carregar()

    def carregar_produtos(self):
        self.produtos = listar_produtos(apenas_ativos=True)
        self.combo_produto["values"] = [
            f"{p['id_produto']} - {p['nome']} | estoque: {p['quantidade_estoque']} {p['unidade_medida']}"
            for p in self.produtos
        ]

    def registrar(self):
        try:
            id_produto = parse_combo_id(self.combo_produto.get())
            if not id_produto:
                raise ValueError("Selecione um produto.")
            novo = movimentar_estoque(
                id_produto, self.funcionario["id_funcionario"],
                self.tipo.get(), self.quantidade.get(), self.motivo.get()
            )
            messagebox.showinfo("Estoque", f"Movimentação registrada. Novo saldo: {novo}")
            self.quantidade.set("")
            self.motivo.set("")
            self.carregar_produtos()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def carregar(self):
        try:
            limpar_tree(self.tree)
            for m in listar_movimentacoes():
                self.tree.insert("", "end", values=(
                    m["data_movimentacao"], m["produto"], m["tipo"], m["quantidade"],
                    m["quantidade_anterior"], m["quantidade_nova"],
                    m["motivo"] or "", m["funcionario"]
                ))
        except Exception as erro:
            mostrar_erro(erro)
