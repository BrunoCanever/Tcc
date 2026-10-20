import tkinter as tk
from tkinter import ttk
from datetime import date
from funcoes.relatorio_funcoes import (
    vendas_por_periodo, produtos_mais_vendidos, estoque_atual,
    estoque_baixo, clientes_crediario_pendente, entregas_pendentes
)
from telas.helpers import mostrar_erro, solicitar_texto_enter


class TelaRelatorios(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        barra = ttk.Frame(self, padding=10)
        barra.pack(fill="x")
        for texto, comando in [
            ("Vendas por período", self.vendas),
            ("Mais vendidos", self.mais_vendidos),
            ("Estoque atual", self.estoque),
            ("Estoque baixo", self.baixo),
            ("Crediário pendente", self.crediario),
            ("Entregas pendentes", self.entregas),
        ]:
            ttk.Button(barra, text=texto, command=comando).pack(side="left", padx=3)

        self.texto = tk.Text(self, wrap="none", font=("Consolas", 10))
        self.texto.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def exibir(self, titulo, dados):
        self.texto.delete("1.0", "end")
        self.texto.insert("end", titulo + "\n")
        self.texto.insert("end", "=" * 100 + "\n")
        if not dados:
            self.texto.insert("end", "Nenhum registro encontrado.\n")
            return

        colunas = list(dados[0].keys())
        self.texto.insert("end", " | ".join(colunas) + "\n")
        self.texto.insert("end", "-" * 100 + "\n")
        for linha in dados:
            self.texto.insert("end", " | ".join(str(linha[c] if linha[c] is not None else "") for c in colunas) + "\n")

    def vendas(self):
        try:
            hoje = date.today().isoformat()
            inicio = solicitar_texto_enter(self, "Período", "Data inicial (AAAA-MM-DD):", valor_inicial=hoje)
            if not inicio:
                return
            fim = solicitar_texto_enter(self, "Período", "Data final (AAAA-MM-DD):", valor_inicial=hoje)
            if not fim:
                return
            self.exibir("VENDAS POR PERÍODO", vendas_por_periodo(inicio, fim))
        except Exception as erro:
            mostrar_erro(erro)

    def mais_vendidos(self):
        try:
            self.exibir("PRODUTOS MAIS VENDIDOS", produtos_mais_vendidos())
        except Exception as erro:
            mostrar_erro(erro)

    def estoque(self):
        try:
            self.exibir("ESTOQUE ATUAL", estoque_atual())
        except Exception as erro:
            mostrar_erro(erro)

    def baixo(self):
        try:
            self.exibir("PRODUTOS COM ESTOQUE BAIXO", estoque_baixo())
        except Exception as erro:
            mostrar_erro(erro)

    def crediario(self):
        try:
            self.exibir("CLIENTES COM CREDIÁRIO PENDENTE", clientes_crediario_pendente())
        except Exception as erro:
            mostrar_erro(erro)

    def entregas(self):
        try:
            self.exibir("ENTREGAS PENDENTES", entregas_pendentes())
        except Exception as erro:
            mostrar_erro(erro)
