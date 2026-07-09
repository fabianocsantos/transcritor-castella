import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path


APP_NAME = "Transcritor"
APP_VERSION = "v0.1 Interface"


class TranscritorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.arquivo_selecionado = None

        self.title(f"{APP_NAME} - {APP_VERSION}")
        self.geometry("760x620")
        self.minsize(700, 580)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.criar_interface()

    def criar_interface(self):
        container = ctk.CTkFrame(self, corner_radius=16)
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
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        titulo.grid(row=0, column=0, padx=24, pady=(28, 4))

        subtitulo = ctk.CTkLabel(
            container,
            text="Transcreva vídeos por link ou por arquivo do computador.",
            font=ctk.CTkFont(size=15),
            text_color=("gray35", "gray70"),
        )
        subtitulo.grid(row=1, column=0, padx=24, pady=(0, 28))

        label_link = ctk.CTkLabel(
            container,
            text="Link do vídeo",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
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
            placeholder_text="Cole aqui um link do YouTube, Drive, Instagram ou TikTok",
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
        separador.grid(row=4, column=0, pady=(0, 12))

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
            font=ctk.CTkFont(size=14, weight="bold"),
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

        frame_modos.grid_columnconfigure((0, 1), weight=1)

        modo_fast = ctk.CTkRadioButton(
            frame_modos,
            text="Rápido",
            variable=self.modo,
            value="fast",
        )
        modo_fast.grid(
            row=0,
            column=0,
            padx=20,
            pady=8,
            sticky="w",
        )

        modo_accurate = ctk.CTkRadioButton(
            frame_modos,
            text="Mais preciso",
            variable=self.modo,
            value="accurate",
        )
        modo_accurate.grid(
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
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.iniciar_transcricao_teste,
        )
        self.botao_transcrever.grid(
            row=9,
            column=0,
            padx=36,
            pady=(0, 18),
            sticky="ew",
        )

        self.barra_progresso = ctk.CTkProgressBar(container)
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
            pady=(0, 26),
        )

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar vídeo ou áudio",
            filetypes=[
                (
                    "Vídeos e áudios",
                    "*.mp4 *.mkv *.mov *.avi *.webm *.mp3 *.wav *.m4a",
                ),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not caminho:
            return

        self.arquivo_selecionado = Path(caminho)
        self.label_arquivo.configure(
            text=self.arquivo_selecionado.name
        )

        self.campo_link.delete(0, "end")

    def iniciar_transcricao_teste(self):
        link = self.campo_link.get().strip()

        if not link and not self.arquivo_selecionado:
            messagebox.showwarning(
                "Nenhuma entrada selecionada",
                "Cole um link ou selecione um arquivo do computador.",
            )
            return

        modo_escolhido = (
            "Rápido"
            if self.modo.get() == "fast"
            else "Mais preciso"
        )

        origem = (
            link
            if link
            else str(self.arquivo_selecionado)
        )

        self.status.configure(
            text="Interface funcionando corretamente."
        )
        self.barra_progresso.set(1)

        messagebox.showinfo(
            "Teste concluído",
            (
                "A interface está funcionando.\n\n"
                f"Origem:\n{origem}\n\n"
                f"Modo: {modo_escolhido}\n\n"
                "A transcrição ainda não foi iniciada nesta etapa."
            ),
        )


if __name__ == "__main__":
    app = TranscritorApp()
    app.mainloop()