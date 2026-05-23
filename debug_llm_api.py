"""Debug: test the LLM API endpoint directly to see its raw response shape."""
import requests

url = "https://cn.wzjself.org/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-live-652f527f5245cf54495a8d12d7c7f298eefa",
    "Content-Type": "application/json",
}
payload = {
    "model": "gpt-5.5",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "stream": False,
}

print("Sending request to LLM API...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
    print(f"Body (first 2000 chars): {resp.text[:2000]}")
except Exception as exc:
    print(f"Request failed: {exc}")
