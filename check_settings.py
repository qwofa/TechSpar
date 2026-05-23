"""Check settings as seen by the running backend."""
import sys
import os
os.chdir(r'c:\Users\seigi\Desktop\26面试\TechSpar')
sys.path.insert(0, r'c:\Users\seigi\Desktop\26面试\TechSpar')

from backend.config import settings
print(f'embedding_backend_mode: {settings.embedding_backend_mode()}')
print(f'embedding_api_base: {settings.embedding_api_base}')
print(f'embedding_api_key set: {bool(settings.embedding_api_key)}')
print(f'embedding_api_model: {settings.embedding_api_model_name()}')
print(f'api_base: {settings.api_base}')
print(f'model: {settings.model}')
print(f'local_embedding_path: {settings.local_embedding_model_path()}')
print(f'base_dir: {settings.base_dir}')

# Check what the embedding actually returns
print('\n--- Testing embedding ---')
try:
    from backend.llm_provider import get_embedding
    emb = get_embedding()
    result = emb.get_text_embedding("hello")
    print(f'Embedding dim: {len(result)}')
except Exception as e:
    print(f'Embedding error: {type(e).__name__}: {e}')

# Check what the LLM actually returns
print('\n--- Testing LLM ---')
try:
    from backend.llm_provider import get_langchain_llm
    from langchain_core.messages import HumanMessage
    llm = get_langchain_llm()
    resp = llm.invoke([HumanMessage(content="Say hello")])
    print(f'LLM response: {resp.content[:100]}')
except Exception as e:
    print(f'LLM error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
