"""Test real PDF upload and full resume flow."""
import urllib.request
import json
import os

BASE = 'http://localhost'
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request(f'{BASE}/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('1. Login OK')

# Read the real PDF
pdf_path = r'c:\Users\seigi\Desktop\26面试\TechSpar\test_resume.pdf'
if not os.path.exists(pdf_path):
    print(f'ERROR: PDF not found at {pdf_path}')
    exit(1)

with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()
print(f'2. PDF size: {len(pdf_bytes)} bytes')

# Upload
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body_parts = [
    b'--' + boundary.encode() + b'\r\n',
    b'Content-Disposition: form-data; name="file"; filename="test_resume.pdf"\r\n',
    b'Content-Type: application/pdf\r\n\r\n',
    pdf_bytes,
    b'\r\n--' + boundary.encode() + b'--\r\n'
]
body = b''.join(body_parts)

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
    result = json.loads(resp.read().decode())
    print('3. Upload SUCCESS:', result)
except urllib.error.HTTPError as e:
    body_err = e.read().decode()
    print(f'3. HTTP {e.code}: {body_err[:300]}')
    if '<html' in body_err.lower():
        print('    *** HTML RESPONSE! ***')
except Exception as e:
    print(f'3. Error: {type(e).__name__}: {e}')

# Check resume status
req_status = urllib.request.Request(
    f'{BASE}/api/resume/status',
    headers={'Authorization': f'Bearer {token}'}
)
try:
    resp = urllib.request.urlopen(req_status, timeout=10)
    print('4. Resume status:', resp.read().decode())
except Exception as e:
    print(f'4. Status error: {e}')

# Test infer-target-role (with long timeout)
print('\n5. Testing infer-target-role (30s timeout)...')
req_infer = urllib.request.Request(
    f'{BASE}/api/profile/infer-target-role',
    data=b'{}',
    method='POST',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
)
try:
    resp = urllib.request.urlopen(req_infer, timeout=30)
    result = json.loads(resp.read().decode())
    print(f'   Infer SUCCESS: {result}')
except urllib.error.HTTPError as e:
    body_err = e.read().decode()
    print(f'   HTTP {e.code}: {body_err[:500]}')
    if '<html' in body_err.lower():
        print('   *** HTML RESPONSE! ***')
except Exception as e:
    print(f'   Error: {type(e).__name__}: {e}')
