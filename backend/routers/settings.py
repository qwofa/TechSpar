"""Settings routes — per-user LLM/Embedding overrides + global system flags."""

import logging

from fastapi import APIRouter, Depends

from backend.auth import get_current_user, is_admin_user
from backend.config import settings
from backend.llm_provider import embedding_signature, provider_status, reset_embedding_cache
from backend.models import EmbeddingSettings, LLMSettings, SettingsResponse, SystemSettings
from backend.storage.user_settings import (
    load_user_provider,
    load_user_services,
    load_user_settings,
    save_user_provider,
    save_user_settings,
)

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api")


@router.get("/settings")
def get_user_settings(user_id: str = Depends(get_current_user)):
    """Return this user's own LLM/Embedding overrides (empty fields inherit the
    global .env default), plus global system flags and per-user training prefs."""
    llm_override, emb_override = load_user_provider(user_id)
    llm = llm_override or LLMSettings()
    embedding = emb_override or EmbeddingSettings()
    services = load_user_services(user_id)
    system = SystemSettings(allow_registration=settings.allow_registration)
    training = load_user_settings(user_id)
    return SettingsResponse(
        llm=llm,
        embedding=embedding,
        services=services,
        system=system,
        training=training,
        is_admin=is_admin_user(user_id),
        configured=provider_status(user_id),
    )


@router.put("/settings")
def put_user_settings(payload: SettingsResponse, user_id: str = Depends(get_current_user)):
    """Persist this user's LLM/Embedding overrides and training prefs.

    On embedding-model change, the user's now-incompatible vectors are invalidated
    (fast — prevents dimension-mismatch). Re-embedding is the explicit follow-up:
    POST /settings/rebuild-index. Returns embedding_changed so the UI can warn."""
    old_emb_sig = embedding_signature(user_id)

    save_user_provider(user_id, payload.llm, payload.embedding, payload.services)
    # Drop the cached client so the next call picks up the new key/base/model.
    reset_embedding_cache(user_id)

    embedding_changed = embedding_signature(user_id) != old_emb_sig
    if embedding_changed:
        from backend.indexer import invalidate_user_embeddings

        logger.info("Embedding model changed for user %s — vectors invalidated.", user_id)
        invalidate_user_embeddings(user_id)

    # 仅 admin 能改全局账户开关；非 admin 的请求即便带了 system 字段也直接忽略。
    if is_admin_user(user_id):
        settings.allow_registration = payload.system.allow_registration

    save_user_settings(payload.training, user_id)
    return {"ok": True, "embedding_changed": embedding_changed}


@router.post("/settings/rebuild-index")
def rebuild_index(user_id: str = Depends(get_current_user)):
    """Re-embed the user's resume / knowledge bases / weak-point memory with their
    current embedding model. Idempotent: clears stale vectors first. Best-effort per
    source — a missing/empty corpus is skipped, not an error."""
    from backend.indexer import (
        build_resume_index,
        build_topic_index,
        get_topic_map,
        invalidate_user_embeddings,
    )
    from backend.vector_memory import rebuild_index_from_profile

    invalidate_user_embeddings(user_id)
    rebuild_index_from_profile(user_id)

    result = {"weak_points": True, "resume": False, "topics": []}

    resume_dir = settings.user_resume_path(user_id)
    if resume_dir.exists() and any(p.is_file() for p in resume_dir.rglob("*")):
        try:
            build_resume_index(user_id, force_rebuild=True)
            result["resume"] = True
        except Exception as exc:  # noqa: BLE001 - best-effort, report and continue
            logger.warning("Resume reindex failed for user %s: %s", user_id, exc)

    for topic in get_topic_map(user_id):
        try:
            build_topic_index(topic, user_id, force_rebuild=True)
            result["topics"].append(topic)
        except Exception as exc:  # noqa: BLE001 - topics without docs are expected
            logger.info("Topic '%s' reindex skipped for user %s: %s", topic, user_id, exc)

    return {"ok": True, "rebuilt": result}
