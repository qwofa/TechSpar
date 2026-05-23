"""Comprehensive diagnosis of the resume upload and processing pipeline."""
import urllib.request
import json

BASE = 'http://localhost'

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request(f'{BASE}/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('1. Login OK')

def api_get(path, token):
    req = urllib.request.Request(f'{BASE}{path}',
                                  headers={'Authorization': f'Bearer {token}'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return f"Error: {e}"

def api_post(path, token, data=None, content_type='application/json', timeout=10):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f'{BASE}{path}', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {token}',
                                          'Content-Type': content_type})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:500]}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

# Step 2: Check resume status (before upload)
print('\n2. Resume status (before upload):')
result = api_get('/api/resume/status', token)
print(f'   {result}')

# Step 3: Check if there's a real PDF to upload
import os
pdf_path = r'c:\Users\seigi\Desktop\26面试\TechSpar\test_resume.pdf'
if os.path.exists(pdf_path):
    print(f'\n3. Found test PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)')
else:
    print(f'\n3. No test PDF found at {pdf_path}')

# Check if there's a data directory for the admin user
data_dir = r'c:\Users\seigi\Desktop\26面试\TechSpar\data\users'
if os.path.exists(data_dir):
    print(f'\n4. User data directories found:')
    for d in os.listdir(data_dir):
        resume_dir = os.path.join(data_dir, d, 'resume')
        if os.path.exists(resume_dir):
            files = os.listdir(resume_dir)
            print(f'   User {d}: resume={files}')
        else:
            print(f'   User {d}: no resume dir')
else:
    print(f'\n4. No data directory found at {data_dir}')

# Step 5: Check LLM API connectivity
print('\n5. Checking LLM API (cn.wzjself.org):')
try:
    req_llm = urllib.request.Request(
        'https://cn.wzjself.org/v1/models',
        headers={'Authorization': f'Bearer sk-live-652f527f5245cf54495a8d12d7c7f298eefa'}
    )
    resp_llm = urllib.request.urlopen(req_llm, timeout=10)
    models = json.loads(resp_llm.read())
    model_names = [m['id'] for m in models.get('data', [])]
    print(f'   Available models: {model_names[:5]}')
except Exception as e:
    print(f'   Error: {type(e).__name__}: {e}')

# Step 6: Check Embedding API connectivity
print('\n6. Checking Embedding API (api.siliconflow.cn):')
try:
    req_emb = urllib.request.Request(
        'https://api.siliconflow.cn/v1/model/list',
        headers={'Authorization': f'Bearer sk-hspbmmdlwdsafyzxwjqcwccgpbtdceuqfighoxtjhayyjuuj'}
    )
    resp_emb = urllib.request.urlopen(req_emb, timeout=10)
    print(f'   Response: {resp_emb.read().decode()[:200]}')
except Exception as e:
    print(f'   Error: {type(e).__name__}: {e}')

# Step 7: Check if main.py is running via uvicorn
print('\n7. Checking backend app info:')
try:
    req_health = urllib.request.Request(f'{BASE}/api/topics', headers={'Authorization': f'Bearer {token}'})
    resp_health = urllib.request.urlopen(req_health, timeout=5)
    print(f'   Topics endpoint OK')
except Exception as e:
    print(f'   Error: {e}')

# Step 8: Check if there are any Python processes
import subprocess
print('\n8. Checking for running Python/uvicorn processes:')
try:
    result = subprocess.run(['tasklist'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'python' in line.lower() or 'uvicorn' in line.lower() or 'node' in line.lower():
            print(f'   {line}')
except:
    print('   (could not list processes)')
