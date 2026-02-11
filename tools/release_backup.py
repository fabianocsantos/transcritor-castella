from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

BASE = Path(r"C:\transcritor")
RELEASES = BASE / "releases"

FILES = [
    BASE / "app.py",
    BASE / "TRANSCRITOR.bat",
    BASE / "README.md",
    BASE / "CHANGELOG.md",
]

def safe_name(s: str) -> str:
    s = (s or "").strip()
    s = s.replace(" ", "_")
    return "".join(c for c in s if c.isalnum() or c in ("_", "-", "."))[:60]

def write_requirements(out_dir: Path):
    req = out_dir / "requirements.txt"
    try:
        # roda pip freeze dentro da venv atual
        result = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, encoding="utf-8")
        req.write_text(result.strip() + "\n", encoding="utf-8")
    except Exception as e:
        req.write_text(f"# erro ao gerar requirements.txt: {e}\n", encoding="utf-8")

def main():
    RELEASES.mkdir(exist_ok=True)

    version = input("Versão (ex: v3.3.2): ").strip() or "vX"
    notes = input("Notas (opcional): ").strip()

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    version_safe = safe_name(version)

    out = RELEASES / f"{version_safe}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)

    # copia arquivos
    for f in FILES:
        if f.exists():
            shutil.copy2(f, out / f.name)

    # salvar dependências
    write_requirements(out)

    # release notes
    (out / "release_notes.txt").write_text(
        f"version: {version}\n"
        f"date: {stamp}\n\n"
        f"notes:\n{notes}\n",
        encoding="utf-8"
    )

    print("\n✅ Release salva em:", out)

if __name__ == "__main__":
    main()
