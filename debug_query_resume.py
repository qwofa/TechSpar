"""Debug query_resume to find the exact source of 404."""
import sys
import os
os.chdir(r'c:\Users\seigi\Desktop\26面试\TechSpar')
sys.path.insert(0, '.')

from backend.config import settings

# Find user ID
user_dir = r'c:\Users\seigi\Desktop\26面试\TechSpar\data\users'
user_ids = os.listdir(user_dir)
user_id = user_ids[0]
print(f'User ID: {user_id}')

# Test Step 1: build_resume_index
print('\n=== Testing build_resume_index ===')
try:
    from backend.indexer import build_resume_index
    result = build_resume_index(user_id, force_rebuild=True)
    print(f'Result type: {type(result).__name__}')
    if isinstance(result, list):
        print(f'Docs count: {len(result)}')
        for doc in result:
            print(f'  Text: {doc.text[:100]}')
    else:
        print(f'Index type: {type(result).__name__}')
except Exception as e:
    import traceback
    print(f'build_resume_index FAILED: {type(e).__name__}: {e}')
    traceback.print_exc()

# Test Step 2: query_resume
print('\n=== Testing query_resume ===')
try:
    from backend.indexer import query_resume
    result = query_resume("列出候选人信息", user_id)
    print(f'Result: {result[:200]}')
except Exception as e:
    import traceback
    print(f'query_resume FAILED: {type(e).__name__}: {e}')
    traceback.print_exc()
