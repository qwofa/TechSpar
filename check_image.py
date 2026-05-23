import json
import sys
d = json.load(sys.stdin)
print("Image:", d[0]["Config"]["Image"])
print("Created:", d[0]["Created"])
