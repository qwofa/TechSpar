"""Wait for Docker Desktop to be ready."""
import subprocess
import time

print("Waiting for Docker Desktop...")
for i in range(30):
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"Docker ready after {i*10} seconds!")
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and any(k in line for k in ['Version', 'Server Version', 'Operating', 'Kernel', 'Context']):
                    print(f"  {line}")
            break
    except subprocess.TimeoutExpired:
        pass
    print(f"  {i+1}/30: waiting...")
    time.sleep(10)
else:
    print("Docker did not become ready in 5 minutes")
    # Try one more time to show error
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=30)
        print(f"Final attempt returncode: {result.returncode}")
        print(f"STDERR: {result.stderr[:500]}")
    except Exception as e:
        print(f"Final error: {e}")
