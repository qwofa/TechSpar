"""Per-user LLM and embedding providers.

Each provider resolves config in this order: explicit user_id arg → current-user
ContextVar → global .env defaults. Per-user overrides live in provider.json;
empty fields inherit the global default per-field, and a wholly-unset user
inherits the global config entirely.

LLM clients are cheap to construct, so they are built per call. Embedding
backends (esp. local HuggingFace models) are expensive, so they are cached per
(user, config-signature) and rebuilt only when the signature changes.
"""

from langchain_openai import ChatOpenAI
from llama_index.llms.openai_like import OpenAILike

from backend.config import (
    embedding_api_model_of,
    embedding_local_model_of,
    embedding_local_path_of,
    embedding_mode_of,
    embedding_target_of,
    settings,
)
from backend.storage.user_settings import load_user_provider, load_user_services
from backend.user_context import get_current_user_id

# user_key ("__global__" or user_id) → (signature, embed_instance)
_embedding_cache: dict[str, tuple[str, object]] = {}

_DEFAULT_TEMPERATURE = 0.7
_COPILOT_TEMPERATURE = 0.3  # Copilot 场景偏确定性


class ProviderNotConfigured(RuntimeError):
    """A user tried to use an LLM/Embedding they haven't configured. There is no
    global fallback — every user brings their own key. Mapped to a 400 with a
    'go configure' hint in app.py so the UI can route them to onboarding."""

    def __init__(self, what: str):
        self.what = what  # "LLM" | "Embedding"
        super().__init__(f"{what} provider not configured for this user")


def _effective_uid(user_id: str | None) -> str | None:
    return user_id if user_id is not None else get_current_user_id()


# ── Config resolution ──

def resolve_llm_config(user_id: str | None = None) -> dict:
    """Resolve this user's LLM config. Per-user only — no global fallback; missing
    fields stay empty and surface as ProviderNotConfigured when a client is built."""
    uid = _effective_uid(user_id)
    override = load_user_provider(uid)[0] if uid else None
    if override is None:
        return {"api_base": "", "api_key": "", "model": "", "temperature": _DEFAULT_TEMPERATURE}
    return {
        "api_base": override.api_base,
        "api_key": override.api_key,
        "model": override.model,
        "temperature": override.temperature,
    }


def resolve_embedding_config(user_id: str | None = None) -> dict:
    """Resolve this user's embedding config (per-user only, no global fallback)."""
    uid = _effective_uid(user_id)
    override = load_user_provider(uid)[1] if uid else None
    if override is None:
        return {
            "backend": "", "api_base": "", "api_key": "",
            "api_model": "", "local_model": "", "local_path": "",
        }
    return {
        "backend": override.backend,
        "api_base": override.api_base,
        "api_key": override.api_key,
        "api_model": override.api_model,
        "local_model": override.local_model,
        "local_path": override.local_path,
    }


def embedding_signature(user_id: str | None = None) -> str:
    """Vector-compatibility identity (model/dimensions). On-disk indexes and
    memory_vectors rows are valid only for this exact value — when it changes they
    must be wiped and rebuilt. Excludes api_key/api_base, which don't affect vectors."""
    c = resolve_embedding_config(user_id)
    return embedding_target_of(
        c["backend"], c["api_base"], c["api_key"], c["api_model"],
        c["local_model"], c["local_path"], settings.base_dir, "",
    )


def _embedding_cache_sig(c: dict) -> str:
    """Full-config cache key — any field change (incl. api_key/api_base) must
    rebuild the embedding client, even when the model identity is unchanged."""
    return "|".join(
        (c["backend"], c["api_base"], c["api_key"], c["api_model"], c["local_model"], c["local_path"])
    )


# ── LLM ──

def _require_llm(c: dict):
    if not c["api_key"] or not c["model"]:
        raise ProviderNotConfigured("LLM")


def get_langchain_llm(user_id: str | None = None):
    """LangChain ChatModel for LangGraph nodes (via OpenAI-compatible proxy)."""
    c = resolve_llm_config(user_id)
    _require_llm(c)
    return ChatOpenAI(
        model=c["model"],
        api_key=c["api_key"],
        base_url=c["api_base"],
        temperature=c["temperature"],
        streaming=True,
    )


def get_copilot_llm(user_id: str | None = None, streaming: bool = False):
    """Copilot uses the user's own main LLM (no separate Copilot provider)."""
    c = resolve_llm_config(user_id)
    _require_llm(c)
    return ChatOpenAI(
        model=c["model"],
        api_key=c["api_key"],
        base_url=c["api_base"],
        temperature=_COPILOT_TEMPERATURE,
        streaming=streaming,
    )


def get_llama_llm(user_id: str | None = None):
    """LlamaIndex LLM (per call — construction is cheap)."""
    c = resolve_llm_config(user_id)
    _require_llm(c)
    return OpenAILike(
        model=c["model"],
        api_key=c["api_key"],
        api_base=c["api_base"],
        temperature=c["temperature"],
        is_chat_model=True,
    )


# ── Embedding ──

def _build_embedding(c: dict):
    deprecated = ""
    if embedding_mode_of(c["backend"], c["api_base"], c["api_key"]) == "api":
        from llama_index.embeddings.openai import OpenAIEmbedding

        if not c["api_key"]:
            raise ProviderNotConfigured("Embedding")
        model_name = embedding_api_model_of(c["api_model"], deprecated)
        if not model_name:
            raise RuntimeError("EMBEDDING_API_MODEL is required when EMBEDDING_BACKEND=api")
        kwargs = {"model_name": model_name, "api_key": c["api_key"]}
        if c["api_base"]:
            kwargs["api_base"] = c["api_base"]
        return OpenAIEmbedding(**kwargs)

    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as exc:
        raise RuntimeError(
            "Local embeddings require optional dependencies. "
            "Install `pip install -r requirements.local-embedding.txt` "
            "and a torch build that matches your environment."
        ) from exc

    model_path = embedding_local_path_of(c["local_path"], c["local_model"], settings.base_dir, deprecated)
    if model_path is not None:
        return HuggingFaceEmbedding(model_name=str(model_path))
    model_name = embedding_local_model_of(c["local_model"], deprecated)
    if model_name:
        return HuggingFaceEmbedding(model_name=model_name)
    raise RuntimeError(
        "LOCAL_EMBEDDING_MODEL or LOCAL_EMBEDDING_PATH is required when EMBEDDING_BACKEND=local"
    )


def get_embedding(user_id: str | None = None):
    """Embedding model, cached per (user, full-config signature)."""
    c = resolve_embedding_config(user_id)
    sig = _embedding_cache_sig(c)
    key = _effective_uid(user_id) or "__global__"
    cached = _embedding_cache.get(key)
    if cached and cached[0] == sig:
        return cached[1]
    inst = _build_embedding(c)
    _embedding_cache[key] = (sig, inst)
    return inst


def reset_embedding_cache(user_id: str | None = None):
    """Drop cached embedding(s) so the next call rebuilds. None clears all users."""
    if user_id is None:
        _embedding_cache.clear()
    else:
        _embedding_cache.pop(user_id, None)


# ── Optional service credentials (per-user, no global fallback) ──

def resolve_dashscope_key(user_id: str | None = None) -> str:
    """DashScope key for ASR (语音输入 / 录音转写 / Copilot 实时)。未配置返回空串。"""
    uid = _effective_uid(user_id)
    return load_user_services(uid).dashscope_api_key if uid else ""


def resolve_tavily_key(user_id: str | None = None) -> str:
    """Tavily key for Copilot 联网搜索。未配置返回空串。"""
    uid = _effective_uid(user_id)
    return load_user_services(uid).tavily_api_key if uid else ""


def resolve_oss_config(user_id: str | None = None) -> dict:
    """阿里云 OSS 配置(录音复盘长音频上传)。未配置字段为空串。"""
    uid = _effective_uid(user_id)
    s = load_user_services(uid) if uid else None
    return {
        "access_key_id": s.oss_access_key_id if s else "",
        "access_key_secret": s.oss_access_key_secret if s else "",
        "bucket": s.oss_bucket if s else "",
        "endpoint": s.oss_endpoint if s else "",
    }


def provider_status(user_id: str | None = None) -> dict:
    """Whether the user has the two essentials configured. Drives the first-run
    onboarding gate (DashScope/Tavily/OSS are optional and not checked here)."""
    llm = resolve_llm_config(user_id)
    emb = resolve_embedding_config(user_id)
    if embedding_mode_of(emb["backend"], emb["api_base"], emb["api_key"]) == "api":
        emb_ok = bool(emb["api_key"])
    else:
        emb_ok = bool(emb["local_model"] or emb["local_path"])
    return {"llm": bool(llm["api_key"] and llm["model"]), "embedding": emb_ok}
