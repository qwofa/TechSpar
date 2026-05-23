"""Upload a real PDF and test the full flow."""
import urllib.request
import json

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('Login OK')

# Read the real PDF
with open(r'c:\Users\seigi\Desktop\26面试\TechSpar\test_resume.pdf', 'rb') as f:
    pdf_bytes = f.read()
print(f'PDF size: {len(pdf_bytes)} bytes')
print(f'PDF header: {pdf_bytes[:8]}')

# Upload PDF
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body_parts = [
    f'--{boundary}\r\n'.encode(),
    f'Content-Disposition: form-data; name="file"; filename="test_resume.pdf"\r\n'.encode(),
    f'Content-Type: application/pdf\r\n\r\n'.encode(),
    pdf_bytes,
    f'\r\n--{boundary}--\r\n'.encode()
]
body = b''.join(body_parts)

req_upload = urllib.request.Request(
    'http://localhost/api/resume/upload',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
    }
)
try:
    resp = urllib.request.urlopen(req_upload, timeout=10)
    result = json.loads(resp.read().decode())
    print('Upload SUCCESS:', result)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {body[:300]}')
    if '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

# Test infer target role (with longer timeout to see the improved error message)
print('\n=== Testing infer-target-role (expecting clear error now) ===')
req2 = urllib.request.Request('http://localhost/api/profile/infer-target-role', data=b'{}', method='POST',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
try:
    resp2 = urllib.request.urlopen(req2, timeout=30)
    result = json.loads(resp2.read().decode())
    print('Infer SUCCESS:', result)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {body[:500]}')
    if '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
    else:
        print('*** Got JSON error (good - clear message!) ***')
except Exception as e:
    print(f'Exception: {type(e).__name__}: {e}')

# Check resume status
print('\n=== Resume status ===')
req3 = urllib.request.Request('http://localhost/api/resume/status',
    headers={'Authorization': f'Bearer {token}'})
resp3 = urllib.request.urlopen(req3, timeout=10)
print('Status:', resp3.read().decode())
