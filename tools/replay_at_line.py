#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import _std_attack


def main():
    log = sys.argv[1]
    target = int(sys.argv[2])
    gs = GameState()
    p = PowerLogParser(log, gs)
    with open(log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    start = starts[-1] if starts else 0
    if (target - 1) <= start and len(starts) > 1:
        start = starts[0]
    for i in range(start, target):
        p.process_line(lines[i])
    gs.in_game = True
    lc = LethalChecker(gs)
    pid = gs.local_player_id or 1
    print("line", target, "start", start + 1, "local", pid, "in_game", gs.in_game, "entities", len(gs.entities))
    print("board_slots", gs.board_slots.get(pid))
    for m in gs.get_board(pid):
        t479 = m.tags.get("479")
        tatk = m.tags.get("ATK")
        print(
            f"  {m.card_id} e{m.entity_id} atk={m.atk} std={_std_attack(m)}"
            f" 479={t479} ATK={tatk} can={m.can_attack}"
            f" exhausted={m.tags.get('EXHAUSTED')} ntip={m.tags.get('NUM_TURNS_IN_PLAY')}"
        )
    overlay = lc.overlay_board_face_damage()
    print("overlay", overlay, lc.overlay_board_breakdown(), "hb", lc.overlay_hero_buff_face())
    opp = gs.get_hero(2)
    if opp:
        print("opp hp", opp.current_health, "armor", opp.tags.get("ARMOR"), "dmg", opp.damage)


if __name__ == "__main__":
    main()
