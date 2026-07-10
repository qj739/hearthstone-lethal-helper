#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analyze_user_logs_lethal import analyze_split_file

roots = [
    Path(__file__).parent / "Logs" / "split_games",
    Path(r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"),
]
seen = set()
rows = []
for root in roots:
    if not root.is_dir():
        continue
    for p in sorted(root.glob("*/game_*.log")):
        key = (p.parent.name, p.name)
        if key in seen:
            continue
        seen.add(key)
        r = analyze_split_file(p)
        if not r.local_won:
            continue
        ts = r.kill_turn_start
        pk = r.pre_kill
        sess = p.parent.name.replace("Hearthstone_", "")
        rows.append((sess, r.game_index, r.end_type, ts, pk, str(p)))

print("ALL LOCAL WINS (deduped)")
print("session,game,end,turn_ov,turn_lethal,pre_ov,pre_lethal")
for sess, gi, end, ts, pk, _ in rows:
    print(
        f"{sess},g{gi},{end},"
        f"{ts.overlay if ts else '-'},"
        f"{'Y' if ts and ts.lethal else ('N' if ts else '-')},"
        f"{pk.overlay if pk else '-'},"
        f"{'Y' if pk and pk.lethal else ('N' if pk else '-')}"
    )

concede_miss = [
    r for r in rows
    if r[2] == "对手投降"
    and ((r[3] and not r[3].lethal) or (r[4] and not r[4].lethal))
]
print(f"\nCONCEDE + NO LETHAL: {len(concede_miss)}")
