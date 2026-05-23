"""Wait for Docker and start compose."""
import subprocess
import sys

print("Waiting for Docker daemon...")
for attempt in range(60):
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"Docker ready after {attempt*10} seconds!")
            break
    except subprocess.TimeoutExpired:
        pass
    print(f"  Attempt {attempt+1}/60: Docker not responding, waiting...")
    import time
    time.sleep(10)
else:
    print("Docker did not become ready in 10 minutes")
    sys.exit(1)

print("\nRunning docker compose up --build -d...")
workspace = r'c:\Users\seigi\Desktop\26面试\TechSpar'
result = subprocess.run(
    ['docker', 'compose', 'up', '--build', '-d'],
    cwd=workspace,
    capture_output=True,
    text=True,
    timeout=600
)
print(f"stdout:\n{result.stdout[:3000]}")
print(f"stderr:\n{result.stderr[:1000]}")
print(f"returncode: {result.returncode}")
