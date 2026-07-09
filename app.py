import argparse
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel

# =====================================================
# CONFIG
# =====================================================

APP_VERSION = "v4.7 Stable (Fast Engine)"

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
SAIDA_DIR = BASE_DIR / "saida"
ENTRADA_DIR = BASE_DIR / "entrada"
TOOLS_DIR = BASE_DIR / "tools"

YTDLP_EXE = TOOLS_DIR / "yt-dlp.exe"
COOKIES = BASE_DIR / "cookies.txt"
LAST_JOB_FILE = BASE_DIR / "_LAST_JOB_DIR.txt"

TEMP_DIR.mkdir(exist_ok=True)
SAIDA_DIR.mkdir(exist_ok=True)
ENTRADA_DIR.mkdir(exist_ok=True)

# =====================================================
# UI
# =====================================================

def banner():
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TRANSCRITOR DE VÍDEO
 Castella Studio • {APP_VERSION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✔ Faster-Whisper Engine
 ✔ Download otimizado
 ✔ RAW • CLEAN • SRT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

def log(msg):
    print(msg, flush=True)

# =====================================================
# HELPERS
# =====================================================

def detectar_fonte(link: str) -> str:
    s = link.lower()
    if "youtube" in s:
        return "youtube"
    if "drive.google" in s:
        return "drive"
    if "instagram" in s:
        return "instagram"
    if "tiktok" in s:
        return "tiktok"
    return "upload"

def run(cmd):
    log(f"[CMD] {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)

def make_job_dir(fonte: str):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    job_dir = SAIDA_DIR / fonte / ts
    job_dir.mkdir(parents=True, exist_ok=True)
    with open(LAST_JOB_FILE, "w", encoding="utf-8") as f:
        f.write(str(job_dir))
    return job_dir

# =====================================================
# DOWNLOAD
# =====================================================

def baixar_audio(link, fonte):
    job_id = uuid.uuid4().hex[:8]
    wav_out = TEMP_DIR / f"{fonte}_{job_id}.wav"

    cmd = [str(YTDLP_EXE)]

    if COOKIES.exists():
        cmd += ["--cookies", str(COOKIES)]

    cmd += [
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", str(wav_out),
        link
    ]

    log(f"🌐 Fonte detectada: {fonte.upper()}")
    run(cmd)

    if not wav_out.exists():
        raise RuntimeError("Falha ao gerar WAV.")

    return wav_out

# =====================================================
# TRANSCRIÇÃO — FASTER WHISPER
# =====================================================

def transcrever(wav_path, modelo="small"):
    log("🧠 Carregando modelo (faster-whisper)...")

    model = WhisperModel(
        modelo,
        device="cpu",
        compute_type="int8"
    )

    segments, info = model.transcribe(
        str(wav_path),
        language="pt"
    )

    texto_total = []
    srt_segments = []

    for segment in segments:
        texto_total.append(segment.text.strip())
        srt_segments.append(segment)

    texto_final = " ".join(texto_total)
    return texto_final, srt_segments

# =====================================================
# SRT
# =====================================================

def format_ts(seconds):
    ms = int(seconds * 1000)
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def salvar_srt(segments, path):
    linhas = []
    for i, seg in enumerate(segments, start=1):
        linhas.append(str(i))
        linhas.append(f"{format_ts(seg.start)} --> {format_ts(seg.end)}")
        linhas.append(seg.text.strip())
        linhas.append("")
    path.write_text("\n".join(linhas), encoding="utf-8")

# =====================================================
# CLEAN
# =====================================================

def clean_text(texto):
    t = re.sub(r"\s+", " ", texto)
    t = re.sub(r"([.!?]) ", r"\1\n\n", t)
    return t.strip()

# =====================================================
# MAIN
# =====================================================

def main():
    banner()

    parser = argparse.ArgumentParser()
    parser.add_argument("--link")
    parser.add_argument("--accurate", action="store_true")
    args = parser.parse_args()

    if not args.link:
        log("❌ Forneça um link com --link")
        return

    modelo = "medium" if args.accurate else "small"
    modo = "ACCURATE" if args.accurate else "FAST"
    log(f"🎯 Modo: {modo}")

    link = args.link.strip().strip('"').strip("'")
    is_url = link.startswith("http")

    if is_url:
        fonte = detectar_fonte(link)
        wav = baixar_audio(link, fonte)
        job_dir = make_job_dir(fonte)
    else:
        p = Path(link)
        if not p.exists():
            p = ENTRADA_DIR / link
        if not p.exists():
            raise FileNotFoundError("Arquivo local não encontrado.")
        fonte = "upload"
        job_dir = make_job_dir("upload")
        wav = p

    texto, segments = transcrever(wav, modelo)

    raw_path = job_dir / "transcricao_raw.txt"
    clean_path = job_dir / "transcricao_clean.md"
    srt_path = job_dir / "legenda.srt"

    raw_path.write_text(texto, encoding="utf-8")
    clean_path.write_text(clean_text(texto), encoding="utf-8")
    salvar_srt(segments, srt_path)

    try:
        if wav.parent == TEMP_DIR:
            wav.unlink()
    except:
        pass

    log("\n✅ Job finalizado em:")
    log(f"📁 {job_dir}")

if __name__ == "__main__":
    main()
