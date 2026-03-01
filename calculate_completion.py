import re

total = 0
done = 0
in_progress = 0
pending = 0
other = 0

with open('BOARD.md', 'r') as f:
    for line in f:
        if line.strip().startswith('| P'):
            total += 1
            if '✅' in line or 'DONE' in line or 'FLESHED OUT' in line:
                done += 1
            elif '⬛' in line or 'In Progress' in line or 'COMPLETING' in line:
                in_progress += 1
            elif '⬜' in line or 'PENDING' in line:
                pending += 1
            else:
                other += 1

if total > 0:
    pct = (done / total) * 100
    print(f"Total Specs: {total}")
    print(f"✅ Completed (Fleshed Out / Done): {done}")
    print(f"⬛ In Progress (Pass 2): {in_progress}")
    print(f"⬜ Pending Skeleton (Pass 1): {pending}")
    print(f"Other: {other}")
    print(f"\nOverall Completion: {pct:.2f}%")
