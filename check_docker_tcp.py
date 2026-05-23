"""Check Docker TCP port and try alternative access."""
import subprocess
import socket

# Check common Docker ports
ports = [2375, 2376, 23750, 23751, 23752]
for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            print(f"Port {port}: OPEN")
        else:
            print(f"Port {port}: closed ({result})")
    except Exception as e:
        print(f"Port {port}: error ({e})")

# Try to get docker context
print("\n=== Docker Contexts ===")
try:
    result = subprocess.run(['docker', 'context', 'ls'], capture_output=True, text=True, timeout=5)
    print(result.stdout)
except Exception as e:
    print(f"Error: {e}")

# Check if docker CLI can at least show version
print("\n=== Docker Version ===")
try:
    result = subprocess.run(['docker', 'version'], capture_output=True, text=True, timeout=10)
    print(f"Return: {result.returncode}")
    if result.returncode == 0:
        print(result.stdout[:500])
    else:
        print(f"STDERR: {result.stderr[:200]}")
except Exception as e:
    print(f"Error: {e}")
