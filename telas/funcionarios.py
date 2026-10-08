import tkinter as tk
from tkinter import ttk, messagebox
from funcoes.funcionario_funcoes import (
    cadastrar_funcionario, listar_funcionarios, buscar_funcionario,
    atualizar_funcionario, excluir_funcionario, listar_cargos
)
from telas.helpers import (
    criar_tree, limpar_tree, mostrar_erro, parse_combo_id,
    vincular_fluxo_enter, vincular_enter_acao, confirmar_com_enter,
)


class TelaFuncionarios(ttk.Frame):
    def __init__(self, master, funcionario_logado):
        super().__init__(master)
        self.funcionario_logado = funcionario_logado
        self.id_selecionado = None

        self.nome = tk.StringVar()
        self.cpf = tk.StringVar()
        self.email = tk.StringVar()
        self.telefone = tk.StringVar()
        self.login = tk.StringVar()
        self.senha = tk.StringVar()
        self.ativo = tk.BooleanVar(value=True)
        self.busca = tk.StringVar()

        form = ttk.LabelFrame(self, text="Funcionário", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        campos = [
            ("Nome*", self.nome), ("CPF", self.cpf), ("E-mail", self.email),
            ("Telefone", self.telefone), ("Login*", self.login), ("Senha", self.senha)
        ]
        for i, (label, var) in enumerate(campos):
            r, c = divmod(i, 3)
            ttk.Label(form, text=label).grid(row=r*2, column=c, sticky="w", padx=5)
            ttk.Entry(form, textvariable=var, show="*" if label=="Senha" else "").grid(
                row=r*2+1, column=c, sticky="ew", padx=5, pady=(0, 8)
            )
            form.columnconfigure(c, weight=1)

        ttk.Label(form, text="Cargo*").grid(row=4, column=0, sticky="w", padx=5)
        self.combo_cargo = ttk.Combobox(form, state="readonly")
        self.combo_cargo.grid(row=5, column=0, sticky="ew", padx=5)
        ttk.Checkbutton(form, text="Ativo", variable=self.ativo).grid(row=5, column=1, sticky="w", padx=5)

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10)
        ttk.Button(barra, text="Novo", command=self.limpar).pack(side="left")
        self.btn_salvar = ttk.Button(barra, text="Salvar", style="Primario.TButton", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ttk.Button(barra, text="Desativar", command=self.excluir).pack(side="left")
        self.entry_busca = ttk.Entry(barra, textvariable=self.busca, width=30)
        self.entry_busca.pack(side="right")
        vincular_enter_acao(self.entry_busca, self.carregar)
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="right", padx=5)

        self.tree = criar_tree(self, [
            ("id", "ID", 50), ("nome", "Nome", 180), ("login", "Login", 120),
            ("cargo", "Cargo", 130), ("cpf", "CPF", 110), ("email", "E-mail", 170),
            ("ativo", "Ativo", 60)
        ])
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        vincular_fluxo_enter(form, self.btn_salvar)
        self.atualizar_cargos()
        self.carregar()

    def atualizar_cargos(self):
        self.cargos = listar_cargos()
        self.combo_cargo["values"] = [f"{c['id_cargo']} - {c['nome']}" for c in self.cargos]

    def carregar(self):
        try:
            dados = buscar_funcionario(self.busca.get()) if self.busca.get().strip() else listar_funcionarios()
            limpar_tree(self.tree)
            for f in dados:
                self.tree.insert("", "end", values=(
                    f["id_funcionario"], f["nome"], f["login"], f["cargo"],
                    f["cpf"] or "", f["email"] or "", "Sim" if f["ativo"] else "Não"
                ))
        except Exception as erro:
            mostrar_erro(erro)

    def selecionar(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.id_selecionado = int(self.tree.item(sel[0], "values")[0])
        try:
            f = next(x for x in listar_funcionarios() if x["id_funcionario"] == self.id_selecionado)
            self.nome.set(f["nome"])
            self.cpf.set(f["cpf"] or "")
            self.email.set(f["email"] or "")
            self.telefone.set(f["telefone"] or "")
            self.login.set(f["login"])
            self.senha.set("")
            self.ativo.set(bool(f["ativo"]))
            self.combo_cargo.set(f"{f['id_cargo']} - {f['cargo']}")
        except Exception as erro:
            mostrar_erro(erro)

    def salvar(self):
        try:
            id_cargo = parse_combo_id(self.combo_cargo.get())
            if not id_cargo:
                raise ValueError("Selecione um cargo.")
            if self.id_selecionado:
                atualizar_funcionario(
                    self.id_selecionado, self.nome.get(), self.login.get(), id_cargo,
                    self.cpf.get(), self.email.get(), self.telefone.get(),
                    self.ativo.get(), self.senha.get() or None
                )
            else:
                if not self.senha.get():
                    raise ValueError("Senha é obrigatória para novo funcionário.")
                cadastrar_funcionario(
                    self.nome.get(), self.login.get(), self.senha.get(), id_cargo,
                    self.cpf.get(), self.email.get(), self.telefone.get(), self.ativo.get()
                )
            self.limpar()
            self.carregar()
            messagebox.showinfo("Funcionários", "Funcionário salvo com sucesso.")
        except Exception as erro:
            mostrar_erro(erro)

    def excluir(self):
        if not self.id_selecionado:
            return
        if self.id_selecionado == self.funcionario_logado["id_funcionario"]:
            messagebox.showwarning("Funcionários", "Você não pode excluir o usuário logado.")
            return
        if not confirmar_com_enter(self, "Desativar", "Desativar funcionário selecionado?"):
            return
        try:
            excluir_funcionario(self.id_selecionado)
            self.limpar()
            self.carregar()
        except Exception as erro:
            mostrar_erro(erro)

    def limpar(self):
        self.id_selecionado = None
        for var in [self.nome, self.cpf, self.email, self.telefone, self.login, self.senha]:
            var.set("")
        self.ativo.set(True)
        self.combo_cargo.set("")
