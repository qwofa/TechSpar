from llama_index.core import SimpleDirectoryReader

print("=== Testing PDF text extraction ===")
docs = SimpleDirectoryReader("/app/data/users/ced02b8a/resume").load_data()
print("Documents found:", len(docs))
for doc in docs:
    text = doc.get_text()
    print("Text length:", len(text))
    print("First 200 chars:", repr(text[:200]))
