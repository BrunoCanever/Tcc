import tkinter as tk
import calendar
from datetime import date, datetime, timedelta
from tkinter import ttk, messagebox

CORES = {
    "fundo": "#F3F6F9",
    "painel": "#FFFFFF",
    "primaria": "#1F4E78",
    "primaria_escura": "#173A5E",
    "secundaria": "#E8EEF5",
    "texto": "#1F2937",
    "texto_suave": "#64748B",
    "borda": "#D8E1EA",
}

def configurar_estilo(janela):
    try:
        janela.configure(bg=CORES["fundo"])
    except Exception:
        pass
    style = ttk.Style(janela)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", font=("Segoe UI", 10), background=CORES["fundo"], foreground=CORES["texto"])
    style.configure("TFrame", background=CORES["fundo"])
    style.configure("Painel.TFrame", background=CORES["painel"])
    style.configure("Sidebar.TFrame", background=CORES["primaria"])
    style.configure("Header.TFrame", background=CORES["painel"])
    style.configure("TLabel", background=CORES["fundo"], foreground=CORES["texto"])
    style.configure("Painel.TLabel", background=CORES["painel"], foreground=CORES["texto"])
    style.configure("Titulo.TLabel", background=CORES["fundo"], foreground=CORES["texto"], font=("Segoe UI Semibold", 20))
    style.configure("Subtitulo.TLabel", background=CORES["fundo"], foreground=CORES["texto_suave"], font=("Segoe UI", 10))
    style.configure("Cabecalho.TLabel", background=CORES["painel"], foreground=CORES["texto"], font=("Segoe UI Semibold", 18))
    style.configure("SidebarTitulo.TLabel", background=CORES["primaria"], foreground="#FFFFFF", font=("Segoe UI Semibold", 14))
    style.configure("SidebarInfo.TLabel", background=CORES["primaria"], foreground="#DCE8F3", font=("Segoe UI", 9))
    style.configure("TButton", font=("Segoe UI Semibold", 10), padding=(12, 8), relief="flat")
    style.configure("Primario.TButton", background=CORES["primaria"], foreground="#FFFFFF", borderwidth=0, padding=(14, 9))
    style.map("Primario.TButton", background=[("active", CORES["primaria_escura"]), ("pressed", CORES["primaria_escura"])])
    style.configure("Secundario.TButton", background=CORES["secundaria"], foreground=CORES["texto"], borderwidth=0, padding=(12, 8))
    style.map("Secundario.TButton", background=[("active", "#DCE6F0"), ("pressed", "#D2DFEB")])
    style.configure("Sidebar.TButton", background=CORES["primaria"], foreground="#FFFFFF", borderwidth=0, anchor="w", padding=(16, 10), font=("Segoe UI Semibold", 10))
    style.map("Sidebar.TButton", background=[("active", CORES["primaria_escura"]), ("pressed", CORES["primaria_escura"])], foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")])
    style.configure("TEntry", fieldbackground="#FFFFFF", foreground=CORES["texto"], padding=7)
    style.configure("TCombobox", fieldbackground="#FFFFFF", foreground=CORES["texto"], padding=6)
    style.configure("TLabelframe", background=CORES["fundo"], bordercolor=CORES["borda"], relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=CORES["fundo"], foreground=CORES["texto"], font=("Segoe UI Semibold", 10))
    style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground=CORES["texto"], rowheight=30, borderwidth=0, font=("Segoe UI", 10))
    style.configure("Treeview.Heading", background=CORES["secundaria"], foreground=CORES["texto"], font=("Segoe UI Semibold", 10), relief="flat", padding=(8, 8))
    style.map("Treeview", background=[("selected", CORES["primaria"])], foreground=[("selected", "#FFFFFF")])

    style.configure("TNotebook", background=CORES["fundo"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure(
        "TNotebook.Tab",
        background=CORES["secundaria"],
        foreground=CORES["texto"],
        font=("Segoe UI Semibold", 9),
        padding=(10, 8),
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", CORES["painel"]), ("active", "#DCE6F0")],
        foreground=[("selected", CORES["primaria"])],
    )

    # Enter confirma qualquer botão ttk que esteja com foco.
    def _enter_botao(evento):
        try:
            if isinstance(evento.widget, ttk.Button):
                evento.widget.invoke()
                return "break"
        except Exception:
            pass

    janela.bind_class("TButton", "<Return>", _enter_botao)
    janela.bind_class("TButton", "<KP_Enter>", _enter_botao)

def _geometria_centralizada(janela, largura, altura):
    janela.update_idletasks()
    sw, sh = janela.winfo_screenwidth(), janela.winfo_screenheight()
    largura = min(largura, max(700, sw - 80))
    altura = min(altura, max(500, sh - 100))
    x, y = max(0, (sw-largura)//2), max(0, (sh-altura)//2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

def maximizar_janela(janela):
    janela.attributes("-fullscreen", False)
    janela.resizable(True, True)
    try:
        janela.state("zoomed")
    except tk.TclError:
        try:
            janela.attributes("-zoomed", True)
        except tk.TclError:
            janela.geometry(f"{janela.winfo_screenwidth()}x{janela.winfo_screenheight()}+0+0")

def modo_janela(janela, largura=1180, altura=760):
    janela.attributes("-fullscreen", False)
    janela.resizable(True, True)
    try:
        janela.state("normal")
    except tk.TclError:
        pass
    _geometria_centralizada(janela, largura, altura)

def alternar_tela_cheia(janela):
    janela.attributes("-fullscreen", not bool(janela.attributes("-fullscreen")))

def sair_tela_cheia(janela):
    janela.attributes("-fullscreen", False)

def alternar_maximizado(janela, largura=1180, altura=760):
    try:
        estado = janela.state()
    except tk.TclError:
        estado = "normal"
    if estado == "zoomed":
        modo_janela(janela, largura, altura)
    else:
        maximizar_janela(janela)

def centralizar_janela(janela, largura=1000, altura=650, maximizada=True):
    configurar_estilo(janela)
    janela.minsize(min(900, largura), min(560, altura))
    janela.bind("<F11>", lambda e: alternar_tela_cheia(janela))
    # Esc é reservado para fechar a aba atual na janela principal.
    janela.bind("<Control-m>", lambda e: alternar_maximizado(janela, largura, altura))
    janela.bind("<Control-M>", lambda e: alternar_maximizado(janela, largura, altura))
    if maximizada:
        janela.after(40, lambda: maximizar_janela(janela))
    else:
        janela.after(10, lambda: modo_janela(janela, largura, altura))

def limpar_tree(tree):
    for item in tree.get_children():
        tree.delete(item)

def mostrar_erro(erro):
    texto = str(erro).strip()

    # Em trocas rápidas de etapa/aba o Tk pode disparar um callback tardio de
    # um widget já destruído. Isso gera um "invalid command name" interno do
    # próprio toolkit e não representa erro real de negócio para o usuário.
    if (
        texto.startswith("invalid command name")
        and ".!" in texto
        and any(
            parte in texto.lower()
            for parte in ("combobox", "treeview", "labelframe", "notebook")
        )
    ):
        return

    messagebox.showerror("Erro", texto)

def criar_tree(parent, colunas, altura=14):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, padx=14, pady=14)
    tree = ttk.Treeview(frame, columns=[c[0] for c in colunas], show="headings", height=altura)
    for nome, titulo, largura in colunas:
        tree.heading(nome, text=titulo)
        tree.column(nome, width=largura, minwidth=45, anchor="w", stretch=True)
    sy = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    sx = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tree.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return tree

def parse_combo_id(valor):
    if not valor:
        return None
    return int(str(valor).split(" - ", 1)[0])


def ativar_enter_botao(botao):
    """Permite confirmar um botão focado usando Enter."""
    def executar(_evento=None):
        try:
            if str(botao.cget("state")) != "disabled":
                botao.invoke()
        except Exception:
            pass
        return "break"

    botao.bind("<Return>", executar)
    botao.bind("<KP_Enter>", executar)
    return botao


def vincular_enter_acao(widget, comando):
    """Executa uma ação ao pressionar Enter no widget."""
    def executar(_evento=None):
        comando()
        return "break"

    widget.bind("<Return>", executar)
    widget.bind("<KP_Enter>", executar)
    return widget


def vincular_fluxo_enter(container, botao_final=None):
    """
    Enter percorre Entry/Combobox/Checkbutton do formulário.
    No último campo, o foco vai para o botão principal; outro Enter confirma.
    """
    campos = []

    def coletar(widget):
        for filho in widget.winfo_children():
            if isinstance(filho, (ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                campos.append(filho)
            coletar(filho)

    coletar(container)

    def utilizavel(widget):
        try:
            return str(widget.cget("state")) not in {"disabled"}
        except Exception:
            return True

    def focar_indice(indice):
        for pos in range(indice, len(campos)):
            if utilizavel(campos[pos]):
                campos[pos].focus_set()
                try:
                    campos[pos].selection_range(0, "end")
                except Exception:
                    pass
                return
        if botao_final is not None:
            botao_final.focus_set()

    for i, campo in enumerate(campos):
        def avancar(_evento=None, indice=i + 1):
            focar_indice(indice)
            return "break"
        campo.bind("<Return>", avancar)
        campo.bind("<KP_Enter>", avancar)

    if botao_final is not None:
        ativar_enter_botao(botao_final)

    return campos


def confirmar_com_enter(parent, titulo, mensagem):
    """
    Confirmação dentro da mesma janela do sistema.
    Enter confirma; Esc cancela. Não cria Toplevel.
    """
    resultado = tk.BooleanVar(master=parent, value=False)
    concluido = tk.BooleanVar(master=parent, value=False)
    root = parent.winfo_toplevel()

    caixa = ttk.Frame(
        root,
        style="Painel.TFrame",
        padding=20,
        relief="solid",
        borderwidth=1,
    )
    caixa.place(relx=0.5, rely=0.5, anchor="center", width=460)
    caixa.lift()

    ttk.Label(
        caixa,
        text=titulo,
        style="Cabecalho.TLabel",
    ).pack(anchor="w")

    ttk.Label(
        caixa,
        text=mensagem,
        style="Painel.TLabel",
        wraplength=410,
        justify="left",
    ).pack(anchor="w", pady=(10, 18))

    botoes = ttk.Frame(caixa, style="Painel.TFrame")
    botoes.pack(fill="x")

    def finalizar(valor):
        resultado.set(bool(valor))
        concluido.set(True)

    botao_nao = ttk.Button(
        botoes,
        text="Cancelar (Esc)",
        style="Secundario.TButton",
        command=lambda: finalizar(False),
    )
    botao_nao.pack(side="left")

    botao_sim = ttk.Button(
        botoes,
        text="Confirmar (Enter)",
        style="Primario.TButton",
        command=lambda: finalizar(True),
    )
    botao_sim.pack(side="right")

    botao_sim.bind("<Return>", lambda _e: (finalizar(True), "break")[1])
    botao_sim.bind("<KP_Enter>", lambda _e: (finalizar(True), "break")[1])
    botao_sim.bind("<Escape>", lambda _e: (finalizar(False), "break")[1])
    botao_nao.bind("<Return>", lambda _e: (finalizar(False), "break")[1])
    botao_nao.bind("<KP_Enter>", lambda _e: (finalizar(False), "break")[1])
    botao_nao.bind("<Escape>", lambda _e: (finalizar(False), "break")[1])
    caixa.bind("<Escape>", lambda _e: (finalizar(False), "break")[1])

    root.update_idletasks()
    try:
        botao_sim.focus_force()
    except Exception:
        botao_sim.focus_set()
    root.wait_variable(concluido)

    valor = bool(resultado.get())
    caixa.destroy()
    return valor


def solicitar_texto_enter(
    parent,
    titulo,
    mensagem,
    valor_inicial="",
    ocultar=False,
):
    """
    Pequeno campo de entrada na mesma janela.
    Enter confirma e Esc cancela.
    """
    root = parent.winfo_toplevel()
    concluido = tk.BooleanVar(master=parent, value=False)
    cancelado = tk.BooleanVar(master=parent, value=False)
    valor = tk.StringVar(master=parent, value=valor_inicial or "")

    caixa = ttk.Frame(
        root,
        style="Painel.TFrame",
        padding=20,
        relief="solid",
        borderwidth=1,
    )
    caixa.place(relx=0.5, rely=0.5, anchor="center", width=460)
    caixa.lift()

    ttk.Label(
        caixa,
        text=titulo,
        style="Cabecalho.TLabel",
    ).pack(anchor="w")

    ttk.Label(
        caixa,
        text=mensagem,
        style="Painel.TLabel",
        wraplength=410,
        justify="left",
    ).pack(anchor="w", pady=(10, 10))

    entrada = ttk.Entry(
        caixa,
        textvariable=valor,
        show="*" if ocultar else "",
    )
    entrada.pack(fill="x", pady=(0, 14))

    botoes = ttk.Frame(caixa, style="Painel.TFrame")
    botoes.pack(fill="x")

    def confirmar(_evento=None):
        cancelado.set(False)
        concluido.set(True)
        return "break"

    def cancelar(_evento=None):
        cancelado.set(True)
        concluido.set(True)
        return "break"

    ttk.Button(
        botoes,
        text="Cancelar (Esc)",
        style="Secundario.TButton",
        command=cancelar,
    ).pack(side="left")

    ttk.Button(
        botoes,
        text="Confirmar (Enter)",
        style="Primario.TButton",
        command=confirmar,
    ).pack(side="right")

    entrada.bind("<Return>", confirmar)
    entrada.bind("<KP_Enter>", confirmar)
    entrada.bind("<Escape>", cancelar)
    caixa.bind("<Escape>", cancelar)

    root.update_idletasks()
    try:
        entrada.focus_force()
    except Exception:
        entrada.focus_set()
    entrada.selection_range(0, "end")
    root.wait_variable(concluido)

    resposta = None if cancelado.get() else valor.get()
    caixa.destroy()
    return resposta


MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

DIAS_SEMANA_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def _data_iso_segura(valor, padrao=None):
    """Converte YYYY-MM-DD/date/datetime em date, sem deslocamento de fuso."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if valor:
        try:
            return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass
    return padrao or date.today()


def solicitar_data(parent, titulo="Selecionar data", valor_inicial=None):
    """
    Seletor de data dentro da própria janela do sistema.

    Não cria Toplevel. Possui atalhos para Hoje, Amanhã, +7, +15 e +30 dias,
    navegação por mês e seleção pelo calendário. Retorna YYYY-MM-DD ou None.
    """
    root = parent.winfo_toplevel()
    concluido = tk.BooleanVar(master=parent, value=False)
    cancelado = tk.BooleanVar(master=parent, value=False)

    inicial = _data_iso_segura(valor_inicial, date.today())
    selecionada = {"data": inicial}
    mes_atual = {"ano": inicial.year, "mes": inicial.month}

    painel = ttk.Frame(
        root,
        style="Painel.TFrame",
        padding=18,
        relief="solid",
        borderwidth=1,
    )
    painel.place(relx=0.5, rely=0.5, anchor="center", width=620, height=535)
    painel.lift()

    ttk.Label(
        painel,
        text=titulo,
        style="Cabecalho.TLabel",
    ).pack(anchor="w")

    ttk.Label(
        painel,
        text="Escolha uma opção rápida ou selecione um dia no calendário.",
        style="Painel.TLabel",
    ).pack(anchor="w", pady=(4, 12))

    atalhos = ttk.Frame(painel, style="Painel.TFrame")
    atalhos.pack(fill="x", pady=(0, 10))

    calendario_area = ttk.Frame(painel, style="Painel.TFrame")
    calendario_area.pack(fill="both", expand=True)

    cabecalho = ttk.Frame(calendario_area, style="Painel.TFrame")
    cabecalho.pack(fill="x", pady=(2, 8))

    grade = ttk.Frame(calendario_area, style="Painel.TFrame")
    grade.pack(fill="both", expand=True)

    rodape = ttk.Frame(painel, style="Painel.TFrame")
    rodape.pack(fill="x", pady=(10, 0))

    texto_selecionada = tk.StringVar(master=parent)

    def texto_data(d):
        return f"{d.strftime('%d/%m/%Y')} ({d.isoformat()})"

    def atualizar_texto():
        texto_selecionada.set(f"Data selecionada: {texto_data(selecionada['data'])}")

    def confirmar(_evento=None):
        cancelado.set(False)
        concluido.set(True)
        return "break"

    def cancelar(_evento=None):
        cancelado.set(True)
        concluido.set(True)
        return "break"

    def escolher(d, confirmar_agora=False):
        selecionada["data"] = d
        mes_atual["ano"] = d.year
        mes_atual["mes"] = d.month
        atualizar_texto()
        desenhar_calendario()
        if confirmar_agora:
            confirmar()

    def escolher_offset(dias):
        escolher(date.today() + timedelta(days=dias))

    opcoes = [
        ("Hoje", 0),
        ("Amanhã", 1),
        ("+7 dias", 7),
        ("+15 dias", 15),
        ("+30 dias", 30),
    ]
    for texto, dias in opcoes:
        ttk.Button(
            atalhos,
            text=texto,
            style="Secundario.TButton",
            command=lambda d=dias: escolher_offset(d),
        ).pack(side="left", padx=(0, 5))

    lbl_mes = ttk.Label(
        cabecalho,
        text="",
        style="Painel.TLabel",
        font=("Segoe UI Semibold", 12),
        anchor="center",
    )
    lbl_mes.pack(side="left", fill="x", expand=True)

    def mover_mes(delta):
        ano = mes_atual["ano"]
        mes = mes_atual["mes"] + delta
        if mes < 1:
            mes = 12
            ano -= 1
        elif mes > 12:
            mes = 1
            ano += 1
        mes_atual["ano"] = ano
        mes_atual["mes"] = mes
        desenhar_calendario()

    ttk.Button(
        cabecalho,
        text="← Mês anterior",
        style="Secundario.TButton",
        command=lambda: mover_mes(-1),
    ).pack(side="left")

    # Reordena visualmente: anterior | título | próximo
    lbl_mes.pack_forget()
    lbl_mes.pack(side="left", fill="x", expand=True, padx=8)

    ttk.Button(
        cabecalho,
        text="Próximo mês →",
        style="Secundario.TButton",
        command=lambda: mover_mes(1),
    ).pack(side="right")

    def desenhar_calendario():
        for filho in grade.winfo_children():
            filho.destroy()

        ano = mes_atual["ano"]
        mes = mes_atual["mes"]
        lbl_mes.config(text=f"{MESES_PT[mes - 1]} {ano}")

        for coluna, nome in enumerate(DIAS_SEMANA_PT):
            grade.columnconfigure(coluna, weight=1, uniform="dias")
            ttk.Label(
                grade,
                text=nome,
                style="Painel.TLabel",
                font=("Segoe UI Semibold", 9),
                anchor="center",
            ).grid(row=0, column=coluna, sticky="ew", padx=2, pady=(0, 4))

        semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(ano, mes)
        while len(semanas) < 6:
            semanas.append([0] * 7)

        hoje = date.today()
        for linha, semana in enumerate(semanas, start=1):
            grade.rowconfigure(linha, weight=1)
            for coluna, dia in enumerate(semana):
                if dia == 0:
                    ttk.Label(
                        grade,
                        text="",
                        style="Painel.TLabel",
                    ).grid(row=linha, column=coluna, sticky="nsew", padx=2, pady=2)
                    continue

                d = date(ano, mes, dia)
                estilo = "Primario.TButton" if d == selecionada["data"] else "Secundario.TButton"
                texto = str(dia)
                if d == hoje and d != selecionada["data"]:
                    texto = f"{dia} •"

                botao = ttk.Button(
                    grade,
                    text=texto,
                    style=estilo,
                    command=lambda data=d: escolher(data),
                    width=5,
                )
                botao.grid(row=linha, column=coluna, sticky="nsew", padx=2, pady=2)
                botao.bind("<Double-1>", lambda _e, data=d: escolher(data, True))

    ttk.Label(
        rodape,
        textvariable=texto_selecionada,
        style="Painel.TLabel",
    ).pack(side="left")

    ttk.Button(
        rodape,
        text="Cancelar (Esc)",
        style="Secundario.TButton",
        command=cancelar,
    ).pack(side="right")

    botao_usar = ttk.Button(
        rodape,
        text="Usar data (Enter)",
        style="Primario.TButton",
        command=confirmar,
    )
    botao_usar.pack(side="right", padx=(0, 8))

    atualizar_texto()
    desenhar_calendario()

    painel.bind("<Escape>", cancelar)
    painel.bind("<Return>", confirmar)
    painel.bind("<KP_Enter>", confirmar)
    botao_usar.bind("<Escape>", cancelar)
    botao_usar.bind("<Return>", confirmar)
    botao_usar.bind("<KP_Enter>", confirmar)

    root.update_idletasks()
    try:
        botao_usar.focus_force()
    except Exception:
        botao_usar.focus_set()

    root.wait_variable(concluido)
    resposta = None if cancelado.get() else selecionada["data"].isoformat()
    painel.destroy()
    return resposta


def vincular_seletor_data(entry, variavel, titulo="Selecionar data"):
    """
    Transforma um Entry de data em seletor por calendário.
    Clique ou Enter abre o calendário. O valor continua no formato YYYY-MM-DD.
    """
    def abrir(_evento=None):
        try:
            if str(entry.cget("state")) == "disabled":
                return "break"
        except Exception:
            pass

        atual = variavel.get().strip() if hasattr(variavel, "get") else ""
        valor = solicitar_data(entry, titulo, valor_inicial=atual or date.today().isoformat())
        if valor:
            variavel.set(valor)
        try:
            entry.focus_set()
        except Exception:
            pass
        return "break"

    entry.bind("<Button-1>", abrir)
    entry.bind("<Return>", abrir)
    entry.bind("<KP_Enter>", abrir)
    return entry
