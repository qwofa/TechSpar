"""Knowledge and graph routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from backend.auth import get_current_user
from backend.config import settings
from backend.graph import build_graph
from backend.indexer import invalidate_topic, load_topics
from backend.llm_provider import get_langchain_llm

router = APIRouter(prefix="/api")


def _read_markdown_files(topic_dir):
    return [
        {"filename": file.name, "content": file.read_text(encoding="utf-8")}
        for file in sorted(topic_dir.glob("*.md"))
    ]


def _update_topic_file(filepath, content: str, topic: str, user_id: str) -> bool:
    if not filepath.exists():
        return False
    filepath.write_text(content, encoding="utf-8")
    invalidate_topic(topic, user_id)
    return True


def _create_topic_file(filepath, content: str, topic: str, user_id: str) -> bool:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if filepath.exists():
        return False
    filepath.write_text(content, encoding="utf-8")
    invalidate_topic(topic, user_id)
    return True


def _delete_topic_file(filepath, topic: str, user_id: str) -> bool:
    if not filepath.exists():
        return False
    filepath.unlink()
    invalidate_topic(topic, user_id)
    return True


def _generate_core_content(llm, topic_name: str) -> str:
    response = llm.invoke([
        SystemMessage(content="你是一位资深技术面试官，擅长梳理技术领域的核心知识体系。"),
        HumanMessage(content=(
            f"请为「{topic_name}」这个技术领域生成一份核心知识梳理，作为面试出题和评分的参考依据。\n\n"
            "要求：\n"
            "- 用 Markdown 格式\n"
            f"- 以 `# {topic_name}` 作为标题\n"
            "- 列出该领域最核心的 8-12 个知识点，每个用二级标题\n"
            "- 每个知识点下用简洁的要点说明关键概念、原理、常见面试考点\n"
            "- 重点覆盖：核心概念、工作原理、最佳实践、常见陷阱\n"
            "- 保持简洁实用，面向面试准备场景\n"
            "- 直接输出 Markdown 内容，不要包裹在代码块中"
        )),
    ])
    return response.content.strip()


def _save_generated_core(topic_dir, content: str, topic: str, user_id: str) -> None:
    topic_dir.mkdir(parents=True, exist_ok=True)
    readme = topic_dir / "README.md"
    readme.write_text(content, encoding="utf-8")
    invalidate_topic(topic, user_id)


def _read_high_freq_file(filepath) -> str:
    if not filepath.exists():
        return ""
    return filepath.read_text(encoding="utf-8")


def _write_high_freq_file(filepath, content: str) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")


@router.get("/knowledge/{topic}/core")
async def get_core_knowledge(topic: str, user_id: str = Depends(get_current_user)):
    """List core knowledge files for a topic."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    topic_dir = settings.user_knowledge_path(user_id) / topics[topic]["dir"]
    if not topic_dir.exists():
        return []

    files = await asyncio.to_thread(_read_markdown_files, topic_dir)
    return files


@router.put("/knowledge/{topic}/core/{filename}")
async def update_core_knowledge(
    topic: str,
    filename: str,
    body: dict,
    user_id: str = Depends(get_current_user),
):
    """Update a core knowledge file."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    filepath = settings.user_knowledge_path(user_id) / topics[topic]["dir"] / filename
    updated = await asyncio.to_thread(_update_topic_file, filepath, body.get("content", ""), topic, user_id)
    if not updated:
        raise HTTPException(404, f"File not found: {filename}")

    return {"ok": True}


@router.delete("/knowledge/{topic}/core/{filename}")
async def delete_core_knowledge(
    topic: str,
    filename: str,
    user_id: str = Depends(get_current_user),
):
    """Delete a core knowledge file."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    filepath = settings.user_knowledge_path(user_id) / topics[topic]["dir"] / filename
    deleted = await asyncio.to_thread(_delete_topic_file, filepath, topic, user_id)
    if not deleted:
        raise HTTPException(404, f"File not found: {filename}")

    return {"ok": True}


@router.post("/knowledge/{topic}/core")
async def create_core_knowledge(topic: str, body: dict, user_id: str = Depends(get_current_user)):
    """Create a new core knowledge file."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    filename = body.get("filename", "").strip()
    if not filename or not filename.endswith(".md"):
        raise HTTPException(400, "Filename must end with .md")

    filepath = settings.user_knowledge_path(user_id) / topics[topic]["dir"] / filename
    created = await asyncio.to_thread(_create_topic_file, filepath, body.get("content", ""), topic, user_id)
    if not created:
        raise HTTPException(409, f"File already exists: {filename}")

    return {"ok": True, "filename": filename}


@router.post("/knowledge/{topic}/generate")
async def generate_core_knowledge(topic: str, user_id: str = Depends(get_current_user)):
    """Use LLM to generate foundational knowledge content for a topic."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    topic_name = topics[topic].get("name", topic)
    llm = get_langchain_llm(user_id)
    content = await asyncio.to_thread(_generate_core_content, llm, topic_name)

    topic_dir = settings.user_knowledge_path(user_id) / topics[topic]["dir"]
    await asyncio.to_thread(_save_generated_core, topic_dir, content, topic, user_id)
    return {"ok": True, "content": content}


@router.get("/knowledge/{topic}/high_freq")
async def get_high_freq(topic: str, user_id: str = Depends(get_current_user)):
    """Get high-frequency question bank for a topic."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    filepath = settings.user_high_freq_path(user_id) / f"{topic}.md"
    content = await asyncio.to_thread(_read_high_freq_file, filepath)
    return {"content": content}


@router.put("/knowledge/{topic}/high_freq")
async def update_high_freq(topic: str, body: dict, user_id: str = Depends(get_current_user)):
    """Update high-frequency question bank for a topic."""
    topics = await asyncio.to_thread(load_topics, user_id)
    if topic not in topics:
        raise HTTPException(400, f"Unknown topic: {topic}")

    filepath = settings.user_high_freq_path(user_id) / f"{topic}.md"
    await asyncio.to_thread(_write_high_freq_file, filepath, body.get("content", ""))
    return {"ok": True}


@router.get("/graph/{topic}")
def get_topic_graph(topic: str, user_id: str = Depends(get_current_user)):
    """Build question relationship graph for a topic."""
    return build_graph(topic, user_id)
