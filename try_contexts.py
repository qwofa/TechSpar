"""Try different Docker contexts."""
import subprocess

print("=== Try default context ===")
try:
    result = subprocess.run(['docker', '--context', 'default', 'info'], capture_output=True, text=True, timeout=15)
    print(f"Return: {result.returncode}")
    if result.returncode == 0:
        print("SUCCESS!")
        for line in result.stdout.split('\n')[:15]:
            line = line.strip()
            if line:
                print(f"  {line}")
    else:
        print(f"STDERR: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("TIMEOUT")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Try desktop-linux context ===")
try:
    result = subprocess.run(['docker', '--context', 'desktop-linux', 'info'], capture_output=True, text=True, timeout=15)
    print(f"Return: {result.returncode}")
    if result.returncode == 0:
        print("SUCCESS!")
        for line in result.stdout.split('\n')[:15]:
            line = line.strip()
            if line:
                print(f"  {line}")
    else:
        print(f"STDERR: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("TIMEOUT")
except Exception as e:
    print(f"Error: {e}")
