#!/usr/bin/env python3
"""提取「回合初未斩」胜局：回合初快照 + 本回合操作序列（含投降局）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_user_logs_lethal import (
    analyze_split_file,
    find_kill_turn_main_action,
    parse_to_line,
    scan_winner,
)
from _report_turn_start_no_lethal import snapshot_at

ROOT = Path(r"C:\Users\hp\Desktop\HS\Logs\split_games")

GAMES = [
    ("Hearthstone_2026_06_16_19_52_58", 2),
    ("Hearthstone_2026_06_16_19_52_58", 6),
    ("Hearthstone_2026_06_16_19_52_58", 7),
    ("Hearthstone_2026_06_16_23_48_03", 1),
    ("Hearthstone_2026_06_16_23_48_03", 2),
    ("Hearthstone_2026_06_16_23_48_03", 6),
]

PLAY_GS_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - BLOCK_START BlockType=PLAY Entity=\[entityName=([^ ]+) id=\d+ zone=HAND zonePos=\d+ cardId=([^ ]+) player=(\d+)\]"
)
ATTACK_GS_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - BLOCK_START BlockType=ATTACK Entity=\[entityName=([^ ]+) id=\d+ zone=PLAY zonePos=\d+ cardId=([^ ]+) player=(\d+)\]"
)
DRAW_SHOW_RE = re.compile(
    r"SHOW_ENTITY - Updating Entity=\[entityName=([^\]]*) id=\d+ zone=DECK zonePos=\d+ cardId= player=(\d+)\] CardID=([A-Z0-9_]+)"
)
END_TURN_RE = re.compile(r"GameState\.SendOption\(\) - selectedOption=0 ")
LOCAL_CP_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) -\s+TAG_CHANGE Entity=([^ ]+) tag=CURRENT_PLAYER value=0\b"
)


def turn_window(lines: list[str], local_tag: str, turn_line: int, end_line: int) -> tuple[int, int]:
    """从 MAIN_ACTION 到本回合结束（我方 CURRENT_PLAYER→0 或投降）。"""
    stop = end_line
    for j in range(turn_line, end_line):
        if LOCAL_CP_RE.search(lines[j]) and local_tag in lines[j]:
            stop = j + 1
            break
    return turn_line, stop


def find_draw(lines: list[str], turn_line: int, local_pid: int) -> str:
    for j in range(turn_line, min(turn_line + 120, len(lines))):
        m = DRAW_SHOW_RE.search(lines[j])
        if m and int(m.group(2)) == local_pid:
            name, cid = m.group(1), m.group(3)
            return name if name and not name.startswith("UNKNOWN") else cid
    return "（无/烧牌）"


def find_actions(lines: list[str], start: int, stop: int, local_pid: int) -> list[str]:
    out: list[str] = []
    for j in range(start, stop):
        ln = lines[j]
        m = PLAY_GS_RE.search(ln)
        if m and int(m.group(3)) == local_pid:
            out.append(f"出 {m.group(1)}")
            continue
        m = ATTACK_GS_RE.search(ln)
        if m and int(m.group(3)) == local_pid:
            out.append(f"攻 {m.group(1)}")
    # 去重连续 PowerTaskList 重复
    dedup: list[str] = []
    for a in out:
        if not dedup or dedup[-1] != a:
            dedup.append(a)
    return dedup


def main() -> None:
    for sess, gi in GAMES:
        path = ROOT / sess / f"game_{gi:02d}.log"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        label = f"{path.parent.name}/{path.name}"
        rep = analyze_split_file(path)
        won_idx, _ = scan_winner(lines)
        concede = None
        for i, ln in enumerate(lines, 1):
            if "PLAYSTATE value=CONCEDED" in ln and "GameState.DebugPrintPower" in ln:
                concede = i
                break
        end = concede or won_idx or len(lines)
        turn_line = find_kill_turn_main_action(lines, rep.local_name, end)
        gs = parse_to_line(lines, label, len(lines))
        local_pid = gs.local_player_id or 2
        draw = find_draw(lines, turn_line, local_pid) if turn_line else "?"
        t0, t1 = turn_window(lines, rep.local_name, turn_line, end) if turn_line else (0, 0)
        actions = find_actions(lines, t0, t1, local_pid) if turn_line else []
        snap = snapshot_at(lines, label, turn_line) if turn_line else None

        print("=" * 64)
        print(f"{sess.replace('Hearthstone_','')} · 第{gi}局 · {rep.end_type}")
        print(f"  回合初 L{turn_line}  本回合结束 L{t1}  投降 L{concede}")
        print(f"  抽牌: {draw}")
        if snap:
            print(f"  对手 {snap['opp_hp']}  法力 {snap['mana']}")
            print(f"  我方场面 {snap['board']}")
            print(f"  对方场面 {snap['opp_board']}")
            print(f"  手牌 {snap['hand']}")
            print(f"  overlay={snap['overlay']}  lethal={snap['lethal']}")
            print(f"  引擎 {snap['play_line']}")
        acts = " → ".join(actions) if actions else "（仅结束回合/无出牌）"
        print(f"  本回合操作: {acts}")
        print()


if __name__ == "__main__":
    main()
