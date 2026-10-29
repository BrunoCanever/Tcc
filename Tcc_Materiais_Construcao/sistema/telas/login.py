import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.auth_funcoes import autenticar
from telas.helpers import centralizar_janela, ativar_enter_botao

class TelaLogin:
    def __init__(self, root, ao_logar):
        self.root = root
        self.ao_logar = ao_logar
        root.title("Login - Sistema de Gerenciamento")
        root.resizable(False, False)
        centralizar_janela(root, 480, 390, maximizada=False)

        fundo = ttk.Frame(root, padding=24)
        fundo.pack(fill="both", expand=True)
        cartao = ttk.Frame(fundo, style="Painel.TFrame", padding=30)
        cartao.pack(fill="both", expand=True)

        ttk.Label(cartao, text="Sistema de Gerenciamento", style="Cabecalho.TLabel").pack(anchor="w", pady=(2,4))
        ttk.Label(cartao, text="Loja de Materiais de Construção", style="Painel.TLabel").pack(anchor="w", pady=(0,24))
        ttk.Label(cartao, text="Login", style="Painel.TLabel").pack(anchor="w")
        self.login = ttk.Entry(cartao)
        self.login.pack(fill="x", pady=(5,14), ipady=3)
        ttk.Label(cartao, text="Senha", style="Painel.TLabel").pack(anchor="w")
        self.senha = ttk.Entry(cartao, show="*")
        self.senha.pack(fill="x", pady=(5,22), ipady=3)
        self.botao_entrar = ttk.Button(
            cartao,
            text="Entrar",
            style="Primario.TButton",
            command=self.entrar,
        )
        self.botao_entrar.pack(fill="x")
        ativar_enter_botao(self.botao_entrar)

        ttk.Label(
            cartao,
            text="Enter: Login → Senha → Entrar → Sistema",
            style="Painel.TLabel",
        ).pack(anchor="w", pady=(18, 0))

        self.login.bind(
            "<Return>",
            lambda _e: self._ir_para_senha(),
        )
        self.login.bind(
            "<KP_Enter>",
            lambda _e: self._ir_para_senha(),
        )
        self.senha.bind(
            "<Return>",
            lambda _e: self._ir_para_confirmacao(),
        )
        self.senha.bind(
            "<KP_Enter>",
            lambda _e: self._ir_para_confirmacao(),
        )
        self.login.focus_set()


    def _ir_para_senha(self):
        self.senha.focus_set()
        self.senha.selection_range(0, "end")
        return "break"

    def _ir_para_confirmacao(self):
        self.botao_entrar.focus_set()
        return "break"

    def entrar(self):
        try:
            funcionario = autenticar(self.login.get(), self.senha.get())
            if not funcionario:
                messagebox.showerror("Login", "Login ou senha inválidos.")
                return
            self.ao_logar(funcionario)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))
