#!/usr/bin/env python3
"""回放 Power.log，在关键行输出场攻与场面随从攻击力（含 tags 479/ATK）。"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import _std_attack, effective_attack_from_tags, entity_zone


def replay(log_path: str, sample_every: int = 50):
    gs = GameState()
    p = PowerLogParser(log_path, gs)
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    start = 0
    for i, line in enumerate(lines):
        if "CREATE_GAME" in line:
            start = i
    lc = LethalChecker(gs)
    pid = None
    for i in range(start, len(lines)):
        p.parse_line(lines[i])
        if gs.local_player_id:
            pid = gs.local_player_id
        if not gs.in_game or pid is None:
            continue
        if (i - start) % sample_every != 0 and i != len(lines) - 1:
            continue
        overlay = lc.overlay_board_face_damage()
        bd = lc.overlay_board_breakdown()
        hb = lc.overlay_hero_buff_face()
        board = gs.get_board(pid)
        if not board and overlay == 0:
            continue
        parts = []
        for m in board:
            atk = _std_attack(m)
            t479 = m.tags.get("479")
            tatk = m.tags.get("ATK")
            can = m.can_attack
            parts.append(
                f"{m.card_id}(e{m.entity_id}) std={atk} ATK={tatk} 479={t479} can={can}"
            )
        print(f"--- line {i+1} overlay={overlay} bd={bd} hb={hb} ---")
        print("  " + " | ".join(parts) if parts else "  (empty board)")


if __name__ == "__main__":
    log = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_20_16_32_17\Power.log"
    replay(log, int(sys.argv[2]) if len(sys.argv) > 2 else 80)
