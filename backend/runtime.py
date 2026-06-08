"""Shared in-memory runtime state for API modules."""

import logging

from backend.models import InterviewMode
from backend.storage.sessions import get_session

logger = logging.getLogger("uvicorn")

# Hot caches for interactive sessions and async task status.
_graphs: dict[str, dict] = {}
_drill_sessions: dict[str, dict] = {}
_job_prep_sessions: dict[str, dict] = {}
_task_status: dict[str, dict] = {}
_copilot_sessions: dict[str, dict] = {}


def set_task_status(
    task_id: str,
    status: str,
    task_type: str,
    *,
    user_id: str | None = None,
    **extra,
) -> dict:
    payload = {"status": status, "type": task_type, **extra}
    if user_id is not None:
        payload["user_id"] = user_id
    _task_status[task_id] = payload
    return payload


def get_task_status(task_id: str, *, user_id: str | None = None) -> dict | None:
    entry = _task_status.get(task_id)
    if entry is None:
        return None
    if user_id is not None and entry.get("user_id") not in (None, user_id):
        return None
    return entry


async def get_or_restore_resume_graph(session_id: str, user_id: str) -> dict | None:
    """Return the cached graph entry, or rebuild it from the checkpoint store."""
    from backend.graphs.resume_interview import compile_resume_interview

    entry = _graphs.get(session_id)
    if entry is not None:
        return entry if entry.get("user_id") == user_id else None

    session = get_session(session_id, user_id=user_id)
    if not session or session.get("mode") != InterviewMode.RESUME.value:
        return None

    graph = compile_resume_interview(user_id)
    config = {"configurable": {"thread_id": session_id}}
    state = await graph.aget_state(config)
    if not state.values:
        return None

    entry = {
        "graph": graph,
        "config": config,
        "mode": InterviewMode.RESUME,
        "topic": session.get("topic"),
        "user_id": user_id,
    }
    _graphs[session_id] = entry
    return entry
