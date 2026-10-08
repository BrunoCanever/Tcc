import queue
import threading
import tkinter as tk
from tkinter import ttk

from funcoes.ia_funcoes import responder_pergunta, status_ia
from telas.helpers import mostrar_erro


class TelaLocalizador(ttk.Frame):
    """Assistente local, somente leitura, para organização e estoque da loja."""

    def __init__(self, master):
        super().__init__(master)

        self.pergunta = tk.StringVar()
        self.status_texto = tk.StringVar()
        self._consultando = False
        self._consulta_id = 0
        self._fila_resultados = queue.Queue()
        self._after_fila = None
        self._after_animacao = None
        self._passo_animacao = 0

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)

        titulo_linha = ttk.Frame(frame)
        titulo_linha.pack(fill="x")

        ttk.Label(
            titulo_linha,
            text="Assistente Local da Loja",
            style="Titulo.TLabel",
        ).pack(side="left", anchor="w")

        ttk.Label(
            frame,
            text=(
                "Consulta organização, produtos e estoque usando somente o banco MySQL da loja. "
                "Não usa internet, chave de API ou créditos."
            ),
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(4, 4))

        ttk.Label(
            frame,
            text=(
                "Pergunte por nome/código, preço, saldo, localização, disponibilidade, reposição, "
                "categorias ou movimentações recentes. O assistente é somente leitura."
            ),
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        self.lbl_status = ttk.Label(frame, textvariable=self.status_texto)
        self.lbl_status.pack(anchor="w", pady=(0, 16))

        busca = ttk.LabelFrame(frame, text="Consulta", padding=14)
        busca.pack(fill="x")
        busca.columnconfigure(0, weight=1)

        self.entrada = ttk.Entry(busca, textvariable=self.pergunta)
        self.entrada.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entrada.bind("<Return>", lambda _e: self.buscar())
        self.entrada.bind("<KP_Enter>", lambda _e: self.buscar())

        self.btn_perguntar = ttk.Button(
            busca,
            text="Consultar",
            style="Primario.TButton",
            command=self.buscar,
        )
        self.btn_perguntar.grid(row=0, column=1)

        exemplos = ttk.Frame(frame)
        exemplos.pack(fill="x", pady=10)

        self.botoes_exemplo = []
        for texto in [
            "Quais produtos estão com estoque baixo?",
            "Onde fica o cimento CP II?",
            "Temos 20 sacos de cimento?",
            "Mostre um resumo do estoque",
        ]:
            botao = ttk.Button(
                exemplos,
                text=texto,
                style="Secundario.TButton",
                command=lambda t=texto: self.usar_exemplo(t),
            )
            botao.pack(side="left", padx=(0, 6))
            self.botoes_exemplo.append(botao)

        resposta_frame = ttk.LabelFrame(frame, text="Resposta", padding=10)
        resposta_frame.pack(fill="both", expand=True, pady=(6, 0))

        frame_texto = ttk.Frame(resposta_frame)
        frame_texto.pack(fill="both", expand=True)
        frame_texto.rowconfigure(0, weight=1)
        frame_texto.columnconfigure(0, weight=1)

        self.resposta = tk.Text(
            frame_texto,
            wrap="word",
            height=18,
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
        )
        self.resposta.grid(row=0, column=0, sticky="nsew")
        self.resposta.configure(state="disabled")

        scroll = ttk.Scrollbar(
            frame_texto,
            orient="vertical",
            command=self.resposta.yview,
        )
        scroll.grid(row=0, column=1, sticky="ns")
        self.resposta.configure(yscrollcommand=scroll.set)

        self.atualizar_status()
        self._mostrar_resposta(
            "Digite uma consulta sobre a loja ou use um dos exemplos acima.\n\n"
            "Exemplos adicionais: “qual o preço da areia média?”, “produtos sem estoque”, "
            "“últimas entradas de estoque”, “quais categorias existem?” e “produtos sem localização”."
        )
        self.entrada.focus_set()

    def ao_exibir(self):
        if not self._consultando:
            self.atualizar_status()

    def atualizar_status(self):
        self.status_texto.set(status_ia()["texto"])

    def usar_exemplo(self, texto):
        if self._consultando:
            return
        self.pergunta.set(texto)
        self.buscar()

    def _mostrar_resposta(self, texto):
        self.resposta.configure(state="normal")
        self.resposta.delete("1.0", "end")
        self.resposta.insert("1.0", str(texto or ""))
        self.resposta.configure(state="disabled")
        self.resposta.see("1.0")

    def _definir_consultando(self, ativo):
        self._consultando = bool(ativo)
        estado = "disabled" if ativo else "normal"
        self.entrada.configure(state=estado)
        self.btn_perguntar.configure(
            state=estado,
            text="Consultando..." if ativo else "Consultar",
        )
        for botao in self.botoes_exemplo:
            botao.configure(state=estado)
        if not ativo:
            self.entrada.focus_set()
            try:
                self.entrada.icursor("end")
            except Exception:
                pass

    def buscar(self):
        if self._consultando:
            return "break"

        pergunta = self.pergunta.get().strip()
        if not pergunta:
            mostrar_erro(ValueError("Digite uma consulta."))
            return "break"

        self._consulta_id += 1
        consulta_id = self._consulta_id
        self._definir_consultando(True)
        self._mostrar_resposta("Consultando o banco de dados da loja...")
        self._passo_animacao = 0
        self._animar_status_consulta(consulta_id)

        worker = threading.Thread(
            target=self._executar_consulta,
            args=(consulta_id, pergunta),
            daemon=True,
            name="consulta-assistente-local",
        )
        worker.start()
        self._agendar_verificacao_fila()
        return "break"

    def _executar_consulta(self, consulta_id, pergunta):
        try:
            texto, modo = responder_pergunta(pergunta)
            self._fila_resultados.put((consulta_id, "OK", texto, modo))
        except Exception as erro:
            self._fila_resultados.put((consulta_id, "ERRO", erro, None))

    def _agendar_verificacao_fila(self):
        if self._after_fila is None:
            self._after_fila = self.after(60, self._verificar_fila)

    def _verificar_fila(self):
        self._after_fila = None
        encontrou = False
        while True:
            try:
                resultado = self._fila_resultados.get_nowait()
            except queue.Empty:
                break

            consulta_id, estado, payload, modo = resultado
            if consulta_id != self._consulta_id:
                continue
            encontrou = True
            self._finalizar_consulta(estado, payload, modo)

        if self._consultando and not encontrou:
            self._agendar_verificacao_fila()

    def _animar_status_consulta(self, consulta_id):
        if not self._consultando or consulta_id != self._consulta_id:
            self._after_animacao = None
            return
        pontos = "." * ((self._passo_animacao % 3) + 1)
        self._passo_animacao += 1
        self.status_texto.set(f"Consultando estoque{pontos}")
        self._after_animacao = self.after(
            280,
            lambda: self._animar_status_consulta(consulta_id),
        )

    def _finalizar_consulta(self, estado, payload, modo):
        if self._after_animacao is not None:
            try:
                self.after_cancel(self._after_animacao)
            except Exception:
                pass
            self._after_animacao = None

        self._definir_consultando(False)
        self.atualizar_status()

        if estado == "ERRO":
            mostrar_erro(payload)
            return

        self._mostrar_resposta(payload or "Nenhuma informação encontrada.")
