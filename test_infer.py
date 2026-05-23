import urllib.request
import json
import time

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('Login OK, token:', token[:30])

BASE = 'http://localhost'

def api_post_raw(path, data=None, timeout=5):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f'{BASE}{path}', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {token}',
                                          'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        content_type = resp.headers.get('Content-Type', '')
        body_resp = resp.read().decode()
        print(f'  Status: {resp.status}, CT: {content_type}')
        print(f'  Body: {body_resp[:200]}')
        if 'html' in content_type.lower():
            print('  *** HTML RESPONSE! ***')
        return resp.status, body_resp
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'  HTTP {e.code}: CT={e.headers.get("Content-Type","")}')
        print(f'  Body: {body[:200]}')
        if '<!doctype' in body.lower() or '<html' in body.lower():
            print('  *** HTML RESPONSE! ***')
        return e.code, body
    except Exception as e:
        print(f'  Exception: {type(e).__name__}: {e}')
        return -1, str(e)

print('\n=== Test: infer-target-role (quick 5s timeout) ===')
api_post_raw('/api/profile/infer-target-role', timeout=5)

print('\n=== Test: infer-target-role (long 60s timeout) ===')
api_post_raw('/api/profile/infer-target-role', timeout=60)

print('\n=== Test: upload a real PDF and then infer ===')
# Upload
pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n211\n%%EOF'

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n').encode()
body += pdf_content + f'\r\n--{boundary}--\r\n'.encode()

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
    print('Upload SUCCESS:', resp.read().decode())
except urllib.error.HTTPError as e:
    print(f'Upload HTTP {e.code}:', e.read().decode()[:200])
    if '<html' in e.read().decode().lower():
        print('*** HTML on upload ***')

# Now test infer
print('\n=== Now testing infer-target-role ===')
api_post_raw('/api/profile/infer-target-role', timeout=60)

# Check profile
print('\n=== Test: get profile ===')
req_profile = urllib.request.Request(f'{BASE}/api/profile',
                                    headers={'Authorization': f'Bearer {token}'})
try:
    resp = urllib.request.urlopen(req_profile, timeout=10)
    print('Profile:', resp.read().decode()[:200])
except Exception as e:
    print(f'Profile error: {e}')
