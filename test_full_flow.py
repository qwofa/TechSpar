import urllib.request
import json

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('Login OK')

BASE = 'http://localhost'

# Upload a real PDF file first
print('\n=== Uploading PDF ===')
pdf_bytes = open(r'C:\Users\seigi\Desktop\26面试\TechSpar\test_upload.py', 'rb').read()
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="resume.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n').encode()
body += pdf_bytes + f'\r\n--{boundary}--\r\n'.encode()

req_upload = urllib.request.Request(
    f'{BASE}/api/resume/upload',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
    }
)
try:
    resp = urllib.request.urlopen(req_upload, timeout=10)
    result = resp.read().decode()
    print('Upload OK:', result)
    content_type = resp.headers.get('Content-Type', '')
    print('Content-Type:', content_type)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}')
    print('Content-Type:', e.headers.get('Content-Type', ''))
    print('Body:', body[:500])
    if '<html' in body.lower():
        print('*** HTML! ***')

# Test: Try to infer target role - should fail since LLM not working
print('\n=== Testing infer-target-role (expecting LLM error) ===')
req2 = urllib.request.Request(f'{BASE}/api/profile/infer-target-role', data=b'{}', method='POST',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
try:
    resp2 = urllib.request.urlopen(req2, timeout=60)
    print('Response:', resp2.read().decode()[:500])
    if '<html' in resp2.read().decode().lower():
        print('*** HTML! ***')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {e.reason}')
    print('Content-Type:', e.headers.get('Content-Type', ''))
    print('Body (first 300):', body[:300])
    if '<!doctype' in body.lower() or '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
except Exception as e:
    print(f'Exception: {type(e).__name__}: {e}')

# Test: Try to start a resume interview
print('\n=== Testing start interview (expecting LLM error) ===')
start_data = {'mode': 'resume', 'topic': None, 'target_role': 'Frontend Developer'}
req3 = urllib.request.Request(f'{BASE}/api/interview/start',
    data=json.dumps(start_data).encode(), method='POST',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
try:
    resp3 = urllib.request.urlopen(req3, timeout=60)
    result = resp3.read().decode()
    print('Start OK:', result[:300])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {e.reason}')
    print('Content-Type:', e.headers.get('Content-Type', ''))
    print('Body (first 300):', body[:300])
    if '<!doctype' in body.lower() or '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
except Exception as e:
    print(f'Exception: {type(e).__name__}: {e}')

# Test: Check what nginx returns for a non-existent API route
print('\n=== Testing 404 from nginx vs backend ===')
req4 = urllib.request.Request(f'{BASE}/api/nonexistent', headers={'Authorization': f'Bearer {token}'})
try:
    resp4 = urllib.request.urlopen(req4, timeout=5)
    print('Response:', resp4.read().decode()[:300])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {e.reason}')
    print('Content-Type:', e.headers.get('Content-Type', ''))
    print('Body (first 300):', body[:300])
    if '<!doctype' in body.lower() or '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
