"""Debug: test full embedding flow, including what llama_index does with the response."""
import sys
sys.path.insert(0, ".")

from backend.config import settings
from llama_index.embeddings.openai import OpenAIEmbedding

print("Creating OpenAIEmbedding instance...")
kwargs = {
    "model_name": settings.embedding_api_model_name(),
    "api_key": settings.embedding_api_key,
    "timeout": 15.0,
    "max_retries": 2,
}
if settings.embedding_api_base:
    kwargs["api_base"] = settings.embedding_api_base

embed = OpenAIEmbedding(**kwargs)
print("Instance created:", embed)

print("\nCalling get_text_embedding...")
try:
    result = embed.get_text_embedding("Hello world")
    print("Result dim:", len(result))
    print("OK:", result[:5])
except Exception as exc:
    print(f"ERROR: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()
