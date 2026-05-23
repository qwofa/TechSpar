"""Test Docker after cleaning up hung processes."""
import subprocess

result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=20)
print(f"Return: {result.returncode}")
if result.returncode == 0:
    print("Docker is READY!")
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line and any(k in line for k in ['Version', 'Context', 'Server Version', 'Operating', 'Kernel']):
            print(f"  {line}")
else:
    print(f"STDERR: {result.stderr[:300]}")
