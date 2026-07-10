#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _report_turn_start_no_lethal import snapshot_at, engine_play_line

path = Path(r"C:\Users\hp\Desktop\HS\Logs\split_games\Hearthstone_2026_06_16_23_48_03\game_01.log")
lines = path.read_text(encoding="utf-8").splitlines()
label = "game_01"

checkpoints = [
    ("回合初 MAIN_ACTION", 23411),
    ("英雄攻后/变形完成", 25095),
    ("女猎手出完后", 25340),
    ("赎罪教堂后/投降前", 25555),
]

for name, ln in checkpoints:
    s = snapshot_at(lines, label, ln)
    print(f"=== {name} L{ln} ===")
    print(f"  对手: {s['opp_hp']}  法力: {s['mana']}")
    print(f"  我方场面: {s['board']}")
    print(f"  对方场面: {s['opp_board']}")
    print(f"  overlay={s['overlay']}  lethal={s['lethal']}  纯随从打脸={s['minion_only']}")
    print(f"  推荐: {s['play_line']}")
    print()
