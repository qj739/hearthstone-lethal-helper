#!/usr/bin/env python3
"""深挖 23_48 投降局：投降发生在哪方回合 + 我方最后一回合出牌。"""
from __future__ import annotations

import re
from pathlib import Path

LOCAL = "能干的英雄#510408"
ROOT = Path(r"C:\Users\hp\Desktop\HS\Logs\split_games\Hearthstone_2026_06_16_23_48_03")

PLAY = re.compile(
    r"GameState\.DebugPrintPower\(\) - BLOCK_START BlockType=(PLAY|ATTACK) "
    r"Entity=\[entityName=([^ ]+) id=\d+ zone=\w+ zonePos=\d+ cardId=([^ ]+) player=(\d+)\]"
)
CP0 = re.compile(
    rf"GameState\.DebugPrintPower\(\) -\s+TAG_CHANGE Entity={re.escape(LOCAL)} tag=CURRENT_PLAYER value=0\b"
)
CP1 = re.compile(
    rf"GameState\.DebugPrintPower\(\) -\s+TAG_CHANGE Entity={re.escape(LOCAL)} tag=CURRENT_PLAYER value=1\b"
)
CONCEDE = re.compile(
    r"GameState\.DebugPrintPower\(\) - TAG_CHANGE Entity=([^ ]+) tag=PLAYSTATE value=CONCEDED"
)


def analyze(path: Path, gi: int) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    concede_i = opp = None
    for i, ln in enumerate(lines):
        m = CONCEDE.search(ln)
        if m:
            concede_i = i + 1
            opp = m.group(1)
            break
    if concede_i is None:
        print(f"game_{gi:02d}: no concede")
        return

    last_cp1 = last_cp0 = None
    for i in range(concede_i):
        if CP1.search(lines[i]):
            last_cp1 = i + 1
        if CP0.search(lines[i]):
            last_cp0 = i + 1
    if last_cp1 and (not last_cp0 or last_cp1 > last_cp0):
        turn_owner = "我方回合"
    else:
        turn_owner = "对方回合"

    turns: list[tuple[int, int]] = []
    cur = None
    for i, ln in enumerate(lines[:concede_i]):
        if CP1.search(ln):
            cur = i + 1
        if CP0.search(ln) and cur:
            turns.append((cur, i + 1))
            cur = None

    # 若投降在我方回合，最后一回合可能未结束
    if turn_owner == "我方回合" and last_cp1:
        t0, t1 = last_cp1, concede_i
        label = "投降所在回合(我方，未结束)"
    else:
        t0, t1 = turns[-1] if turns else (0, 0)
        label = "我方最后一完整回合"

    pid = "2"
    acts: list[str] = []
    for j in range(t0, t1):
        m = PLAY.search(lines[j])
        if m and m.group(4) == pid:
            kind = "出" if m.group(1) == "PLAY" else "攻"
            acts.append(f"{kind}{m.group(2)}({m.group(3)})")

    print(f"=== game_{gi:02d}  投降 L{concede_i}  对手={opp} ===")
    print(f"  投降时回合: {turn_owner}")
    print(f"  {label}: L{t0}-L{t1}")
    print(f"  我方操作: {' -> '.join(acts) if acts else '(无)'}")
    print()


def main() -> None:
    for gi in (1, 2, 6):
        analyze(ROOT / f"game_{gi:02d}.log", gi)


if __name__ == "__main__":
    main()
