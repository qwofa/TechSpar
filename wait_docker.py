"""Wait for Docker to be ready."""
import subprocess
import time

print("Waiting for Docker Desktop to start...")
for i in range(60):
    result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Docker is ready! (took {i*2} seconds)")
        break
    time.sleep(2)
else:
    print("Docker did not become ready in 120 seconds")

# Show docker info
result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
if result.returncode == 0:
    lines = result.stdout.split('\n')
    for line in lines[:15]:
        print(line)
