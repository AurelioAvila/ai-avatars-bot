"""
Runs Easy-Wav2Lip locally (lipsync_engine/, its own Python 3.10 venv in
lipsync_venv/) instead of the manual Google Colab step main.py originally
documented. Colab's free tier can't run unattended/scheduled, so it forced a
human to open a notebook and click "Run All" for every single video - this
runs the exact same model (Wav2Lip + optional GFPGAN enhance) fully locally
on the GTX 1660, no manual step, no per-video cost.
"""
import configparser
import os
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENGINE_DIR = BASE_DIR / "lipsync_engine"
VENV_PYTHON = BASE_DIR / "lipsync_venv" / "Scripts" / "python.exe"
CONFIG_PATH = ENGINE_DIR / "config.ini"
LOCK_PATH = BASE_DIR / "lipsync.lock"


def _acquire_lock(timeout: int = 900) -> None:
    """config.ini and lipsync_engine/temp/ are shared, single-instance state -
    two runs racing (a manual test overlapping the scheduled task, say)
    silently clobber each other's video/audio paths mid-run instead of
    erroring cleanly (confirmed live 2026-08-01). A simple exclusive-create
    lockfile serializes access instead."""
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"Lip-sync locale: lock occupato da troppo tempo ({LOCK_PATH})")
            time.sleep(2)


def _release_lock() -> None:
    LOCK_PATH.unlink(missing_ok=True)


def generate_avatar_video(avatar_image_path: str, audio_path: str) -> str:
    """Runs the local lip-sync engine on (avatar_image_path, audio_path) and
    returns the path to the rendered talking-head mp4."""
    avatar_image_path = Path(avatar_image_path).resolve()
    audio_path = Path(audio_path).resolve()

    _acquire_lock()
    try:
        return _run(avatar_image_path, audio_path)
    finally:
        _release_lock()


def _run(avatar_image_path: Path, audio_path: Path) -> str:
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    config["OPTIONS"]["video_file"] = str(avatar_image_path)
    config["OPTIONS"]["vocal_file"] = str(audio_path)
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

    result = subprocess.run(
        [str(VENV_PYTHON), "run.py"],
        cwd=str(ENGINE_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Lip-sync locale fallito: {result.stdout[-2000:]}\n{result.stderr[-2000:]}")

    # Easy-Wav2Lip names the output "<image_stem>_<audio_stem>_Easy-Wav2Lip.mp4"
    # in the same folder as the source image.
    output_path = avatar_image_path.parent / f"{avatar_image_path.stem}_{audio_path.stem}_Easy-Wav2Lip.mp4"
    if not output_path.exists():
        raise RuntimeError(f"Lip-sync completato ma il file atteso non esiste: {output_path}\n{result.stdout[-1000:]}")

    # The subprocess exits right as it finishes writing the mp4 - reading it
    # a beat too early (ffmpeg in the next pipeline step, antivirus scan
    # holding a lock, etc.) intermittently fails. Wait for its size to stop
    # changing before handing it off, instead of assuming "process exited"
    # means "file fully flushed and readable".
    last_size = -1
    for _ in range(20):
        size = output_path.stat().st_size
        if size == last_size and size > 0:
            break
        last_size = size
        time.sleep(0.5)

    return str(output_path)
