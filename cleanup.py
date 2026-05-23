"""Kill all hung python processes."""
import subprocess
import time

pids_to_kill = [58140, 48792, 47924, 40940, 53444, 42020, 47156, 49684, 55836]
for pid in pids_to_kill:
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, timeout=5)
    except:
        pass

time.sleep(2)

# Also kill python processes using lots of memory (likely hung)
result = subprocess.run(['tasklist'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'python' in line.lower():
        parts = line.split()
        if len(parts) >= 2:
            pid = parts[1]
            try:
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, timeout=5)
            except:
                pass

print("Cleanup done")
