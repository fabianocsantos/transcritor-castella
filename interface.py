import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk


APP_NAME = "Transcritor"
APP_VERSION = "v0.2 Interface Integrada"

BASE_DIR = Path(__file__).resolve().parent
APP_SCRIPT = BASE_DIR / "app.py"
LAST_JOB_FILE = BASE_DIR / "_LAST_JOB_DIR.txt"


class TranscritorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.arquivo_selecionado = None
        self.ultimo_job = None
        self.processando = False

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME} - {APP_VERSION}")
        self.geometry("760x680")
        self.minsize(700, 640)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.criar_interface()

    def criar_interface(self):
        container = ctk.CTkFrame(
            self,
            corner_radius=16,
        )
        container.grid(
            row=0,
            column=0,
            padx=24,
            pady=24,
            sticky="nsew",
        )

        container.grid_columnconfigure(0, weight=1)

        titulo = ctk.CTkLabel(
            container,
            text=APP_NAME,
            font=ctk.CTkFont(
                size=30,
                weight="bold",
            ),
        )
        titulo.grid(
            row=0,
            column=0,
            padx=24,
            pady=(28, 4),
        )

        subtitulo = ctk.CTkLabel(
            container,
            text=(
                "Transcreva vídeos por link "
                "ou por arquivo do computador."
            ),
            font=ctk.CTkFont(size=15),
            text_color=("gray35", "gray70"),
        )
        subtitulo.grid(
            row=1,
            column=0,
            padx=24,
            pady=(0, 28),
        )

        label_link = ctk.CTkLabel(
            container,
            text="Link do vídeo",
            anchor="w",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        )
        label_link.grid(
            row=2,
            column=0,
            padx=36,
            pady=(0, 8),
            sticky="ew",
        )

        self.campo_link = ctk.CTkEntry(
            container,
            height=42,
            placeholder_text=(
                "Cole um link do YouTube, Drive, "
                "Instagram ou TikTok"
            ),
        )
        self.campo_link.grid(
            row=3,
            column=0,
            padx=36,
            pady=(0, 18),
            sticky="ew",
        )

        separador = ctk.CTkLabel(
            container,
            text="ou",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
        )
        separador.grid(
            row=4,
            column=0,
            pady=(0, 12),
        )

        self.botao_arquivo = ctk.CTkButton(
            container,
            text="Selecionar vídeo do computador",
            height=42,
            command=self.selecionar_arquivo,
        )
        self.botao_arquivo.grid(
            row=5,
            column=0,
            padx=150,
            pady=(0, 10),
            sticky="ew",
        )

        self.label_arquivo = ctk.CTkLabel(
            container,
            text="Nenhum arquivo selecionado",
            text_color=("gray40", "gray65"),
        )
        self.label_arquivo.grid(
            row=6,
            column=0,
            padx=36,
            pady=(0, 26),
        )

        label_modo = ctk.CTkLabel(
            container,
            text="Modo de transcrição",
            anchor="w",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        )
        label_modo.grid(
            row=7,
            column=0,
            padx=36,
            pady=(0, 8),
            sticky="ew",
        )

        self.modo = ctk.StringVar(value="fast")

        frame_modos = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        frame_modos.grid(
            row=8,
            column=0,
            padx=36,
            pady=(0, 24),
            sticky="ew",
        )

        frame_modos.grid_columnconfigure(
            (0, 1),
            weight=1,
        )

        self.modo_fast = ctk.CTkRadioButton(
            frame_modos,
            text="Rápido",
            variable=self.modo,
            value="fast",
        )
        self.modo_fast.grid(
            row=0,
            column=0,
            padx=20,
            pady=8,
            sticky="w",
        )

        self.modo_accurate = ctk.CTkRadioButton(
            frame_modos,
            text="Mais preciso",
            variable=self.modo,
            value="accurate",
        )
        self.modo_accurate.grid(
            row=0,
            column=1,
            padx=20,
            pady=8,
            sticky="w",
        )

        self.botao_transcrever = ctk.CTkButton(
            container,
            text="Iniciar transcrição",
            height=50,
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
            command=self.iniciar_transcricao,
        )
        self.botao_transcrever.grid(
            row=9,
            column=0,
            padx=36,
            pady=(0, 18),
            sticky="ew",
        )

        self.barra_progresso = ctk.CTkProgressBar(
            container,
            mode="indeterminate",
        )
        self.barra_progresso.grid(
            row=10,
            column=0,
            padx=36,
            pady=(0, 10),
            sticky="ew",
        )
        self.barra_progresso.set(0)

        self.status = ctk.CTkLabel(
            container,
            text="Pronto para começar.",
            text_color=("gray35", "gray70"),
        )
        self.status.grid(
            row=11,
            column=0,
            padx=36,
            pady=(0, 18),
        )

        self.botao_abrir_pasta = ctk.CTkButton(
            container,
            text="Abrir pasta da transcrição",
            height=42,
            state="disabled",
            command=self.abrir_pasta_resultado,
        )
        self.botao_abrir_pasta.grid(
            row=12,
            column=0,
            padx=150,
            pady=(0, 28),
            sticky="ew",
        )

    def selecionar_arquivo(self):
        if self.processando:
            return

        caminho = filedialog.askopenfilename(
            title="Selecionar vídeo ou áudio",
            filetypes=[
                (
                    "Vídeos e áudios",
                    (
                        "*.mp4 *.mkv *.mov *.avi "
                        "*.webm *.mp3 *.wav *.m4a"
                    ),
                ),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not caminho:
            return

        self.arquivo_selecionado = Path(caminho)

        self.label_arquivo.configure(
            text=self.arquivo_selecionado.name,
        )

        self.campo_link.delete(0, "end")

    def iniciar_transcricao(self):
        if self.processando:
            return

        link = self.campo_link.get().strip()

        if not link and not self.arquivo_selecionado:
            messagebox.showwarning(
                "Nenhuma entrada selecionada",
                (
                    "Cole um link ou selecione um "
                    "arquivo do computador."
                ),
            )
            return

        if not APP_SCRIPT.exists():
            messagebox.showerror(
                "Arquivo não encontrado",
                (
                    "O arquivo app.py não foi encontrado "
                    "na pasta do programa."
                ),
            )
            return

        origem = (
            link
            if link
            else str(self.arquivo_selecionado)
        )

        self.processando = True
        self.ultimo_job = None

        self.botao_abrir_pasta.configure(
            state="disabled",
        )

        self.alterar_estado_controles("disabled")

        self.botao_transcrever.configure(
            text="Transcrevendo...",
        )

        self.status.configure(
            text=(
                "Preparando o vídeo e iniciando "
                "a transcrição..."
            ),
        )

        self.barra_progresso.start()

        thread = threading.Thread(
            target=self.executar_transcricao,
            args=(origem,),
            daemon=True,
        )
        thread.start()

    def executar_transcricao(self, origem):
        comando = [
            sys.executable,
            str(APP_SCRIPT),
            "--link",
            origem,
        ]

        if self.modo.get() == "accurate":
            comando.append("--accurate")

        flags_janela = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

        ambiente = os.environ.copy()
        ambiente["PYTHONIOENCODING"] = "utf-8"
        ambiente["PYTHONUTF8"] = "1"

        try:
            resultado = subprocess.run(
                comando,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags_janela,
                env=ambiente,
            )

            if resultado.returncode != 0:
                mensagem_erro = (
                    resultado.stderr.strip()
                    or resultado.stdout.strip()
                    or "Erro desconhecido."
                )

                self.after(
                    0,
                    self.transcricao_com_erro,
                    mensagem_erro,
                )
                return

            job_dir = self.ler_ultimo_job()

            self.after(
                0,
                self.transcricao_concluida,
                job_dir,
            )

        except Exception as erro:
            self.after(
                0,
                self.transcricao_com_erro,
                str(erro),
            )

    def ler_ultimo_job(self):
        if not LAST_JOB_FILE.exists():
            return None

        try:
            caminho = LAST_JOB_FILE.read_text(
                encoding="utf-8",
            ).strip()

            if not caminho:
                return None

            pasta = Path(caminho)

            if pasta.exists():
                return pasta

        except OSError:
            return None

        return None

    def transcricao_concluida(self, job_dir):
        self.processando = False
        self.ultimo_job = job_dir

        self.barra_progresso.stop()
        self.barra_progresso.set(1)

        self.alterar_estado_controles("normal")

        self.botao_transcrever.configure(
            text="Iniciar nova transcrição",
        )

        self.status.configure(
            text="Transcrição concluída com sucesso.",
        )

        if self.ultimo_job:
            self.botao_abrir_pasta.configure(
                state="normal",
            )

        messagebox.showinfo(
            "Transcrição concluída",
            (
                "Os arquivos foram gerados com sucesso.\n\n"
                "Use o botão abaixo para abrir "
                "a pasta da transcrição."
            ),
        )

    def transcricao_com_erro(self, mensagem_erro):
        self.processando = False

        self.barra_progresso.stop()
        self.barra_progresso.set(0)

        self.alterar_estado_controles("normal")

        self.botao_transcrever.configure(
            text="Tentar novamente",
        )

        self.status.configure(
            text="Não foi possível concluir a transcrição.",
        )

        mensagem_resumida = mensagem_erro[-1500:]

        messagebox.showerror(
            "Erro na transcrição",
            (
                "O programa encontrou um problema.\n\n"
                f"Detalhes:\n{mensagem_resumida}"
            ),
        )

    def alterar_estado_controles(self, estado):
        self.campo_link.configure(state=estado)
        self.botao_arquivo.configure(state=estado)
        self.modo_fast.configure(state=estado)
        self.modo_accurate.configure(state=estado)
        self.botao_transcrever.configure(state=estado)

        if estado == "normal":
            self.botao_transcrever.configure(
                state="normal",
            )

    def abrir_pasta_resultado(self):
        if not self.ultimo_job:
            messagebox.showwarning(
                "Pasta não encontrada",
                (
                    "Ainda não há uma pasta de "
                    "transcrição disponível."
                ),
            )
            return

        if not self.ultimo_job.exists():
            messagebox.showerror(
                "Pasta não encontrada",
                (
                    "A pasta do resultado não existe "
                    "mais neste computador."
                ),
            )
            return

        os.startfile(str(self.ultimo_job))


if __name__ == "__main__":
    app = TranscritorApp()
    app.mainloop()