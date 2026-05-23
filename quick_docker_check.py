import subprocess
result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
if result.returncode == 0:
    print("Docker is READY")
    for line in result.stdout.split('\n')[:20]:
        if line.strip():
            print(line)
else:
    print(f"Docker NOT ready. stderr: {result.stderr[:200]}")
