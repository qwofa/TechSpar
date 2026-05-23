"""Fast Docker Compose check and startup."""
import subprocess

result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
if result.returncode != 0:
    print("Docker not ready")
    exit(1)
print("Docker ready")
