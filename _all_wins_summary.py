#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analyze_user_logs_lethal import analyze_split_file
from verify_all_power_logs import discover_split_games

files = discover_split_games()
print("session,game,end,turn_ov,turn_lethal,pre_ov,pre_lethal")
for p in files:
    r = analyze_split_file(p)
    if not r.local_won:
        continue
    ts = r.kill_turn_start
    pk = r.pre_kill
    sess = p.parent.name.replace("Hearthstone_", "")
    print(
        f"{sess},g{r.game_index},{r.end_type},"
        f"{ts.overlay if ts else '-'},"
        f"{'Y' if ts and ts.lethal else ('N' if ts else '-')},"
        f"{pk.overlay if pk else '-'},"
        f"{'Y' if pk and pk.lethal else ('N' if pk else '-')}"
    )
