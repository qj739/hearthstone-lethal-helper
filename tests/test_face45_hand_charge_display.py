#!/usr/bin/env python3
"""场攻主数字不含手牌冲锋；冲锋单独分项。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_25_15_28_30\Power.log"
)
LINE = 55400


def _replay(line: int) -> tuple[GameState, LethalChecker]:
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "DebugPrintPower" in l
    ]
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    for i in range(starts[3], line):
        ln = lines[i].rstrip("\n\r")
        if ln:
            with contextlib.redirect_stdout(io.StringIO()):
                p.process_line(ln)
    gs.in_game = True
    return gs, LethalChecker(gs)


def test_face45_board_only_display():
    gs, lc = _replay(LINE)
    lc.overlay_board_face_damage()
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()
    hand_chg = lc.overlay_hand_charge_face()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()

    assert display == 40, f"board display should be 40, got {display}"
    assert lethal == 45, f"lethal should include hand charge, got {lethal}"
    assert hand_chg == 5, f"hand charge face should be 5, got {hand_chg}"
    assert pure == 40, f"pure board {pure}"
    assert minion == 44, f"minion breakdown with charge {minion}"
    assert weapon == 1
    print("OK face45 display", display, "lethal", lethal, "冲", hand_chg)


if __name__ == "__main__":
    if not LOG.is_file():
        print("SKIP no log", LOG)
    else:
        test_face45_board_only_display()
        print("all passed")
