"""Reproduce the full '立即开始模拟' flow end-to-end, with proper startup."""
import sys
sys.path.insert(0, ".")

import asyncio
import traceback

async def main():
    # ── Step 0: Initialize checkpointer (normally done by FastAPI lifespan) ──
    from backend.graphs.resume_interview import init_resume_checkpointer
    await init_resume_checkpointer()
    print("Checkpointer initialized OK")

    user_id = "admin"

    print("\n=== Step 1: compile_resume_interview ===")
    try:
        from backend.graphs.resume_interview import compile_resume_interview
        graph = compile_resume_interview(user_id)
        print("Graph compiled OK")
    except Exception as exc:
        print(f"FAILED compile: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return

    print("\n=== Step 2: invoke init node (equivalent to /api/interview/start) ===")
    try:
        config = {"configurable": {"thread_id": "test-session-123"}}
        result = await graph.ainvoke(
            {"target_role": "AI 应用开发工程师"},
            config
        )
        print("AINVOKE OK")
        print(f"  Keys in result: {list(result.keys())}")
        if result.get("messages"):
            last_msg = result["messages"][-1]
            print(f"  Last message type: {type(last_msg).__name__}")
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            print(f"  Last message content (first 300): {content[:300]}")
        print(f"  Phase: {result.get('phase')}")
        print(f"  Is finished: {result.get('is_finished')}")
        print("\n=== ALL TESTS PASSED ===")
    except Exception as exc:
        print(f"FAILED ainvoke: {type(exc).__name__}: {exc}")
        traceback.print_exc()

asyncio.run(main())
