import urllib.request
import json

# Login
login_data = json.dumps({'email': 'admin@techspar.local', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost/api/auth/login', data=login_data,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['token']
print('Login OK')

# Create a minimal valid PDF
pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n211\n%%EOF'

# Build multipart form data
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body_parts = [
    f'--{boundary}\r\n'.encode(),
    b'Content-Disposition: form-data; name="file"; filename="@my.pdf"\r\n',
    b'Content-Type: application/pdf\r\n',
    b'\r\n',
    pdf_content,
    f'\r\n--{boundary}--\r\n'.encode()
]
body = b''.join(body_parts)

req_upload = urllib.request.Request(
    'http://localhost/api/resume/upload',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }
)

try:
    resp_upload = urllib.request.urlopen(req_upload, timeout=30)
    result = resp_upload.read().decode()
    print('Upload SUCCESS:', result)
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    body = e.read().decode()
    print('Body (first 500 chars):', body[:500])
    # Check if it's HTML
    if '<html' in body.lower() or '<!doctype' in body.lower():
        print('*** HTML response detected! ***')
except Exception as e:
    print('Error:', type(e).__name__, str(e))
