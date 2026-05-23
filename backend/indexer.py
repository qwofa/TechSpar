"""LlamaIndex indexing for resume and interview knowledge base."""
import json
import logging
import queue
import threading
from pathlib import Path
from typing import Union

from llama_index.core import (
    Document,
    ListIndex,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    Settings as LlamaSettings,
)

from backend.config import settings
from backend.llm_provider import get_llama_llm, get_embedding

logger = logging.getLogger("uvicorn")

# In-memory cache: value can be VectorStoreIndex OR list[Document]
_index_cache: dict[tuple[str, str], Union["VectorStoreIndex", list["Document"]]] = {}


def _build_index_with_timeout(docs, cache_dir, timeout_seconds=10.0):
    """Build vector index in a thread with a timeout.

    Returns (result, exception) tuple.
    - result: VectorStoreIndex on success, None on failure/timeout.
    - exception: Exception instance on failure, None on success.
    """
    result = None
    exc_info = None

    def worker():
        nonlocal result, exc_info
        try:
            result = VectorStoreIndex.from_documents(docs)
            cache_dir.mkdir(parents=True, exist_ok=True)
            result.storage_context.persist(persist_dir=str(cache_dir))
        except Exception:
            import sys
            exc_info = sys.exc_info()

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=timeout_seconds)
    if t.is_alive():
        # Timeout — thread is still running (embedding API unreachable)
        return None, TimeoutError(f"Embedding API did not respond within {timeout_seconds}s")
    if exc_info:
        return None, exc_info[1]
    return result, None


def load_topics(user_id: str) -> dict:
    """Load topics from user's topics.json. Returns {key: {name, icon, dir}}."""
    from backend.preset_topics import ensure_preset_topics

    ensure_preset_topics(user_id)
    path = settings.user_topics_path(user_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_topics(topics: dict, user_id: str):
    """Write topics back to user's topics.json."""
    path = settings.user_topics_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(topics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_topic_map(user_id: str) -> dict[str, str]:
    """Returns {key: dir_name}."""
    return {k: v["dir"] for k, v in load_topics(user_id).items()}


def _init_llama_settings():
    # chunk_size 需小于 embedding API 的 token 限制（SiliconFlow BAAI/bge-large-zh-v1.5 = 512 tokens）
    # 中文约 1.5~2 字符/token，取 256 字符 ≈ 128~170 tokens，留足安全余量
    LlamaSettings.chunk_size = 256
    LlamaSettings.chunk_overlap = 50
    LlamaSettings.llm = get_llama_llm()
    LlamaSettings.embed_model = get_embedding()


def build_resume_index(user_id: str, force_rebuild: bool = False) -> Union["VectorStoreIndex", list["Document"]]:
    """Build or load the resume index.

    Uses embedding-based vector index when the embedding API is reachable.
    Falls back to a plain ListIndex (no embeddings, no LLM calls) when unreachable.
    """
    cache_key = (user_id, "resume")
    if cache_key in _index_cache and not force_rebuild:
        return _index_cache[cache_key]

    _init_llama_settings()
    resume_path = settings.user_resume_path(user_id)

    # Step 1: Load PDF text
    try:
        docs = SimpleDirectoryReader(
            input_dir=str(resume_path),
            recursive=True,
        ).load_data()
    except Exception as exc:
        raise RuntimeError(
            f"简历文件解析失败（可能是 PDF 损坏或格式不支持）：{exc}"
        ) from exc
    if not docs:
        raise RuntimeError(
            "未能从简历中提取文本内容，请确认 PDF 包含可提取的文字而非纯图片扫描件。"
        )

    cache_dir = settings.user_index_cache_path(user_id) / "resume"

    # Step 2: Try to build vector index (requires embedding API)
    # Use a 10-second thread timeout to fail fast when embedding API is unreachable.
    if cache_dir.exists() and not force_rebuild:
        try:
            storage_context = StorageContext.from_defaults(persist_dir=str(cache_dir))
            index = load_index_from_storage(storage_context)
        except Exception as exc:
            exc_msg = str(exc).lower()
            cause = str(exc.__cause__).lower() if exc.__cause__ else ""
            combined = exc_msg + cause
            network_failure = any(kw in combined for kw in [
                "timeout", "timed out", "connection", "httpsconnectionpool",
                "503", "502", "apitimeouterror", "retry", "network", "unreachable",
                "request timed out",
            ])
            if network_failure:
                logger.warning(
                    "Embedding API unreachable (load failure: %s) — using fallback for resume %s",
                    exc, user_id,
                )
                _index_cache[cache_key] = docs
                return _index_cache[cache_key]
            raise
    else:
        index, exc = _build_index_with_timeout(docs, cache_dir, timeout_seconds=10.0)
        if exc is not None:
            if isinstance(exc, TimeoutError):
                logger.warning("Embedding API unreachable (timeout) — using fallback for resume %s", user_id)
            else:
                exc_msg = str(exc).lower()
                cause = str(exc.__cause__).lower() if exc.__cause__ else ""
                combined = exc_msg + cause
                network_failure = any(kw in combined for kw in [
                    "timeout", "timed out", "connection", "httpsconnectionpool",
                    "503", "502", "apitimeouterror", "retry", "network", "unreachable",
                ])
                if not network_failure:
                    raise exc
                logger.warning(
                    "Embedding API unreachable (%s) — using fallback for resume %s",
                    exc, user_id,
                )
            _index_cache[cache_key] = docs
            return _index_cache[cache_key]
        cache_dir.mkdir(parents=True, exist_ok=True)
        _index_cache[cache_key] = index
        return _index_cache[cache_key]

    _index_cache[cache_key] = index
    return index


def build_topic_index(topic: str, user_id: str, force_rebuild: bool = False) -> VectorStoreIndex:
    """Build or load index for a specific knowledge topic."""
    cache_key = (user_id, topic)
    if cache_key in _index_cache and not force_rebuild:
        return _index_cache[cache_key]

    _init_llama_settings()

    topic_map = get_topic_map(user_id)
    if topic not in topic_map:
        raise ValueError(f"Unknown topic: {topic}. Available: {list(topic_map.keys())}")

    dir_name = topic_map[topic]
    topic_dir = settings.user_knowledge_path(user_id) / dir_name
    cache_dir = settings.user_index_cache_path(user_id) / topic

    if cache_dir.exists() and not force_rebuild:
        storage_context = StorageContext.from_defaults(persist_dir=str(cache_dir))
        index = load_index_from_storage(storage_context)
    else:
        if not topic_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {topic_dir}")

        docs = SimpleDirectoryReader(
            input_dir=str(topic_dir),
            recursive=True,
            required_exts=[".md", ".txt", ".py"],
        ).load_data()

        if not docs:
            raise ValueError(f"No documents found in {topic_dir}")

        index = VectorStoreIndex.from_documents(docs)
        cache_dir.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(cache_dir))

    _index_cache[cache_key] = index
    return index


def query_resume(question: str, user_id: str, top_k: int = 3) -> str:
    """Query the resume index.

    Strategy:
    1. Try vector-index query (fast, semantic search) — requires working OpenAI API.
    2. If embedding API is unreachable, build_resume_index returns raw documents.
       In that case, return all text so the LLM can work with it.
    3. If the LLM call for synthesis times out or fails, fall back to raw text.
    """
    index = build_resume_index(user_id)
    if isinstance(index, (list, tuple)):
        # Fallback: embedding unreachable, return all text directly
        return _extract_resume_text_fallback(user_id)

    import concurrent.futures
    engine = index.as_query_engine(similarity_top_k=top_k)

    def _do_query():
        return engine.query(question)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_do_query)
        try:
            response = future.result(timeout=15.0)
            return str(response)
        except concurrent.futures.TimeoutError:
            logger.warning("query_resume timed out after 15s for user %s — using raw text fallback", user_id)
            return _extract_resume_text_fallback(user_id)
        except Exception as exc:
            exc_msg = str(exc).lower()
            cause_msg = str(exc.__cause__).lower() if exc.__cause__ else ""
            combined = exc_msg + cause_msg
            if any(kw in combined for kw in ["timeout", "timed out", "rate", "limit", "429", "cooldown"]):
                logger.warning("query_resume LLM error for user %s: %s — using raw text fallback", user_id, exc)
                return _extract_resume_text_fallback(user_id)
            # For other errors (e.g., network), let it propagate so the caller handles it
            raise


def _extract_resume_text_fallback(user_id: str) -> str:
    """Extract raw text from resume PDF without using embeddings.

    Used when the OpenAI Embedding API is unreachable.
    """
    from llama_index.core import SimpleDirectoryReader

    resume_path = settings.user_resume_path(user_id)
    pdf_files = list(resume_path.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError("未找到简历文件，请重新上传")

    texts = []
    for pdf_file in pdf_files:
        try:
            reader = SimpleDirectoryReader(input_files=[str(pdf_file)])
            docs = reader.load_data()
            for doc in docs:
                text = (doc.text or "").strip()
                if text:
                    texts.append(text)
        except Exception as exc:
            raise RuntimeError(
                f"无法读取简历文件 '{pdf_file.name}'（可能是 PDF 损坏或图片扫描件）：{exc}"
            )

    if not texts:
        raise RuntimeError(
            "未能从简历中提取文本内容，请确认 PDF 包含可提取的文字而非纯图片扫描件。"
        )

    return "\n\n".join(texts)


def query_topic(topic: str, question: str, user_id: str, top_k: int = 5) -> str:
    """Query a topic knowledge base."""
    index = build_topic_index(topic, user_id)
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    return str(response)


def retrieve_topic_context(topic: str, question: str, user_id: str, top_k: int = 5) -> list[str]:
    """Retrieve raw text chunks from topic index (for answer evaluation)."""
    index = build_topic_index(topic, user_id)
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)
    return [node.get_content() for node in nodes]
