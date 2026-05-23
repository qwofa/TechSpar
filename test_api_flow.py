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

def api_get(path):
    req = urllib.request.Request(f'{BASE}{path}', headers={'Authorization': f'Bearer {token}'})
    resp = urllib.request.urlopen(req, timeout=10)
    return resp

def api_post(path, data=None, content_type='application/json'):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f'{BASE}{path}', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {token}',
                                          'Content-Type': content_type})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e, e.read().decode()

print('\n=== Test 1: Resume status ===')
try:
    resp = api_get('/api/resume/status')
    print('Status:', resp.read().decode())
except Exception as e:
    print('Error:', e)

print('\n=== Test 2: Resume upload ===')
# Create minimal PDF
pdf_content = b'%PDF-1.4\ntest\n%%EOF'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="@my.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n').encode()
body += pdf_content + f'\r\n--{boundary}--\r\n'.encode()

req_upload = urllib.request.Request(
    f'{BASE}/api/resume/upload',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }
)
try:
    resp = urllib.request.urlopen(req_upload, timeout=30)
    print('Upload SUCCESS:', resp.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}:', body[:300])
    if '<html' in body.lower():
        print('*** HTML RESPONSE ***')

print('\n=== Test 3: Infer target role (most likely to fail) ===')
resp_or_err, body = api_post('/api/profile/infer-target-role')
print(f'Status: {resp_or_err.code if hasattr(resp_or_err, "code") else "OK"}')
print(f'Body: {body[:500]}')
if '<html' in body.lower():
    print('*** HTML RESPONSE ***')

print('\n=== Test 4: Resume status after upload ===')
try:
    resp = api_get('/api/resume/status')
    print('Status:', resp.read().decode())
except Exception as e:
    print('Error:', e)

print('\n=== Test 5: Start interview ===')
data = {'mode': 'resume', 'topic': None, 'target_role': 'AI Engineer'}
body2 = json.dumps(data).encode()
req_start = urllib.request.Request(f'{BASE}/api/interview/start', data=body2, method='POST',
                                   headers={'Authorization': f'Bearer {token}',
                                            'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req_start, timeout=30)
    print('Start SUCCESS:', resp.read().decode()[:300])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}:', body[:300])
    if '<html' in body.lower():
        print('*** HTML RESPONSE ***')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
