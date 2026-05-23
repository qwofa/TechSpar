"""Start Docker Compose from Windows."""
import subprocess
import sys
import time

workspace = r'c:\Users\seigi\Desktop\26面试\TechSpar'

print("=== Step 1: Check Docker ===")
result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    print("Docker is ready!")
else:
    print(f"Docker not ready: {result.stderr[:200]}")
    sys.exit(1)

print("\n=== Step 2: Docker Compose Up ===")
result = subprocess.run(
    ['docker', 'compose', 'up', '--build', '-d'],
    cwd=workspace,
    capture_output=True,
    text=True,
    timeout=600
)
print(f"stdout:\n{result.stdout}")
print(f"stderr:\n{result.stderr}")
print(f"returncode: {result.returncode}")

if result.returncode == 0:
    print("\n=== Step 3: Check Containers ===")
    subprocess.run(['docker', 'compose', 'ps'], cwd=workspace)
    
    print("\n=== Step 4: Test Backend ===")
    subprocess.run(['curl', 'http://localhost:8000/api/auth/login', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', '{"email":"admin@techspar.local","password":"admin123"}'])
    
    print("\n=== Step 5: Test Frontend ===")
    subprocess.run(['curl', 'http://localhost/', '-I'])
