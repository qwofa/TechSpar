"""Quick test: does the configured embedding backend work?"""
import sys
sys.path.insert(0, ".")

from backend.llm_provider import get_embedding
from backend.config import settings

print("=== Embedding Config ===")
print(f"  Backend mode : {settings.embedding_backend_mode()}")
print(f"  API Base     : {settings.embedding_api_base}")
print(f"  API Model    : {settings.embedding_api_model_name()}")
print(f"  API Key      : {'[set]' if settings.embedding_api_key else '[empty]'}")
print()

try:
    embed = get_embedding()
    print("Embedding instance created OK.")

    result = embed.get_text_embedding("Hello world, this is a test.")
    print(f"Embedding dim   : {len(result)}")
    print(f"First 5 values  : {result[:5]}")

    # Batch test
    results = embed.get_text_embedding_batch(["你好", "世界"])
    print(f"Batch results   : {len(results)} items, dims = {[len(r) for r in results]}")

    print()
    print("=== ALL TESTS PASSED ===")
except Exception as exc:
    print(f"ERROR: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
