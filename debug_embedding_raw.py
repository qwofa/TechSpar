"""Debug: print the raw API response from SiliconFlow to understand its shape."""
import requests

url = "https://api.siliconflow.cn/v1/embeddings"
headers = {
    "Authorization": "Bearer sk-hspbmmdlwdsafyzxwjqcwccgpbtdceuqfighoxtjhayyjuuj",
    "Content-Type": "application/json",
}
payload = {
    "model": "BAAI/bge-large-zh-v1.5",
    "input": "Hello world",
}

resp = requests.post(url, headers=headers, json=payload, timeout=15)
print("Status code:", resp.status_code)
print("Response text:", resp.text[:2000])
