import re
import json
import uuid
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from faster_whisper import WhisperModel


BASE = Path(__file__).parent
ENTRADA = BASE / "entrada"
SAIDA = BASE / "saida"
TEMP = BASE / "temp"
COOKIES = BASE / "cookies.txt"

for p in (ENTRADA, SAIDA, TEMP):
    p.mkdir(exist_ok=True)

# -------------------------
# Config defaults
# -------------------------
LANG = "pt"

MODEL_FAST = "small"
MODEL_ACCURATE = "medium"

# FAST (rápido)
FAST_DEVICE = "cpu"
FAST_COMPUTE = "int8"
FAST_BEAM = 1
FAST_VAD = True
FAST_AUDIO_FILTERS = False

# ACCURATE (mais fiel)
ACC_DEVICE = "cpu"
ACC_COMPUTE = "int8"
ACC_BEAM = 5
ACC_VAD = True
ACC_AUDIO_FILTERS = True


# -------------------------
# Utils: safe names
# -------------------------
def sanitize_name(name: str, max_len: int = 80) -> str:
    name = (name or "").strip()
    name = re.sub(r"[\\/:*?\"<>|]+", "", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_{2,}", "_", name)
    name = name.strip("_")
    return name[:max_len] if len(name) > max_len else name

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def today_folder():
    return datetime.now().strftime("%Y-%m-%d")


# -------------------------
# SRT
# -------------------------
def srt_time(seconds: float) -> str:
    td = timedelta(seconds=max(0, seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def write_srt(segments, out_path: Path) -> None:
    lines = []
    i = 1
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        start = srt_time(seg.start)
        end = srt_time(seg.end)
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
        i += 1

    out_path.write_text("\n".join(lines), encoding="utf-8")


# -------------------------
# Heurística (Natural)
# -------------------------
FILLERS = [
    "é", "eh", "hã", "hum", "tipo", "assim", "né", "tá", "então",
    "cara", "mano", "tipo assim", "tá bom", "tá certo"
]

def normalize_spaces(text: str) -> str:
    text = text.replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def remove_filler_start(line: str) -> str:
    original = line.strip()
    pattern = r"^(" + "|".join(re.escape(f) for f in sorted(FILLERS, key=len, reverse=True)) + r")([\s,.:;-]+)"
    line = re.sub(pattern, "", original, flags=re.IGNORECASE).strip()
    return line if line else original

def remove_stutters(text: str) -> str:
    return re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)

def light_punctuation(text: str) -> str:
    text = re.sub(r"[!?]{2,}", "!", text)
    text = re.sub(r"\.{3,}", "...", text)
    text = re.sub(r"\s+([,!.?…])", r"\1", text)
    text = re.sub(r"([,!.?…])([A-Za-zÀ-ÿ0-9])", r"\1 \2", text)
    return text

def sentence_capitalize(text: str) -> str:
    if not text:
        return text
    text = text[0].upper() + text[1:]

    def _cap(m):
        return m.group(1) + " " + m.group(2).upper()

    return re.sub(r"([.!?…]\s+)([a-zà-ÿ])", _cap, text)

def smart_paragraphs(text: str) -> str:
    words = text.split()
    if len(words) <= 60:
        return text

    parts = re.split(r"(?<=[.!?…])\s+", text)

    paras = []
    buf = []
    count = 0

    for p in parts:
        count += len(p.split())
        buf.append(p)
        if count >= 45:
            paras.append(" ".join(buf).strip())
            buf = []
            count = 0

    if buf:
        paras.append(" ".join(buf).strip())

    return "\n\n".join(paras).strip()

def clean_transcript_natural(text: str) -> str:
    text = normalize_spaces(text)
    text = remove_stutters(text)
    text = light_punctuation(text)

    lines = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        if not line:
            continue
        lines.append(remove_filler_start(line))

    text = " ".join(lines)
    text = normalize_spaces(text)
    text = sentence_capitalize(text)
    text = smart_paragraphs(text)
    return text.strip()


# -------------------------
# Jobs + Metadata
# -------------------------
def create_job_dir(source: str, title: str | None = None) -> Path:
    source = sanitize_name(source.lower())
    date = today_folder()
    job_id = uuid.uuid4().hex[:8]
    title = sanitize_name(title or f"job_{job_id}")

    folder_name = f"{now_stamp()}__{title}"
    job_dir = SAIDA / source / date / folder_name
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

def write_meta(job_dir: Path, meta: dict) -> None:
    (job_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# -------------------------
# Audio extraction (FFmpeg)
# -------------------------
def extrair_audio(video_path: Path, wav_path: Path, use_filters: bool = False) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
    ]
    if use_filters:
        af = "highpass=f=80,lowpass=f=8000,loudnorm=I=-16:TP=-1.5:LRA=11"
        cmd += ["-af", af]
    cmd += [str(wav_path)]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# -------------------------
# ASR
# -------------------------
def transcrever_com_segmentos(wav_path: Path, accurate: bool):
    if accurate:
        model_name, device, compute, beam, vad = MODEL_ACCURATE, ACC_DEVICE, ACC_COMPUTE, ACC_BEAM, ACC_VAD
    else:
        model_name, device, compute, beam, vad = MODEL_FAST, FAST_DEVICE, FAST_COMPUTE, FAST_BEAM, FAST_VAD

    model = WhisperModel(model_name, device=device, compute_type=compute)

    segments, _ = model.transcribe(
        str(wav_path),
        language=LANG,
        vad_filter=vad,
        beam_size=beam,
        best_of=beam if beam > 1 else 1,
        temperature=0.0
    )

    segments_list = list(segments)
    raw_text = "\n".join([s.text.strip() for s in segments_list if s.text.strip()]).strip()
    return raw_text, segments_list, model_name, beam, vad


# -------------------------
# YouTube (robusto)
# -------------------------
def run_ytdlp(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def youtube_get_title(url: str) -> str:
    cmd = [sys.executable, "-m", "yt_dlp", "--print", "%(title)s", url]
    out = subprocess.check_output(cmd, text=True, encoding="utf-8", errors="ignore").strip()
    return out if out else "youtube_video"

def youtube_download_audio_wav(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "yt_%(id)s.%(ext)s")

    # tentativas (fallback)
    attempts = []

    # 1) normal
    attempts.append([
        sys.executable, "-m", "yt_dlp",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", out_template,
        url
    ])

    # 2) forçar m4a (às vezes evita 403)
    attempts.append([
        sys.executable, "-m", "yt_dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", out_template,
        url
    ])

    # 3) android client (foge do SABR)
    attempts.append([
        sys.executable, "-m", "yt_dlp",
        "--extractor-args", "youtube:player_client=android",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", out_template,
        url
    ])

    # 4) android + m4a
    attempts.append([
        sys.executable, "-m", "yt_dlp",
        "--extractor-args", "youtube:player_client=android",
        "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", out_template,
        url
    ])

    # 5) se cookies existirem, tentar com cookies (último recurso)
    if COOKIES.exists():
        attempts.append([
            sys.executable, "-m", "yt_dlp",
            "--cookies", str(COOKIES),
            "--extractor-args", "youtube:player_client=android",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "-o", out_template,
            url
        ])

    last_err = None
    for idx, cmd in enumerate(attempts, start=1):
        try:
            print(f"🎧 yt-dlp tentativa {idx}/{len(attempts)}...")
            run_ytdlp(cmd)

            wavs = sorted(out_dir.glob("yt_*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not wavs:
                raise RuntimeError("yt-dlp rodou, mas nenhum .wav foi gerado.")
            return wavs[0]

        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Falha ao baixar áudio do YouTube mesmo com fallback. Último erro: {last_err}")


# -------------------------
# Drive capture (public links, via python -m gdown)
# -------------------------
def drive_extract_file_id(url: str) -> str:
    url = url.strip()

    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "id" in qs:
        return qs["id"][0]

    raise ValueError("Não consegui extrair o fileId do link do Drive.")

def drive_download_public(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    file_id = drive_extract_file_id(url)
    out_path = out_dir / f"drive_{file_id}"

    cmd = [
        sys.executable, "-m", "gdown",
        f"https://drive.google.com/uc?id={file_id}",
        "-O", str(out_path),
        "--quiet"
    ]
    subprocess.run(cmd, check=True)

    candidates = sorted(
        out_dir.glob(f"drive_{file_id}*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not candidates:
        raise RuntimeError("Falha ao baixar do Drive. Verifique permissões do link.")
    return candidates[0]


# -------------------------
# Main processing
# -------------------------
def save_last_job_dir(job_dir: Path) -> None:
    (BASE / "_LAST_JOB_DIR.txt").write_text(str(job_dir), encoding="utf-8")

def process_job(source: str, title: str, wav_path: Path, origin: dict, accurate: bool):
    job_dir = create_job_dir(source, title)

    out_raw = job_dir / "transcript_raw.txt"
    out_clean = job_dir / "transcript_clean.md"
    out_srt = job_dir / "subtitles.srt"

    raw_text, segments_list, model_name, beam, vad = transcrever_com_segmentos(wav_path, accurate=accurate)

    out_raw.write_text(raw_text, encoding="utf-8")
    out_clean.write_text(clean_transcript_natural(raw_text), encoding="utf-8")
    write_srt(segments_list, out_srt)

    meta = {
        "source": source,
        "title": title,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "language": LANG,
        "mode": "accurate" if accurate else "fast",
        "model": model_name,
        "beam_size": beam,
        "vad_filter": vad,
        "origin": origin
    }
    write_meta(job_dir, meta)

    save_last_job_dir(job_dir)

    print("\n✅ Job finalizado:")
    print(f"📁 Pasta: {job_dir}")
    print(f"📄 RAW:   {out_raw}")
    print(f"🧼 CLEAN: {out_clean}")
    print(f"🎬 SRT:   {out_srt}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, help="URL do YouTube para transcrever")
    parser.add_argument("--drive", type=str, help="Link do Google Drive (público/liberado) para transcrever")
    parser.add_argument("--accurate", action="store_true", help="Modo mais fiel (mais lento)")
    args = parser.parse_args()

    accurate = args.accurate

    if args.url:
        title = youtube_get_title(args.url)
        print(f"\n🌐 YouTube detectado: {title}")
        print("🎯 Modo:", "ACCURATE (mais fiel)" if accurate else "FAST (rápido)")

        wav = youtube_download_audio_wav(args.url, TEMP)

        process_job(
            source="youtube",
            title=title,
            wav_path=wav,
            origin={"url": args.url},
            accurate=accurate
        )
        return

    if args.drive:
        print("\n☁️ Google Drive link detectado.")
        print("🎯 Modo:", "ACCURATE (mais fiel)" if accurate else "FAST (rápido)")

        downloaded = drive_download_public(args.drive, TEMP)

        title = downloaded.stem
        wav = TEMP / f"{downloaded.stem}.wav"

        extrair_audio(downloaded, wav, use_filters=ACC_AUDIO_FILTERS if accurate else FAST_AUDIO_FILTERS)

        process_job(
            source="drive",
            title=title,
            wav_path=wav,
            origin={"drive_url": args.drive, "downloaded_file": downloaded.name},
            accurate=accurate
        )
        return

    videos = [p for p in ENTRADA.iterdir() if p.is_file()]
    if not videos:
        print(f"❌ Nenhum arquivo encontrado em: {ENTRADA}")
        print("➡️ Use --url / --drive OU coloque vídeos na pasta entrada.")
        return

    print("🎯 Modo:", "ACCURATE (mais fiel)" if accurate else "FAST (rápido)")

    for video in videos:
        print(f"\n🎬 Upload detectado: {video.name}")
        wav = TEMP / f"{video.stem}.wav"
        try:
            extrair_audio(video, wav, use_filters=ACC_AUDIO_FILTERS if accurate else FAST_AUDIO_FILTERS)

            process_job(
                source="upload",
                title=video.stem,
                wav_path=wav,
                origin={"file_name": video.name},
                accurate=accurate
            )
        except Exception as e:
            print(f"🔥 ERRO em {video.name}: {e}")


if __name__ == "__main__":
    main()
