import tkinter as tk
from tkinter import ttk, messagebox

from funcoes.caixa_diario_funcoes import (
    abrir_caixa,
    fechar_caixa,
    listar_atividades_caixa_hoje,
    registrar_movimentacao,
    resumo_caixa_hoje,
)
from funcoes.utils import moeda
from telas.helpers import (
    mostrar_erro,
    vincular_fluxo_enter,
    confirmar_com_enter,
)


class TelaCaixaDiario(ttk.Frame):
    """
    Caixa Diário com duas abas internas:

    - Resumo do caixa;
    - Vendas e movimentações do dia.

    Sangria e acréscimo são registrados por uma pequena telinha dentro da
    própria aba, sem criar outra janela do Windows.
    """

    def __init__(self, master, funcionario):
        super().__init__(master)
        self.funcionario = funcionario

        self.valor_abertura = tk.StringVar(value="0")
        self.mov_tipo = tk.StringVar(value="SANGRIA")
        self.mov_valor = tk.StringVar()
        self.mov_motivo = tk.StringVar()
        self.valor_contado = tk.StringVar()
        self.obs_fechamento = tk.StringVar()

        self.aba_atual = "RESUMO"
        self.popup_movimentacao_visivel = False

        self.area = ttk.Frame(self, padding=16)
        self.area.pack(fill="both", expand=True)

        self.carregar()

    def ao_exibir(self):
        self.carregar(self.aba_atual)

    # ============================================================
    # Montagem principal
    # ============================================================
    def carregar(self, aba=None):
        if aba:
            self.aba_atual = aba

        for widget in self.area.winfo_children():
            widget.destroy()

        self.popup_movimentacao_visivel = False

        try:
            resumo = resumo_caixa_hoje()
        except Exception as erro:
            mostrar_erro(erro)
            return

        topo = ttk.Frame(self.area)
        topo.pack(fill="x", pady=(0, 12))

        ttk.Label(
            topo,
            text="Caixa Diário",
            style="Titulo.TLabel",
        ).pack(side="left")

        ttk.Label(
            topo,
            text=(
                "Resumo, vendas, sangrias e acréscimos do caixa do dia"
            ),
            style="Subtitulo.TLabel",
        ).pack(side="right")

        if not resumo:
            self._montar_abertura()
            return

        self.resumo_atual = resumo

        self.notebook_caixa = ttk.Notebook(self.area)
        self.notebook_caixa.pack(fill="both", expand=True)

        self.aba_resumo = ttk.Frame(
            self.notebook_caixa,
            padding=12,
        )
        self.aba_atividades = ttk.Frame(
            self.notebook_caixa,
            padding=12,
        )

        self.notebook_caixa.add(
            self.aba_resumo,
            text="Resumo do caixa",
        )
        self.notebook_caixa.add(
            self.aba_atividades,
            text="Vendas e movimentações",
        )

        self._montar_aba_resumo(resumo)
        self._montar_aba_atividades(resumo)

        self.notebook_caixa.bind(
            "<<NotebookTabChanged>>",
            self._ao_trocar_aba,
        )

        if self.aba_atual == "ATIVIDADES":
            self.notebook_caixa.select(self.aba_atividades)
        else:
            self.notebook_caixa.select(self.aba_resumo)
            self.aba_atual = "RESUMO"

    def _ao_trocar_aba(self, _evento=None):
        try:
            selecionada = self.notebook_caixa.select()
            if selecionada == str(self.aba_atividades):
                self.aba_atual = "ATIVIDADES"
                self.atualizar_atividades()
            else:
                self.aba_atual = "RESUMO"
        except Exception:
            pass

    # ============================================================
    # Abertura
    # ============================================================
    def _montar_abertura(self):
        quadro = ttk.LabelFrame(
            self.area,
            text="Abrir caixa de hoje",
            padding=24,
        )
        quadro.pack(
            fill="x",
            padx=150,
            pady=(70, 10),
        )
        quadro.columnconfigure(1, weight=1)

        ttk.Label(
            quadro,
            text=(
                "Informe o dinheiro que já existe na gaveta no início do "
                "dia como fundo de troco."
            ),
            wraplength=760,
            justify="left",
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 18),
        )

        ttk.Label(
            quadro,
            text="Valor de abertura (R$)",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=8,
        )

        entrada = ttk.Entry(
            quadro,
            textvariable=self.valor_abertura,
        )
        entrada.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=8,
        )

        self.btn_abrir_caixa = ttk.Button(
            quadro,
            text="ABRIR CAIXA",
            style="Primario.TButton",
            command=self.abrir,
        )
        self.btn_abrir_caixa.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(16, 0),
        )

        vincular_fluxo_enter(
            quadro,
            self.btn_abrir_caixa,
        )
        entrada.focus_set()

    def abrir(self):
        try:
            abrir_caixa(
                self.funcionario["id_funcionario"],
                self.valor_abertura.get() or "0",
            )
            self.aba_atual = "RESUMO"
            self.carregar("RESUMO")
        except Exception as erro:
            mostrar_erro(erro)

    # ============================================================
    # Aba Resumo
    # ============================================================
    def _montar_aba_resumo(self, resumo):
        self._montar_cards_resumo(
            self.aba_resumo,
            resumo,
        )
        self._montar_formas_pagamento(
            self.aba_resumo,
            resumo,
        )

        if resumo["status"] == "ABERTO":
            self._montar_fechamento(
                self.aba_resumo,
            )
        else:
            self._montar_fechado(
                self.aba_resumo,
                resumo,
            )

    def _montar_cards_resumo(self, parent, resumo):
        status = resumo["status"]

        cab = ttk.LabelFrame(
            parent,
            text=(
                f"Caixa de {resumo['data_caixa']} — {status}"
            ),
            padding=14,
        )
        cab.pack(fill="x", pady=(0, 12))

        dados = [
            ("Abertura", resumo["valor_abertura"]),
            (
                "Vendas em dinheiro",
                resumo["vendas_dinheiro"],
            ),
            (
                "Acréscimos no caixa",
                resumo["acrescimos_caixa"],
            ),
            ("Sangrias", resumo["sangrias"]),
            (
                "Saldo esperado",
                resumo["saldo_esperado"],
            ),
            (
                "Total de vendas",
                resumo["total_vendas"],
            ),
        ]

        for i, (titulo, valor) in enumerate(dados):
            card = ttk.Frame(
                cab,
                padding=(10, 8),
            )
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=3,
            )

            ttk.Label(
                card,
                text=titulo,
                style="Subtitulo.TLabel",
            ).pack(anchor="w")

            ttk.Label(
                card,
                text=moeda(valor),
                font=("Segoe UI Semibold", 13),
            ).pack(
                anchor="w",
                pady=(4, 0),
            )

            cab.columnconfigure(i, weight=1)

    def _montar_formas_pagamento(self, parent, resumo):
        quadro = ttk.LabelFrame(
            parent,
            text="Vendas por forma de pagamento",
            padding=12,
        )
        quadro.pack(
            fill="x",
            pady=(0, 12),
        )

        formas = [
            "DINHEIRO",
            "PIX",
            "CARTAO_CREDITO",
            "CARTAO_DEBITO",
            "CREDIARIO",
        ]

        for i, forma in enumerate(formas):
            coluna = ttk.Frame(
                quadro,
                padding=(8, 4),
            )
            coluna.grid(
                row=0,
                column=i,
                sticky="nsew",
            )

            ttk.Label(
                coluna,
                text=forma.replace("_", " ").title(),
                style="Subtitulo.TLabel",
            ).pack(anchor="w")

            ttk.Label(
                coluna,
                text=moeda(
                    resumo["formas"].get(forma, 0)
                ),
                font=("Segoe UI Semibold", 12),
            ).pack(
                anchor="w",
                pady=(3, 0),
            )

            quadro.columnconfigure(i, weight=1)

    def _montar_fechamento(self, parent):
        quadro = ttk.LabelFrame(
            parent,
            text="Fechamento do caixa",
            padding=14,
        )
        quadro.pack(
            fill="x",
            pady=(0, 12),
        )
        quadro.columnconfigure(1, weight=1)

        ttk.Label(
            quadro,
            text="Dinheiro contado na gaveta (R$)",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        contado = ttk.Entry(
            quadro,
            textvariable=self.valor_contado,
        )
        contado.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 10),
            pady=6,
        )

        ttk.Label(
            quadro,
            text="Observação do fechamento",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        obs = ttk.Entry(
            quadro,
            textvariable=self.obs_fechamento,
        )
        obs.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, 10),
            pady=6,
        )

        self.btn_fechar_caixa = ttk.Button(
            quadro,
            text="FECHAR CAIXA",
            command=self.fechar,
        )
        self.btn_fechar_caixa.grid(
            row=0,
            column=2,
            rowspan=2,
            sticky="nsew",
        )

        vincular_fluxo_enter(
            quadro,
            self.btn_fechar_caixa,
        )

    def fechar(self):
        if not confirmar_com_enter(
            self,
            "Fechar Caixa Diário",
            (
                "Confirmar o fechamento do caixa de hoje?\n\n"
                "Enquanto estiver fechado, ele não poderá receber "
                "novas vendas ou movimentações. Você poderá reabri-lo "
                "depois, se necessário."
            ),
        ):
            return

        try:
            resultado = fechar_caixa(
                self.funcionario["id_funcionario"],
                self.valor_contado.get(),
                self.obs_fechamento.get(),
            )

            diferenca = resultado["diferenca"]

            if diferenca == 0:
                situacao = "Caixa conferido sem diferença."
            elif diferenca > 0:
                situacao = (
                    f"Sobra de {moeda(diferenca)}."
                )
            else:
                situacao = (
                    f"Falta de {moeda(abs(diferenca))}."
                )

            messagebox.showinfo(
                "Caixa fechado",
                (
                    f"Saldo esperado: "
                    f"{moeda(resultado['saldo_esperado'])}\n"
                    f"Dinheiro contado: "
                    f"{moeda(resultado['valor_contado'])}\n"
                    f"{situacao}"
                ),
            )

            self.carregar("RESUMO")

        except Exception as erro:
            mostrar_erro(erro)

    def reabrir(self):
        if not confirmar_com_enter(
            self,
            "Reabrir Caixa Diário",
            (
                "Reabrir o caixa de hoje?\n\n"
                "As vendas e movimentações já registradas serão mantidas. "
                "O caixa voltará a aceitar novas vendas, sangrias e acréscimos."
            ),
        ):
            return

        try:
            abrir_caixa(
                self.funcionario["id_funcionario"],
                self.resumo_atual.get("valor_abertura", 0),
            )
            messagebox.showinfo(
                "Caixa reaberto",
                "O Caixa Diário foi reaberto e já pode receber novas vendas.",
            )
            self.valor_contado.set("")
            self.obs_fechamento.set("")
            self.carregar("RESUMO")
        except Exception as erro:
            mostrar_erro(erro)

    def _montar_fechado(self, parent, resumo):
        quadro = ttk.LabelFrame(
            parent,
            text="Fechamento registrado",
            padding=14,
        )
        quadro.pack(
            fill="x",
            pady=(0, 12),
        )

        diferenca = resumo.get("diferenca")

        ttk.Label(
            quadro,
            text=(
                f"Fechado por: "
                f"{resumo.get('funcionario_fechamento') or '-'}\n"
                f"Dinheiro contado: "
                f"{moeda(resumo.get('valor_contado') or 0)}\n"
                f"Saldo esperado no fechamento: "
                f"{moeda(resumo.get('saldo_esperado_fechamento') or 0)}\n"
                f"Diferença: {moeda(diferenca or 0)}\n"
                f"Observação: "
                f"{resumo.get('observacao_fechamento') or '-'}"
            ),
            justify="left",
        ).pack(anchor="w")

        rodape = ttk.Frame(quadro)
        rodape.pack(fill="x", pady=(14, 0))

        ttk.Label(
            rodape,
            text=(
                "Se precisar continuar as vendas no mesmo dia, reabra o caixa. "
                "Todo o histórico já registrado será mantido."
            ),
            style="Subtitulo.TLabel",
        ).pack(side="left")

        self.btn_reabrir_caixa = ttk.Button(
            rodape,
            text="REABRIR CAIXA",
            style="Primario.TButton",
            command=self.reabrir,
        )
        self.btn_reabrir_caixa.pack(side="right")
        vincular_fluxo_enter(rodape, self.btn_reabrir_caixa)

    # ============================================================
    # Aba Vendas e movimentações
    # ============================================================
    def _montar_aba_atividades(self, resumo):
        barra = ttk.Frame(self.aba_atividades)
        barra.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            barra,
            text="Movimentação completa do dia",
            font=("Segoe UI Semibold", 14),
        ).pack(side="left")

        ttk.Label(
            barra,
            text=(
                "Vendas, sangrias e acréscimos em ordem de horário"
            ),
            style="Subtitulo.TLabel",
        ).pack(
            side="left",
            padx=(12, 0),
        )

        estado = (
            "normal"
            if resumo["status"] == "ABERTO"
            else "disabled"
        )

        self.btn_acrescimo = ttk.Button(
            barra,
            text="Acréscimo",
            style="Secundario.TButton",
            command=lambda: self.abrir_popup_movimentacao(
                "ACRESCIMO"
            ),
            state=estado,
        )
        self.btn_acrescimo.pack(
            side="right",
            padx=(5, 0),
        )

        self.btn_sangria = ttk.Button(
            barra,
            text="Sangria",
            style="Secundario.TButton",
            command=lambda: self.abrir_popup_movimentacao(
                "SANGRIA"
            ),
            state=estado,
        )
        self.btn_sangria.pack(
            side="right",
            padx=(5, 0),
        )

        ttk.Button(
            barra,
            text="Atualizar",
            style="Secundario.TButton",
            command=self.atualizar_atividades,
        ).pack(
            side="right",
            padx=(5, 0),
        )

        quadro = ttk.LabelFrame(
            self.aba_atividades,
            text="Vendas e movimentações do dia",
            padding=8,
        )
        quadro.pack(
            fill="both",
            expand=True,
        )

        frame_tree = ttk.Frame(quadro)
        frame_tree.pack(
            fill="both",
            expand=True,
        )

        colunas = (
            "hora",
            "tipo",
            "ref",
            "descricao",
            "pagamento",
            "valor",
            "funcionario",
            "status",
        )

        self.tree_atividades = ttk.Treeview(
            frame_tree,
            columns=colunas,
            show="headings",
            selectmode="browse",
        )

        configuracao = [
            ("hora", "Data / hora", 145),
            ("tipo", "Tipo", 105),
            ("ref", "Referência", 85),
            ("descricao", "Descrição", 260),
            ("pagamento", "Pagamento", 135),
            ("valor", "Valor", 110),
            ("funcionario", "Funcionário", 145),
            ("status", "Status", 100),
        ]

        for nome, titulo, largura in configuracao:
            self.tree_atividades.heading(
                nome,
                text=titulo,
            )
            self.tree_atividades.column(
                nome,
                width=largura,
                minwidth=65,
                anchor="w",
            )

        sy = ttk.Scrollbar(
            frame_tree,
            orient="vertical",
            command=self.tree_atividades.yview,
        )
        sx = ttk.Scrollbar(
            frame_tree,
            orient="horizontal",
            command=self.tree_atividades.xview,
        )

        self.tree_atividades.configure(
            yscrollcommand=sy.set,
            xscrollcommand=sx.set,
        )

        self.tree_atividades.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        sy.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        sx.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        frame_tree.rowconfigure(0, weight=1)
        frame_tree.columnconfigure(0, weight=1)

        self.lbl_total_atividades = ttk.Label(
            self.aba_atividades,
            style="Subtitulo.TLabel",
        )
        self.lbl_total_atividades.pack(
            anchor="e",
            pady=(6, 0),
        )

        self._criar_popup_movimentacao(
            self.aba_atividades
        )
        self.atualizar_atividades()

    def atualizar_atividades(self):
        if not hasattr(self, "tree_atividades"):
            return

        try:
            if not self.tree_atividades.winfo_exists():
                return
        except Exception:
            return

        try:
            dados = listar_atividades_caixa_hoje()

            for item in self.tree_atividades.get_children():
                self.tree_atividades.delete(item)

            total_vendas = 0
            total_movimentos = 0

            for atividade in dados:
                tipo = (
                    atividade.get("tipo")
                    or ""
                ).upper()

                valor = atividade.get("valor") or 0

                if tipo == "SANGRIA":
                    valor_texto = (
                        f"- {moeda(valor)}"
                    )
                    tipo_texto = "Sangria"
                    referencia = (
                        f"MOV-{atividade['referencia']}"
                    )
                    total_movimentos += 1

                elif tipo == "ACRESCIMO":
                    valor_texto = (
                        f"+ {moeda(valor)}"
                    )
                    tipo_texto = "Acréscimo"
                    referencia = (
                        f"MOV-{atividade['referencia']}"
                    )
                    total_movimentos += 1

                else:
                    valor_texto = moeda(valor)
                    tipo_texto = "Venda"
                    referencia = (
                        f"#{atividade['referencia']}"
                    )
                    total_vendas += 1

                data = atividade.get("data_hora")

                try:
                    data_texto = data.strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                except Exception:
                    data_texto = str(data or "")

                pagamento = (
                    atividade.get("forma_pagamento")
                    or "-"
                ).replace("_", " ").title()

                self.tree_atividades.insert(
                    "",
                    "end",
                    values=(
                        data_texto,
                        tipo_texto,
                        referencia,
                        atividade.get("descricao") or "-",
                        pagamento,
                        valor_texto,
                        atividade.get("funcionario") or "-",
                        atividade.get("status") or "-",
                    ),
                )

            self.lbl_total_atividades.config(
                text=(
                    f"{total_vendas} venda(s) • "
                    f"{total_movimentos} movimentação(ões) manual(is)"
                )
            )

        except Exception as erro:
            mostrar_erro(erro)

    # ============================================================
    # Popup compacto Sangria / Acréscimo
    # ============================================================
    def _criar_popup_movimentacao(self, parent):
        self.popup_movimentacao = ttk.LabelFrame(
            parent,
            text="Movimentação de caixa",
            padding=14,
        )
        self.popup_movimentacao.columnconfigure(
            1,
            weight=1,
        )

        self.lbl_popup_movimento = ttk.Label(
            self.popup_movimentacao,
            text="",
            font=("Segoe UI Semibold", 13),
        )
        self.lbl_popup_movimento.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )

        ttk.Label(
            self.popup_movimentacao,
            text="Valor (R$):",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        self.entry_mov_valor = ttk.Entry(
            self.popup_movimentacao,
            textvariable=self.mov_valor,
            width=22,
        )
        self.entry_mov_valor.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=6,
        )

        ttk.Label(
            self.popup_movimentacao,
            text="Motivo:",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        self.entry_mov_motivo = ttk.Entry(
            self.popup_movimentacao,
            textvariable=self.mov_motivo,
            width=28,
        )
        self.entry_mov_motivo.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=6,
        )

        botoes = ttk.Frame(
            self.popup_movimentacao
        )
        botoes.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )

        ttk.Button(
            botoes,
            text="Cancelar",
            style="Secundario.TButton",
            command=self.fechar_popup_movimentacao,
        ).pack(side="left")

        self.btn_registrar_movimento = ttk.Button(
            botoes,
            text="Registrar",
            style="Primario.TButton",
            command=self.registrar_movimento,
        )
        self.btn_registrar_movimento.pack(
            side="right"
        )

        self.entry_mov_valor.bind(
            "<Return>",
            lambda _e: self._focar(
                self.entry_mov_motivo
            ),
        )
        self.entry_mov_valor.bind(
            "<KP_Enter>",
            lambda _e: self._focar(
                self.entry_mov_motivo
            ),
        )

        self.entry_mov_motivo.bind(
            "<Return>",
            lambda _e: self._focar(
                self.btn_registrar_movimento
            ),
        )
        self.entry_mov_motivo.bind(
            "<KP_Enter>",
            lambda _e: self._focar(
                self.btn_registrar_movimento
            ),
        )

        self.popup_movimentacao.bind(
            "<Escape>",
            lambda _e: self.fechar_popup_movimentacao(),
        )
        self.entry_mov_valor.bind(
            "<Escape>",
            lambda _e: self.fechar_popup_movimentacao(),
        )
        self.entry_mov_motivo.bind(
            "<Escape>",
            lambda _e: self.fechar_popup_movimentacao(),
        )

    def abrir_popup_movimentacao(self, tipo):
        tipo = (tipo or "").upper()

        if tipo not in {"SANGRIA", "ACRESCIMO"}:
            return

        try:
            resumo = resumo_caixa_hoje()

            if (
                not resumo
                or resumo["status"] != "ABERTO"
            ):
                raise ValueError(
                    "O Caixa Diário precisa estar aberto "
                    "para registrar movimentações."
                )

            self.mov_tipo.set(tipo)
            self.mov_valor.set("")
            self.mov_motivo.set("")

            titulo = (
                "Sangria"
                if tipo == "SANGRIA"
                else "Acréscimo"
            )

            self.lbl_popup_movimento.config(
                text=titulo
            )
            self.popup_movimentacao.configure(
                text=titulo
            )

            self.popup_movimentacao.place(
                relx=0.5,
                rely=0.42,
                anchor="center",
                width=390,
                height=210,
            )
            self.popup_movimentacao.lift()
            self.popup_movimentacao_visivel = True

            self._focar(
                self.entry_mov_valor,
                selecionar=True,
            )

        except Exception as erro:
            mostrar_erro(erro)

    def fechar_popup_movimentacao(self):
        self.popup_movimentacao_visivel = False
        self.mov_valor.set("")
        self.mov_motivo.set("")

        if hasattr(self, "popup_movimentacao"):
            self.popup_movimentacao.place_forget()

        return "break"

    def registrar_movimento(self):
        try:
            registrar_movimentacao(
                self.funcionario["id_funcionario"],
                self.mov_tipo.get(),
                self.mov_valor.get(),
                self.mov_motivo.get(),
            )

            self.fechar_popup_movimentacao()
            self.aba_atual = "ATIVIDADES"
            self.carregar("ATIVIDADES")

        except Exception as erro:
            mostrar_erro(erro)

    def _focar(self, widget, selecionar=False):
        if widget is None:
            return "break"

        try:
            if widget.winfo_exists():
                widget.focus_set()
                if selecionar:
                    try:
                        widget.selection_range(
                            0,
                            "end",
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        return "break"
