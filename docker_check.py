"""Non-blocking Docker check."""
import subprocess
result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=60)
print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print("Docker is READY")
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line and any(k in line for k in ['Version', 'Context', 'Server', 'OS/Arch', 'Kernel', 'Operating']):
            print(line)
else:
    print(f"Docker NOT ready. stderr: {result.stderr[:300]}")
