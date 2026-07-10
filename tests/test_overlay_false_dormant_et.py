#!/usr/bin/env python3
"""法术解场后随从多打脸，不应误显示「回」分项。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_26_14_30_12\Power.log"
)
LINE = 277767


def _replay(line: int) -> LethalChecker:
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    for i, ln in enumerate(lines):
        if i >= line:
            break
        with contextlib.redirect_stdout(io.StringIO()):
            p.process_line(ln.rstrip("\n\r"))
    gs.in_game = True
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    return lc


def test_spell_clear_no_false_dormant_et():
    """双活体根须衍生物+活体根须/潮起潮落：无休眠回合结束，不应有回2。"""
    if not LOG.is_file():
        print("SKIP no log", LOG)
        return
    lc = _replay(LINE)
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()
    dormant = lc.overlay_end_turn_face_for_display()
    pure, minion, _, spell, hp = lc.overlay_board_breakdown()
    buff = lc.overlay_hero_buff_face()

    assert dormant == 0, f"no dormant ET on board, got {dormant}"
    assert display == lethal, (
        f"display {display} should match lethal {lethal} when no dormant/charge"
    )
    assert pure < minion, "spells should raise minion face above pure immediate"
    assert display == minion + spell + hp + buff, (
        f"display {display} != minion+spell+hp+buff"
    )
    print("OK no false dormant et", display, "pure", pure, "minion", minion)


def test_large_board_no_end_turn_false_hui():
    """多随从无回合结束源：不应误显示回4/回5。"""
    if not LOG.is_file():
        print("SKIP no log", LOG)
        return
    lc = _replay(299317)
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()
    et = lc.overlay_end_turn_face_for_display()
    pure, minion, _, spell, hp = lc.overlay_board_breakdown()
    buff = lc.overlay_hero_buff_face()
    bc = lc.overlay_battlecry_face()

    assert et == 0, f"no end-turn on board, got et={et}"
    assert display == lethal == minion + spell + hp + buff + bc
    assert pure == 21 and minion == 26
    print("OK large board no false hui", display, "et", et)


if __name__ == "__main__":
    test_spell_clear_no_false_dormant_et()
    test_large_board_no_end_turn_false_hui()
    print("all passed")
