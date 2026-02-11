import os
import sys
import argparse
import subprocess
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
SAIDA_DIR = os.path.join(BASE_DIR, "saida")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SAIDA_DIR, exist_ok=True)


def banner():
    print("\n" + "━" * 55)
    print(" TRANSCRITOR DE VÍDEO")
    print(" Castella Studio • v4.1 Stable")
    print("━" * 55)
    print(" ✔ YouTube")
    print(" ✔ Google Drive")
    print(" ✔ Instagram")
    print(" ✔ TikTok")
    print(" ✔ Upload local")
    print(" Saída: RAW • CLEAN • SRT")
    print("━" * 55 + "\n")


def run(cmd):
    subprocess.run(cmd, check=True)


def detectar_fonte(link):
    if "youtube.com" in link or "youtu.be" in link:
        return "youtube"
    if "drive.google.com" in link:
        return "drive"
    if "instagram.com" in link:
        return "instagram"
    if "tiktok.com" in link or "vt.tiktok.com" in link:
        return "tiktok"
    return "upload"


def baixar_audio(link):
    cmd = [
        "yt-dlp",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", os.path.join(TEMP_DIR, "%(id)s.%(ext)s"),
        link
    ]
    run(cmd)

    # pega último wav criado
    arquivos = [f for f in os.listdir(TEMP_DIR) if f.endswith(".wav")]
    arquivos.sort(key=lambda x: os.path.getmtime(os.path.join(TEMP_DIR, x)), reverse=True)
    return os.path.join(TEMP_DIR, arquivos[0])


def limpar_texto(texto):
    linhas = texto.splitlines()
    novo = []

    for l in linhas:
        l = l.strip()
        if not l:
            continue

        if not l.endswith((".", "!", "?")):
            l += "."

        novo.append(l)

    return "\n\n".join(novo)


def transcrever(audio_path, modelo):
    cmd = [
        sys.executable,
        "-m", "whisper",
        audio_path,
        "--model", modelo,
        "--language", "pt",
        "--device", "cpu",
        "--fp16", "False",
        "--output_format", "all",
        "--output_dir", TEMP_DIR
    ]
    run(cmd)


def organizar_saida(fonte, modelo):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta_final = os.path.join(SAIDA_DIR, fonte, timestamp)
    os.makedirs(pasta_final, exist_ok=True)

    arquivos = os.listdir(TEMP_DIR)

    txt = None
    srt = None

    for f in arquivos:
        if f.endswith(".txt") and not f.endswith("_clean.txt"):
            txt = f
        if f.endswith(".srt"):
            srt = f

    if not txt:
        print("Erro: TXT não encontrado.")
        sys.exit(1)

    # mover RAW
    shutil.move(os.path.join(TEMP_DIR, txt),
                os.path.join(pasta_final, "transcript_raw.txt"))

    # mover SRT
    if srt:
        shutil.move(os.path.join(TEMP_DIR, srt),
                    os.path.join(pasta_final, "subtitles.srt"))

    # gerar CLEAN
    with open(os.path.join(pasta_final, "transcript_raw.txt"), "r", encoding="utf-8") as f:
        raw = f.read()

    clean = limpar_texto(raw)

    with open(os.path.join(pasta_final, "transcript_clean.md"), "w", encoding="utf-8") as f:
        f.write(clean)

    # limpar TEMP
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))

    print("\n✅ Job finalizado:")
    print(f"📁 Pasta: {pasta_final}")
    print("Finalizado!\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--link", help="Link do vídeo")
    parser.add_argument("--accurate", action="store_true")
    args = parser.parse_args()

    banner()

    modelo = "medium" if args.accurate else "small"
    print(f"🎯 Modo: {'ACCURATE' if args.accurate else 'FAST'}\n")

    if args.link:
        fonte = detectar_fonte(args.link)
        print(f"🌐 Fonte detectada: {fonte.upper()}\n")

        audio = baixar_audio(args.link)
        transcrever(audio, modelo)
        organizar_saida(fonte, modelo)

    else:
        print("❌ Forneça um link com --link")


if __name__ == "__main__":
    main()
