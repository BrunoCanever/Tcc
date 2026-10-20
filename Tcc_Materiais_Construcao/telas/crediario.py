import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.crediario_funcoes import listar_parcelas, dar_baixa_parcela
from funcoes.utils import moeda
from telas.helpers import criar_tree, limpar_tree, mostrar_erro, vincular_enter_acao, confirmar_com_enter


class TelaCrediario(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        barra = ttk.Frame(self, padding=10)
        barra.pack(fill="x")
        self.status = tk.StringVar(value="")
        ttk.Label(barra, text="Status:").pack(side="left")
        self.combo_status = ttk.Combobox(
            barra, textvariable=self.status,
            values=["", "PENDENTE", "ATRASADA", "PAGA"],
            state="readonly", width=14
        )
        self.combo_status.pack(side="left", padx=5)
        vincular_enter_acao(self.combo_status, self.carregar)
        self.termo = tk.StringVar()
        ttk.Label(barra, text="Cliente:").pack(side="left", padx=(15, 0))
        self.entry_termo = ttk.Entry(barra, textvariable=self.termo, width=28)
        self.entry_termo.pack(side="left", padx=5)
        vincular_enter_acao(self.entry_termo, self.carregar)
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="left")
        ttk.Button(barra, text="Dar baixa", command=self.baixar).pack(side="right")

        self.tree = criar_tree(self, [
            ("id", "ID", 55), ("venda", "Venda", 70), ("cliente", "Cliente", 220),
            ("numero", "Parcela", 70), ("valor", "Valor", 100),
            ("vencimento", "Vencimento", 100), ("pagamento", "Pagamento", 100),
            ("status", "Status", 90)
        ])
        self.tree.bind("<Return>", lambda _e: (self.baixar(), "break")[1])
        self.tree.bind("<KP_Enter>", lambda _e: (self.baixar(), "break")[1])
        self.carregar()

    def carregar(self):
        try:
            dados = listar_parcelas(self.status.get() or None, self.termo.get() or None)
            limpar_tree(self.tree)
            for p in dados:
                self.tree.insert("", "end", values=(
                    p["id_parcela"], p["id_venda"], p["cliente"], p["numero"],
                    moeda(p["valor"]), p["data_vencimento"],
                    p["data_pagamento"] or "", p["status"]
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def baixar(self):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0], "values")
        if valores[-1] == "PAGA":
            messagebox.showinfo("Crediário", "Essa parcela já está paga.")
            return
        if not confirmar_com_enter(self, "Crediário", "Confirmar pagamento da parcela?"):
            return
        try:
            dar_baixa_parcela(int(valores[0]))
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)
