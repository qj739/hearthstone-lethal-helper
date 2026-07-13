import sys
for line in sys.stdin:
    if "Co-authored-by: Cursor" in line:
        continue
    sys.stdout.write(line)
