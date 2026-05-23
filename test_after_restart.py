"""Test API after fresh restart."""
import urllib.request
import json
import time

time.sleep(3)

BASE = 'http://127.0.0.1:8000'
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request(f'{BASE}/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('Login OK')

print('\nTesting infer-target-role (60s timeout)...')
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
    resp = urllib.request.urlopen(req_infer, timeout=60)
    result = json.loads(resp.read().decode())
    print(f'Infer SUCCESS: {result}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP {e.code}: {body[:500]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
