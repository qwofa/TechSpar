"""Check Docker Desktop status and wait."""
import subprocess
import time
import os

print("=== Docker Desktop Process Check ===")
# Check if Docker Desktop process is running
procs = subprocess.run(['tasklist'], capture_output=True, text=True)
for line in procs.stdout.split('\n'):
    if 'docker' in line.lower() or 'com.docker' in line.lower():
        print(line)

print("\n=== Docker Daemon Status ===")
result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
if result.returncode == 0:
    print("Docker is READY!")
    for line in result.stdout.split('\n')[:20]:
        print(line)
else:
    print(f"Docker not ready: {result.stderr[:200] if result.stderr else 'no stderr'}")
    print("Docker Desktop may still be starting up...")

print("\n=== Polling every 5 seconds, max 3 minutes ===")
for i in range(36):
    time.sleep(5)
    result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Docker ready after {(i+1)*5} seconds!")
        for line in result.stdout.split('\n')[:15]:
            print(line)
        break
    print(f"  {(i+1)*5}s: still waiting... ({result.stderr[:80] if result.stderr else 'no error'})")
else:
    print("Docker did not become ready in 3 minutes")
