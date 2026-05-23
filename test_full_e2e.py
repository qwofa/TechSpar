"""Full end-to-end test of the resume upload and interview flow."""
import urllib.request
import json
import os

BASE = 'http://127.0.0.1:8000'
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request(f'{BASE}/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('1. Login OK')

# Check resume status
req_status = urllib.request.Request(
    f'{BASE}/api/resume/status',
    headers={'Authorization': f'Bearer {token}'}
)
resp = urllib.request.urlopen(req_status, timeout=10)
status = json.loads(resp.read().decode())
print(f'2. Resume status: {status}')

# Test infer-target-role
print('\n3. Testing infer-target-role...')
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
    print(f'   SUCCESS: {result}')
    target_role = result.get('target_role', '')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'   HTTP {e.code}: {body}')
    target_role = ''

# Test start interview
if target_role:
    print(f'\n4. Testing start interview (role: {target_role})...')
    start_data = {
        'mode': 'resume',
        'topic': None,
        'target_role': target_role
    }
    req_start = urllib.request.Request(
        f'{BASE}/api/interview/start',
        data=json.dumps(start_data).encode(),
        method='POST',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    try:
        resp = urllib.request.urlopen(req_start, timeout=60)
        result = json.loads(resp.read().decode())
        print(f'   SUCCESS! Session ID: {result.get("session_id")}')
        print(f'   Message preview: {result.get("message", "")[:100]}...')
        session_id = result.get('session_id')

        # Test chat
        if session_id:
            print(f'\n5. Testing chat/send-message...')
            chat_data = {
                'session_id': session_id,
                'message': '你好，我是候选人，很高兴参加这次面试。'
            }
            req_chat = urllib.request.Request(
                f'{BASE}/api/interview/chat',
                data=json.dumps(chat_data).encode(),
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            resp = urllib.request.urlopen(req_chat, timeout=60)
            chat_result = json.loads(resp.read().decode())
            print(f'   Message: {chat_result.get("message", "")[:150]}...')
            print(f'   Is finished: {chat_result.get("is_finished")}')

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'   HTTP {e.code}: {body[:500]}')
    except Exception as e:
        print(f'   Error: {type(e).__name__}: {e}')

print('\n=== All tests completed ===')
