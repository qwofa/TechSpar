"""Try Docker through WSL2."""
import subprocess

print("=== WSL docker info ===")
result = subprocess.run(
    ['wsl', '-d', 'docker-desktop', '--', 'docker', 'info'],
    capture_output=True,
    text=True,
    timeout=30
)
print(f"Return: {result.returncode}")
if result.returncode == 0:
    print("SUCCESS via WSL!")
    print(result.stdout[:500])
else:
    print(f"STDERR: {result.stderr[:300]}")

print("\n=== WSL docker ps ===")
result = subprocess.run(
    ['wsl', '-d', 'docker-desktop', '--', 'docker', 'ps'],
    capture_output=True,
    text=True,
    timeout=30
)
print(f"Return: {result.returncode}")
print(f"STDOUT: {result.stdout[:200]}")
print(f"STDERR: {result.stderr[:200]}")
