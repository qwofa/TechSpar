"""Resume and speech-to-text routes."""

import re
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.auth import get_current_user
from backend.config import settings
from backend.indexer import _index_cache

router = APIRouter(prefix="/api")


def _sanitize_filename(filename: str) -> str:
    """Normalize filename to safe ASCII/UTF-8, preserving extension."""
    name = filename.rsplit(".", 1)
    if len(name) == 2:
        base, ext = name
    else:
        base, ext = filename, ""
    # Replace problematic characters with underscore
    base = re.sub(r'[<>:"|?*\x00-\x1f]', "_", base)
    # Collapse multiple spaces/underscores
    base = re.sub(r'[\s_]+', "_", base.strip())
    if ext:
        ext = ext.lstrip(".").lower()
        return f"{base}.{ext}"
    return base


@router.get("/resume/status")
def resume_status(user_id: str = Depends(get_current_user)):
    """Check if a resume file exists."""
    resume_dir = settings.user_resume_path(user_id)
    if not resume_dir.exists():
        return {"has_resume": False}
    files = [file for file in resume_dir.iterdir() if file.suffix.lower() == ".pdf"]
    if not files:
        return {"has_resume": False}
    resume_file = files[0]
    return {
        "has_resume": True,
        "filename": resume_file.name,
        "size": resume_file.stat().st_size,
    }


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """Upload a resume PDF. Replaces any existing resume."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    resume_dir = settings.user_resume_path(user_id)
    resume_dir.mkdir(parents=True, exist_ok=True)

    for old in resume_dir.iterdir():
        if old.is_file():
            old.unlink()

    safe_filename = _sanitize_filename(file.filename)
    dest = resume_dir / safe_filename
    content = await file.read()
    dest.write_bytes(content)

    _index_cache.pop((user_id, "resume"), None)
    cache_dir = settings.user_index_cache_path(user_id) / "resume"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    return {"ok": True, "filename": file.filename, "size": len(content)}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """Transcribe short audio clip to text via DashScope ASR."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Empty audio file.")

    try:
        from backend.transcribe import transcribe_short

        suffix = "." + (file.filename or "audio.webm").rsplit(".", 1)[-1]
        text = transcribe_short(audio_bytes, suffix=suffix)
        return {"text": text}
    except Exception as exc:
        raise HTTPException(500, f"Transcription failed: {exc}")
