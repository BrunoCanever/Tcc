import tkinter as tk
from tkinter import ttk, messagebox

from telas.helpers import (
    centralizar_janela,
    maximizar_janela,
    modo_janela,
    alternar_tela_cheia,
    confirmar_com_enter,
)
from telas.clientes import TelaClientes
from telas.fornecedores import TelaFornecedores
from telas.categorias import TelaCategorias
from telas.produtos import TelaProdutos
from telas.funcionarios import TelaFuncionarios
from telas.estoque import TelaEstoque
from telas.caixa import TelaCaixa
from telas.caixa_diario import TelaCaixaDiario
from telas.crediario import TelaCrediario
from telas.entregas import TelaEntregas
from telas.relatorios import TelaRelatorios
from telas.localizador import TelaLocalizador


class MenuPrincipal:
    """
    Controla toda a aplicação dentro de uma única janela Tk.

    Os módulos ficam abertos como abas de um ttk.Notebook.
    """

    def __init__(self, root, funcionario):
        self.root = root
        self.funcionario = funcionario

        self.abas = {}
        self.historico = []
        self.aba_atual = None
        self._mudanca_por_historico = False

        root.title("Sistema de Gerenciamento - Materiais de Construção")
        root.resizable(True, True)
        centralizar_janela(root, 1280, 800, maximizada=True)

        # Esc fecha a aba atual; Alt+Left volta para a aba anterior.
        root.bind("<Escape>", self.fechar_aba_atual)
        root.bind("<Alt-Left>", self.voltar)
        root.bind("<F1>", self.mostrar_atalhos)
        root.bind("<F2>", self.abrir_caixa_atalho)
        root.bind("<F3>", self.abrir_caixa_diario_atalho)
        root.bind("<F4>", lambda e: self._executar_atalho_aba("atalho_f4"))
        root.bind("<F5>", lambda e: self._executar_atalho_aba("atalho_f5"))
        root.bind("<Control-i>", self.abrir_ia_atalho)
        root.bind("<Control-I>", self.abrir_ia_atalho)

        self._montar()

    def _montar(self):
        # Cabeçalho
        topo = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 12))
        topo.pack(fill="x")

        titulos = ttk.Frame(topo, style="Header.TFrame")
        titulos.pack(side="left", fill="x", expand=True)

        ttk.Label(
            titulos,
            text="Sistema de Gerenciamento",
            style="Cabecalho.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            titulos,
            text=f"{self.funcionario['nome']}  •  {self.funcionario['cargo']}",
            style="Painel.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        controles = ttk.Frame(topo, style="Header.TFrame")
        controles.pack(side="right")

        ttk.Button(
            controles,
            text="Fechar aba (Esc)",
            style="Secundario.TButton",
            command=self.fechar_aba_atual,
        ).pack(side="left", padx=3)

        ttk.Button(
            controles,
            text="Voltar (Alt+←)",
            style="Secundario.TButton",
            command=self.voltar,
        ).pack(side="left", padx=3)

        ttk.Button(
            controles,
            text="Modo janela",
            style="Secundario.TButton",
            command=lambda: modo_janela(self.root, 1280, 800),
        ).pack(side="left", padx=3)

        ttk.Button(
            controles,
            text="Maximizar",
            style="Secundario.TButton",
            command=lambda: maximizar_janela(self.root),
        ).pack(side="left", padx=3)

        ttk.Button(
            controles,
            text="Tela cheia (F11)",
            style="Primario.TButton",
            command=lambda: alternar_tela_cheia(self.root),
        ).pack(side="left", padx=3)

        # Área principal
        corpo = ttk.Frame(self.root)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)

        lateral = ttk.Frame(corpo, style="Sidebar.TFrame", padding=(14, 18))
        lateral.grid(row=0, column=0, sticky="ns")

        area_abas = ttk.Frame(corpo, padding=(12, 10, 12, 12))
        area_abas.grid(row=0, column=1, sticky="nsew")
        area_abas.rowconfigure(0, weight=1)
        area_abas.columnconfigure(0, weight=1)

        ttk.Label(
            lateral,
            text="MÓDULOS",
            style="SidebarTitulo.TLabel",
        ).pack(anchor="w", padx=8, pady=(2, 12))

        botoes = [
            ("Frente de Caixa", "caixa", TelaCaixa, (self.funcionario,)),
            ("Caixa Diário", "caixa_diario", TelaCaixaDiario, (self.funcionario,)),
            ("Produtos", "produtos", TelaProdutos, ()),
            ("Categorias", "categorias", TelaCategorias, ()),
            ("Clientes", "clientes", TelaClientes, ()),
            ("Fornecedores", "fornecedores", TelaFornecedores, ()),
            ("Estoque", "estoque", TelaEstoque, (self.funcionario,)),
            ("Crediário", "crediario", TelaCrediario, ()),
            ("Entregas", "entregas", TelaEntregas, ()),
            ("Relatórios", "relatorios", TelaRelatorios, ()),
            ("Assistente Local", "localizador", TelaLocalizador, ()),
        ]

        if self.funcionario["cargo"] == "Administrador":
            botoes.insert(
                5,
                (
                    "Funcionários",
                    "funcionarios",
                    TelaFuncionarios,
                    (self.funcionario,),
                ),
            )

        for titulo, chave, classe, args in botoes:
            ttk.Button(
                lateral,
                text=titulo,
                style="Sidebar.TButton",
                width=23,
                command=lambda t=titulo, c=chave, cl=classe, a=args:
                    self.abrir_aba(c, t, cl, *a),
            ).pack(fill="x", pady=2)

        ttk.Separator(lateral).pack(fill="x", padx=8, pady=14)

        ttk.Label(
            lateral,
            text=("F1: atalhos\nF2: frente de caixa\nF3: caixa diário\n"
                  "F4: avançar/finalizar venda\nF5: cancelar venda\n"
                  "Ctrl+I: assistente local\nEsc: fechar aba"),
            style="SidebarInfo.TLabel",
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 12))

        ttk.Button(
            lateral,
            text="Sair do sistema",
            style="Sidebar.TButton",
            command=self.sair,
        ).pack(fill="x", pady=2)

        # Notebook é a única área onde as "telas" dos módulos existem.
        self.notebook = ttk.Notebook(area_abas)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self._ao_mudar_aba)
        self.notebook.bind("<Button-2>", self._fechar_com_botao_meio)

        self._criar_aba_inicio()

    def _criar_aba_inicio(self):
        inicio = ttk.Frame(self.notebook, padding=28)
        self.notebook.add(inicio, text="Início")
        self.abas["inicio"] = inicio

        inicio.columnconfigure(0, weight=1)
        inicio.rowconfigure(3, weight=1)

        ttk.Label(
            inicio,
            text="Painel inicial",
            style="Titulo.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            inicio,
            text=(
                "Abra vários módulos pelo menu. Eles permanecerão nas abas, "
                "mas somente uma janela do sistema ficará aberta."
            ),
            style="Subtitulo.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(5, 24))

        cartao = ttk.LabelFrame(inicio, text="Navegação", padding=22)
        cartao.grid(row=2, column=0, sticky="ew")
        cartao.columnconfigure(0, weight=1)

        ttk.Label(
            cartao,
            text=(
                "• Clique em um módulo para abrir uma aba.\n\n"
                "• Se o módulo já estiver aberto, ele será apenas selecionado.\n\n"
                "• Esc fecha a aba atual. A aba Início não pode ser fechada.\n\n"
                "• Alt + ← volta para a aba anterior sem fechá-la.\n\n"
                "• F11 alterna a tela cheia. F1 mostra todos os atalhos do teclado."
            ),
            style="Painel.TLabel",
            justify="left",
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, sticky="nw")

        self.notebook.select(inicio)
        self.aba_atual = str(inicio)

    def abrir_aba(self, chave, titulo, classe, *args):
        """Abre o módulo uma vez e mantém a aba viva enquanto não for fechada."""
        if chave in self.abas:
            frame = self.abas[chave]
            if str(frame) in self.notebook.tabs():
                self.notebook.select(frame)
                self._atualizar_aba(frame)
                return

        frame = classe(self.notebook, *args)
        self.abas[chave] = frame
        self.notebook.add(frame, text=titulo)
        self.notebook.select(frame)


    def _frame_atual(self):
        atual = self.notebook.select()
        if not atual:
            return None
        try:
            return self.root.nametowidget(atual)
        except Exception:
            return None

    def _executar_atalho_aba(self, nome_metodo):
        frame = self._frame_atual()
        metodo = getattr(frame, nome_metodo, None) if frame is not None else None
        if callable(metodo):
            return metodo() or "break"
        return "break"

    def abrir_caixa_atalho(self, _evento=None):
        self.abrir_aba("caixa", "Frente de Caixa", TelaCaixa, self.funcionario)
        frame = self.abas.get("caixa")
        if frame is not None:
            frame.atalho_f2()
        return "break"

    def abrir_caixa_diario_atalho(self, _evento=None):
        self.abrir_aba(
            "caixa_diario",
            "Caixa Diário",
            TelaCaixaDiario,
            self.funcionario,
        )
        return "break"

    def abrir_ia_atalho(self, _evento=None):
        self.abrir_aba("localizador", "Assistente Local", TelaLocalizador)
        return "break"

    def mostrar_atalhos(self, _evento=None):
        messagebox.showinfo(
            "Atalhos do sistema",
            "Enter — próximo campo / confirmar ação\n"
            "F1  — mostrar atalhos\n"
            "F2  — abrir a frente de caixa / procurar produtos\n"
            "F3  — abrir o Caixa Diário\n"
            "F4  — avançar a etapa da venda ou finalizar\n"
            "F5  — cancelar e apagar a venda atual\n"
            "Ctrl+I — abrir o Assistente Local\n"
            "Esc — fechar a aba atual\n"
            "Alt+← — voltar para a aba anterior\n"
            "F11 — tela cheia\n"
            "Ctrl+M — alternar janela/maximizado",
        )
        return "break"

    def _ao_mudar_aba(self, _evento=None):
        nova = self.notebook.select()
        if not nova:
            return

        if self.aba_atual and nova != self.aba_atual:
            if not self._mudanca_por_historico:
                self.historico.append(self.aba_atual)

        self.aba_atual = nova
        self._mudanca_por_historico = False

        widget = self.root.nametowidget(nova)
        self._atualizar_aba(widget)

    def _atualizar_aba(self, frame):
        """Atualiza listagens ao voltar para uma aba, sem recriar a tela."""
        ao_exibir = getattr(frame, "ao_exibir", None)
        if callable(ao_exibir):
            try:
                ao_exibir()
            except Exception:
                pass
            return

        carregar = getattr(frame, "carregar", None)
        if callable(carregar):
            try:
                carregar()
            except Exception:
                # A própria tela tratará erros quando necessário.
                pass

        carregar_produtos = getattr(frame, "carregar_produtos", None)
        if callable(carregar_produtos):
            try:
                carregar_produtos()
            except Exception:
                pass

        carregar_clientes = getattr(frame, "carregar_clientes", None)
        if callable(carregar_clientes):
            try:
                carregar_clientes()
            except Exception:
                pass

    def voltar(self, _evento=None):
        """
        Volta para a aba visitada anteriormente sem fechar a aba atual.
        Se não houver histórico, retorna à aba Início.
        """
        abas_existentes = set(self.notebook.tabs())

        while self.historico:
            anterior = self.historico.pop()
            if anterior in abas_existentes and anterior != self.notebook.select():
                self._mudanca_por_historico = True
                self.notebook.select(anterior)
                return "break"

        inicio = self.abas.get("inicio")
        if inicio is not None and str(inicio) != self.notebook.select():
            self._mudanca_por_historico = True
            self.notebook.select(inicio)

        return "break"

    def fechar_aba_atual(self, _evento=None):
        atual = self.notebook.select()
        if not atual:
            return "break"

        inicio = self.abas.get("inicio")
        if inicio is not None and atual == str(inicio):
            return "break"

        widget = self.root.nametowidget(atual)

        pode_fechar = getattr(widget, "pode_fechar", None)
        if callable(pode_fechar) and not pode_fechar():
            return "break"

        chave_remover = None
        for chave, frame in self.abas.items():
            if frame is widget:
                chave_remover = chave
                break

        # Primeiro volta para uma aba existente; depois remove a atual.
        alvo = None
        existentes = set(self.notebook.tabs())
        while self.historico:
            candidato = self.historico.pop()
            if candidato in existentes and candidato != atual:
                alvo = candidato
                break

        if alvo is None and inicio is not None:
            alvo = str(inicio)

        if alvo:
            self._mudanca_por_historico = True
            self.notebook.select(alvo)

        self.notebook.forget(widget)
        widget.destroy()

        if chave_remover:
            self.abas.pop(chave_remover, None)

        self.historico = [x for x in self.historico if x != atual]
        return "break"

    def _fechar_com_botao_meio(self, evento):
        try:
            indice = self.notebook.index(f"@{evento.x},{evento.y}")
        except tk.TclError:
            return

        atual = self.notebook.select()
        alvo = self.notebook.tabs()[indice]
        self.notebook.select(alvo)
        self.fechar_aba_atual()

        if atual in self.notebook.tabs():
            self.notebook.select(atual)

    def sair(self):
        if confirmar_com_enter(self.notebook, "Sair", "Encerrar o sistema?"):
            self.root.destroy()
