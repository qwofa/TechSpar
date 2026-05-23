"""Reproduce the exact code path: copilot precompute_embeddings via get_embedding()."""
import sys
sys.path.insert(0, ".")

import asyncio
import traceback

# Simulate what happens in copilot.py _init_copilot_session
async def simulate_precompute():
    from backend.copilot.strategy_tree import StrategyTreeNavigator

    # Minimal strategy tree with 1 node
    tree = {
        "nodes": {
            "root_0": {
                "topic": "自我介绍",
                "intent": "self_intro",
                "sample_questions": ["请做一个简短的自我介绍"],
                "children": [],
            }
        },
        "root_nodes": ["root_0"],
        "phase_order": [],
    }

    navigator = StrategyTreeNavigator(tree)
    print("Navigator created OK")

    try:
        await navigator.precompute_embeddings()
        print("precompute_embeddings OK")
        print(f"Embeddings: {navigator._embeddings}")
    except Exception as exc:
        print(f"ERROR during precompute_embeddings: {type(exc).__name__}: {exc}")
        traceback.print_exc()

asyncio.run(simulate_precompute())
