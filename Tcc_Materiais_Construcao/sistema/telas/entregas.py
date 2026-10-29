import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.entrega_funcoes import listar_entregas, atualizar_status_entrega, STATUS_ENTREGA
from telas.helpers import criar_tree, limpar_tree, mostrar_erro, vincular_enter_acao


class TelaEntregas(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        barra = ttk.Frame(self, padding=10)
        barra.pack(fill="x")
        self.filtro = tk.StringVar(value="")
        ttk.Label(barra, text="Filtrar:").pack(side="left")
        self.combo_filtro = ttk.Combobox(
            barra, textvariable=self.filtro,
            values=[""] + STATUS_ENTREGA, state="readonly", width=14
        )
        self.combo_filtro.pack(side="left", padx=5)
        vincular_enter_acao(self.combo_filtro, self.carregar)
        ttk.Button(barra, text="Atualizar lista", command=self.carregar).pack(side="left")

        ttk.Label(barra, text="Novo status:").pack(side="right", padx=(10, 0))
        self.novo_status = tk.StringVar(value="EM ROTA")
        self.combo_novo_status = ttk.Combobox(
            barra, textvariable=self.novo_status,
            values=STATUS_ENTREGA, state="readonly", width=14
        )
        self.combo_novo_status.pack(side="right", padx=5)
        vincular_enter_acao(self.combo_novo_status, self.alterar)
        ttk.Button(barra, text="Alterar status", command=self.alterar).pack(side="right")

        self.tree = criar_tree(self, [
            ("id", "ID", 55), ("venda", "Venda", 70), ("cliente", "Cliente", 180),
            ("endereco", "Endereço", 300), ("prevista", "Previsão", 100),
            ("status", "Status", 90), ("obs", "Observação", 220)
        ])
        self.tree.bind("<Return>", lambda _e: (self.alterar(), "break")[1])
        self.tree.bind("<KP_Enter>", lambda _e: (self.alterar(), "break")[1])
        self.carregar()

    def carregar(self):
        try:
            dados = listar_entregas(self.filtro.get() or None)
            limpar_tree(self.tree)
            for e in dados:
                self.tree.insert("", "end", values=(
                    e["id_entrega"], e["id_venda"], e["cliente"], e["endereco"],
                    e["data_prevista"] or "", e["status"], e["observacao"] or ""
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def alterar(self):
        sel = self.tree.selection()
        if not sel:
            return
        id_entrega = int(self.tree.item(sel[0], "values")[0])
        try:
            atualizar_status_entrega(id_entrega, self.novo_status.get())
            self.carregar()
            messagebox.showinfo("Entregas", "Status atualizado.")
        except Exception as erro:
            mostrar_erro(erro)
