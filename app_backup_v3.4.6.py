import argparse
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
import sys

VERSION = "3.4.6"
PRODUCT_NAME = "TRANSCRITOR DE VÍDEO"
PRODUCT_BRAND = "Castella Studio"

BASE_DIR = Path(__file__).parent
ENTRADA = BASE_DIR / "entrada"
SAIDA = BASE_DIR / "saida"
TEMP = BASE_DIR / "temp"
COOKIES = BASE_DIR / "cookies.txt"

ENTRADA.mkdir(exist_ok=True)
SAIDA.mkdir(exist_ok=True)
TEMP.mkdir(exist_ok=True)

def show_banner():
    print("\n" + "━" * 55)
    print(f" {PRODUCT_NAME}")
    print(f" {PRODUCT_BRAND} • v{VERSION} Stable")
    print("━" * 55)
    print(" ✔ Upload local")
    print(" ✔ YouTube")
    print(" ✔ Google Drive")
    print(" ✔ Instagram")
    print(" ✔ TikTok")
    print("\n Modo: FAST | ACCURATE")
    print(" Saída: RAW • CLEAN • SRT")
    print("━" * 55 + "\n")

def run(cmd):
    return subprocess.run(cmd, check=True)

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)

def extrair_audio(input_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        str(output_path)
    ]
    run(cmd)

def transcrever(wav_path):
    cmd = [
        sys.executable, "-m", "whisper",
        str(wav_path),
        "--model", "small",
        "--language", "pt",
        "--output_format", "all",
        "--output_dir", str(TEMP)
    ]
    run(cmd)

def organizar_saida(base_name, fonte):
    data = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H-%M-%S")

    pasta = SAIDA / fonte / data / f"{data}_{hora}__{base_name}"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta

def processar_audio(wav_path, fonte, base_name):
    pasta_final = organizar_saida(base_name, fonte)

    raw = TEMP / f"{wav_path.stem}.txt"
    srt = TEMP / f"{wav_path.stem}.srt"

    if raw.exists():
        raw.rename(pasta_final / "transcript_raw.txt")

    if srt.exists():
        srt.rename(pasta_final / "subtitles.srt")

    print("\n✅ Job finalizado:")
    print(f"📁 Pasta: {pasta_final}")

def baixar_youtube(url):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", str(TEMP / "yt_%(id)s.%(ext)s"),
        url
    ]
    run(cmd)

def baixar_drive(url):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", str(TEMP / "drive_%(id)s.%(ext)s"),
        url
    ]
    run(cmd)

def baixar_social(url):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--cookies", str(COOKIES),
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", str(TEMP / "social_%(id)s.%(ext)s"),
        url
    ]
    run(cmd)

def detectar_fonte(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "drive.google.com" in url:
        return "drive"
    if "instagram.com" in url:
        return "instagram"
    if "tiktok.com" in url or "vt.tiktok.com" in url:
        return "tiktok"
    return "desconhecido"

def main():
    show_banner()

    parser = argparse.ArgumentParser()
    parser.add_argument("--link", type=str)
    args = parser.parse_args()

    if args.link:
        fonte = detectar_fonte(args.link)
        print(f"🌐 {fonte.upper()} detectado")
        print("🎯 Modo: FAST (rápido)")

        if fonte == "youtube":
            baixar_youtube(args.link)
            wav = sorted(TEMP.glob("yt_*.wav"))[-1]

        elif fonte == "drive":
            baixar_drive(args.link)
            arquivo = sorted(TEMP.glob("drive_*"))[-1]
            wav = TEMP / f"{arquivo.stem}.wav"
            extrair_audio(arquivo, wav)

        elif fonte in ["instagram", "tiktok"]:
            baixar_social(args.link)
            wav = sorted(TEMP.glob("social_*.wav"))[-1]

        else:
            print("❌ Fonte não suportada.")
            return

        base_name = sanitize_filename(wav.stem)
        transcrever(wav)
        processar_audio(wav, fonte, base_name)

    else:
        arquivos = list(ENTRADA.glob("*.*"))
        if not arquivos:
            print("❌ Nenhum arquivo encontrado na pasta entrada.")
            return

        for arquivo in arquivos:
            print(f"\n🎬 Processando: {arquivo.name}")
            wav = TEMP / f"{arquivo.stem}.wav"
            extrair_audio(arquivo, wav)
            transcrever(wav)
            processar_audio(wav, "upload", arquivo.stem)

if __name__ == "__main__":
    main()
