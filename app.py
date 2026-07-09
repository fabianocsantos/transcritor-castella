import argparse
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel


APP_VERSION = "v4.8 Dev - Interface"

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
SAIDA_DIR = BASE_DIR / "saida"
ENTRADA_DIR = BASE_DIR / "entrada"
TOOLS_DIR = BASE_DIR / "tools"

YTDLP_EXE = TOOLS_DIR / "yt-dlp.exe"
COOKIES_FILE = BASE_DIR / "cookies.txt"
LAST_JOB_FILE = BASE_DIR / "_LAST_JOB_DIR.txt"


TEMP_DIR.mkdir(exist_ok=True)
SAIDA_DIR.mkdir(exist_ok=True)
ENTRADA_DIR.mkdir(exist_ok=True)
TOOLS_DIR.mkdir(exist_ok=True)


def banner():
    print()
    print("=" * 58)
    print("TRANSCRITOR")
    print(APP_VERSION)
    print("=" * 58)
    print()


def log(mensagem=""):
    print(mensagem, flush=True)


def detectar_fonte(link):
    link_normalizado = link.lower()

    if "youtube.com" in link_normalizado or "youtu.be" in link_normalizado:
        return "youtube"

    if "drive.google.com" in link_normalizado:
        return "drive"

    if "instagram.com" in link_normalizado:
        return "instagram"

    if "tiktok.com" in link_normalizado:
        return "tiktok"

    return "link"


def executar_comando(comando):
    comando_legivel = " ".join(str(item) for item in comando)
    log(f"[CMD] {comando_legivel}")

    subprocess.run(
        comando,
        check=True,
    )


def criar_pasta_job(fonte):
    horario = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    pasta_job = SAIDA_DIR / fonte / horario
    pasta_job.mkdir(
        parents=True,
        exist_ok=True,
    )

    LAST_JOB_FILE.write_text(
        str(pasta_job),
        encoding="utf-8",
    )

    return pasta_job


def baixar_audio(link, fonte):
    if not YTDLP_EXE.exists():
        raise FileNotFoundError(
            "O arquivo tools\\yt-dlp.exe não foi encontrado."
        )

    identificador = uuid.uuid4().hex[:8]
    arquivo_wav = TEMP_DIR / f"{fonte}_{identificador}.wav"

    comando = [
        str(YTDLP_EXE),
        "--no-playlist",
    ]

    if COOKIES_FILE.exists():
        comando.extend(
            [
                "--cookies",
                str(COOKIES_FILE),
            ]
        )

    comando.extend(
        [
            "-f",
            "bestaudio/best",
            "--extract-audio",
            "--audio-format",
            "wav",
            "--audio-quality",
            "0",
            "-o",
            str(arquivo_wav),
            link,
        ]
    )

    log(f"Fonte detectada: {fonte.upper()}")
    log("Preparando o áudio...")

    executar_comando(comando)

    if not arquivo_wav.exists():
        raise RuntimeError(
            "O áudio não foi gerado corretamente."
        )

    return arquivo_wav


def carregar_modelo():
    log("Carregando o modelo de transcrição...")

    try:
        return WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

    except RuntimeError as erro:
        mensagem = str(erro).lower()

        if (
            "failed to allocate memory" in mensagem
            or "cannot allocate memory" in mensagem
            or "out of memory" in mensagem
        ):
            raise RuntimeError(
                "Memória insuficiente para carregar o modelo.\n\n"
                "Feche outros programas e tente novamente."
            ) from erro

        raise


def transcrever(caminho_arquivo, modo="fast"):
    modelo = carregar_modelo()

    if modo == "accurate":
        log("Modo: MAIS PRECISO")
        log("Analisando o áudio com maior cuidado...")

        configuracoes = {
            "language": "pt",
            "beam_size": 5,
            "best_of": 5,
            "patience": 1.0,
            "temperature": 0.0,
            "condition_on_previous_text": True,
            "vad_filter": True,
        }

    else:
        log("Modo: RÁPIDO")
        log("Iniciando a transcrição...")

        configuracoes = {
            "language": "pt",
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "vad_filter": True,
        }

    try:
        segmentos_gerador, _ = modelo.transcribe(
            str(caminho_arquivo),
            **configuracoes,
        )

        partes_texto = []
        segmentos = []

        for segmento in segmentos_gerador:
            texto_segmento = segmento.text.strip()

            if texto_segmento:
                partes_texto.append(texto_segmento)

            segmentos.append(segmento)

        texto_completo = " ".join(partes_texto).strip()

        if not texto_completo:
            raise RuntimeError(
                "Nenhuma fala foi identificada no arquivo."
            )

        return texto_completo, segmentos

    except RuntimeError as erro:
        mensagem = str(erro).lower()

        if (
            "failed to allocate memory" in mensagem
            or "cannot allocate memory" in mensagem
            or "out of memory" in mensagem
        ):
            raise RuntimeError(
                "O computador ficou sem memória durante a transcrição.\n\n"
                "Feche outros programas e tente novamente no modo Rápido."
            ) from erro

        raise


def formatar_tempo_srt(segundos):
    milissegundos_totais = int(segundos * 1000)

    horas = milissegundos_totais // 3_600_000
    milissegundos_totais %= 3_600_000

    minutos = milissegundos_totais // 60_000
    milissegundos_totais %= 60_000

    segundos_inteiros = milissegundos_totais // 1_000
    milissegundos = milissegundos_totais % 1_000

    return (
        f"{horas:02d}:"
        f"{minutos:02d}:"
        f"{segundos_inteiros:02d},"
        f"{milissegundos:03d}"
    )


def salvar_srt(segmentos, caminho_saida):
    linhas = []

    for indice, segmento in enumerate(
        segmentos,
        start=1,
    ):
        inicio = formatar_tempo_srt(segmento.start)
        fim = formatar_tempo_srt(segmento.end)
        texto = segmento.text.strip()

        linhas.extend(
            [
                str(indice),
                f"{inicio} --> {fim}",
                texto,
                "",
            ]
        )

    caminho_saida.write_text(
        "\n".join(linhas),
        encoding="utf-8",
    )


def limpar_texto(texto):
    texto_limpo = re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()

    texto_limpo = re.sub(
        r"([.!?])\s+",
        r"\1\n\n",
        texto_limpo,
    )

    return texto_limpo.strip()


def localizar_arquivo_local(entrada):
    caminho_informado = Path(entrada)

    if caminho_informado.exists():
        return caminho_informado.resolve()

    caminho_na_entrada = ENTRADA_DIR / entrada

    if caminho_na_entrada.exists():
        return caminho_na_entrada.resolve()

    raise FileNotFoundError(
        "O arquivo local selecionado não foi encontrado."
    )


def remover_audio_temporario(caminho):
    try:
        if caminho.parent == TEMP_DIR and caminho.exists():
            caminho.unlink()
    except OSError:
        pass


def processar_transcricao(entrada, modo):
    entrada_limpa = entrada.strip().strip('"').strip("'")
    entrada_e_link = entrada_limpa.lower().startswith(
        (
            "http://",
            "https://",
        )
    )

    audio_temporario = None

    try:
        if entrada_e_link:
            fonte = detectar_fonte(entrada_limpa)
            caminho_audio = baixar_audio(
                entrada_limpa,
                fonte,
            )
            audio_temporario = caminho_audio

        else:
            fonte = "upload"
            caminho_audio = localizar_arquivo_local(
                entrada_limpa
            )

        pasta_job = criar_pasta_job(fonte)

        texto, segmentos = transcrever(
            caminho_audio,
            modo,
        )

        caminho_raw = pasta_job / "transcricao_raw.txt"
        caminho_clean = pasta_job / "transcricao_clean.md"
        caminho_srt = pasta_job / "legenda.srt"

        log("Salvando os arquivos...")

        caminho_raw.write_text(
            texto,
            encoding="utf-8",
        )

        caminho_clean.write_text(
            limpar_texto(texto),
            encoding="utf-8",
        )

        salvar_srt(
            segmentos,
            caminho_srt,
        )

        log()
        log("Transcrição concluída com sucesso.")
        log(f"Pasta: {pasta_job}")

    finally:
        if audio_temporario:
            remover_audio_temporario(
                audio_temporario
            )


def main():
    banner()

    parser = argparse.ArgumentParser(
        description="Transcritor de vídeos e áudios."
    )

    parser.add_argument(
        "--link",
        required=True,
        help="Link ou caminho do arquivo a ser transcrito.",
    )

    parser.add_argument(
        "--accurate",
        action="store_true",
        help="Usa o modo de transcrição mais cuidadoso.",
    )

    argumentos = parser.parse_args()

    modo = (
        "accurate"
        if argumentos.accurate
        else "fast"
    )

    processar_transcricao(
        argumentos.link,
        modo,
    )


if __name__ == "__main__":
    try:
        main()

    except subprocess.CalledProcessError:
        print(
            "\nNão foi possível baixar o vídeo.\n\n"
            "Confira se o link está correto, se o conteúdo está "
            "disponível e se o acesso exige login.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    except FileNotFoundError as erro:
        print(
            f"\n{erro}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    except RuntimeError as erro:
        print(
            f"\n{erro}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    except Exception as erro:
        print(
            "\nOcorreu um erro inesperado durante a transcrição.\n"
            f"Detalhes: {erro}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)