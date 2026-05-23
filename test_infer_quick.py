import urllib.request
import json
import time

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']

# Test infer with short timeout
print('Testing infer-target-role with 5s timeout...')
req2 = urllib.request.Request('http://localhost/api/profile/infer-target-role', data=b'{}', method='POST',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})

start = time.time()
try:
    resp2 = urllib.request.urlopen(req2, timeout=5)
    elapsed = time.time() - start
    print(f'Response in {elapsed:.1f}s - Status: {resp2.status}')
    body = resp2.read().decode()
    print(f'Body: {body[:500]}')
    if '<html' in body.lower():
        print('*** HTML RESPONSE! ***')
except Exception as e:
    elapsed = time.time() - start
    print(f'Exception after {elapsed:.1f}s: {type(e).__name__}: {e}')
