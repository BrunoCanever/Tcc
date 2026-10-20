import tkinter as tk
from tkinter import messagebox

from funcoes.auth_funcoes import garantir_admin_inicial
from scripts.atualizar_localizacao_produtos import atualizar_banco
from scripts.atualizar_venda_etapas import atualizar_banco as atualizar_banco_venda
from scripts.atualizar_caixa_diario import atualizar_banco as atualizar_banco_caixa
from scripts.atualizar_preco_item_venda import atualizar_banco as atualizar_banco_preco_item
from scripts.atualizar_catalogo_unidades import atualizar_banco as atualizar_banco_catalogo
from telas.login import TelaLogin
from telas.menu import MenuPrincipal


def iniciar():
    root = tk.Tk()

    try:
        # Mantém bancos de versões anteriores compatíveis sem apagar dados.
        atualizar_banco()
        atualizar_banco_venda()
        atualizar_banco_caixa()
        atualizar_banco_preco_item()
        atualizar_banco_catalogo()
        criado = garantir_admin_inicial()
        if criado:
            messagebox.showinfo(
                "Primeiro acesso",
                "Usuário administrador inicial criado.\n\n"
                "Login: q\nSenha: q\n\n"
                "Este é o administrador padrão com acesso total ao sistema."
            )
    except Exception as erro:
        messagebox.showerror(
            "Banco de dados",
            "Não foi possível iniciar o sistema.\n\n"
            f"{erro}\n\n"
            "Confirme se o MySQL está ligado e se o banco foi criado."
        )
        root.destroy()
        return

    def ao_logar(funcionario):
        for widget in root.winfo_children():
            widget.destroy()
        MenuPrincipal(root, funcionario)

    TelaLogin(root, ao_logar)
    root.mainloop()


if __name__ == "__main__":
    iniciar()
