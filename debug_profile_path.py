"""Direct debug: simulate the exact API call path to find 404 source."""
import sys
import os
os.chdir(r'c:\Users\seigi\Desktop\26面试\TechSpar')
sys.path.insert(0, r'c:\Users\seigi\Desktop\26面试\TechSpar')

# Get the user ID
user_dir = r'c:\Users\seigi\Desktop\26面试\TechSpar\data\users'
user_id = os.listdir(user_dir)[0]
print(f'User ID: {user_id}')

# Simulate the exact profile.py code path
print('\n=== Step 1: Check resume exists ===')
from backend.config import settings
resume_dir = settings.user_resume_path(user_id)
pdfs = list(resume_dir.glob("*.pdf"))
print(f'Resume dir: {resume_dir}')
print(f'PDFs found: {[p.name for p in pdfs]}')
if not pdfs:
    print('ERROR: No PDF found!')
    exit(1)
print('Resume exists - OK')

# Step 2: Simulate profile.py's query_resume call
print('\n=== Step 2: query_resume (exactly as profile.py does) ===')
from backend.indexer import query_resume
try:
    resume_ctx = query_resume(
        "列出候选人的技术栈、项目方向、教育背景与目标岗位相关线索",
        user_id
    )
    print(f'SUCCESS! Resume context length: {len(resume_ctx)}')
    print(f'Preview: {resume_ctx[:200]}')
except Exception as exc:
    print(f'FAILED: {type(exc).__name__}: {exc}')
    import traceback
    traceback.print_exc()

# Step 3: Simulate the LLM call (profile.py does this after query_resume)
print('\n=== Step 3: LLM call (as profile.py does) ===')
from backend.llm_provider import get_langchain_llm
from langchain_core.messages import HumanMessage, SystemMessage
from backend.prompts.interviewer import INFER_TARGET_ROLE_PROMPT

try:
    llm = get_langchain_llm()
    response = llm.invoke([
        SystemMessage(content="你是岗位推断引擎。只返回岗位名称，不要任何其他内容。"),
        HumanMessage(content=INFER_TARGET_ROLE_PROMPT.format(resume_context=resume_ctx)),
    ])
    role = (response.content or "").strip().strip('"').strip("「」").strip()
    print(f'SUCCESS! Target role: {role}')
except Exception as exc:
    print(f'FAILED: {type(exc).__name__}: {exc}')
    import traceback
    traceback.print_exc()
