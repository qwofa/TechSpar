"""Poll Docker until ready."""
import subprocess
import time

for i in range(90):
    result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Docker ready after {i*2} seconds")
        # Show key info
        lines = result.stdout.split('\n')
        for line in lines:
            if any(k in line for k in ['Version', 'Context', 'Server Version', 'Operating System']):
                print(line)
        break
    print(f"Waiting... ({i*2}s) - {result.stderr[:50] if result.stderr else 'no error'}")
    time.sleep(2)
else:
    print("Docker did not become ready")
    print(result.stderr[:500])
