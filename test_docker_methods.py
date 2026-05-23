"""Test multiple ways to access Docker."""
import subprocess
import time

methods = [
    ("docker info (direct)", ['docker', 'info']),
    ("docker info (cmd)", ['cmd', '/c', 'docker', 'info']),
]

for name, cmd in methods:
    print(f"\n=== {name} ===")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"Return: {result.returncode}")
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(k in line for k in ['Version', 'Context', 'Server Version', 'Operating', 'Kernel']):
                    print(f"  {line}")
            print("  SUCCESS!")
        else:
            print(f"  STDERR: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 15s")
    except Exception as e:
        print(f"  ERROR: {e}")
