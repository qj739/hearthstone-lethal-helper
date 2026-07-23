#!/usr/bin/env python3
"""英雄已攻击后：恶魔之爪不得再造假挥击误触发审判官跟刀；退货政策可触发球霸亡语。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_23_18_25_26\Power.log"
)


def _replay(target: int) -> GameState:
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < target)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    gs.in_game = True
    return gs


def test_return_policy_registered():
    defn = get_board_spell_def("MIS_102")
    assert defn is not None
    assert defn.name == "退货政策"
    print("OK MIS_102 registered")


def test_no_inquisitor_lethal_after_hero_exhausted():
    """英雄已攻击后：不得再提示审判官+恶魔之爪斩杀。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(14280)
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _t, _s, lethal = lc.calculate_lethal_potential()
    note = (lc.overlay_spell_note() or "") + " ".join(lc.overlay_combo_display_lines())
    assert "伊利达雷审判官" not in note, note
    assert not lethal, (face, note)
    assert face < 7, face
    print("OK no false inquisitor after hero attack", face)


def test_return_policy_lethal_from_log():
    """退货政策触发球霸亡语 3 伤：对手 2 血应斩。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(14880)
    hand = [c.card_id for c in gs.get_hand(gs.local_player_id)]
    assert "MIS_102" in hand, hand
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _t, _s, lethal = lc.calculate_lethal_potential()
    assert face >= 2, (face, lc.overlay_spell_note(), lc.overlay_combo_display_lines())
    assert lethal, (face, lc.overlay_combo_display_lines())
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert "退货政策" in note, note
    print("OK return policy lethal from log", face)


if __name__ == "__main__":
    test_return_policy_registered()
    test_no_inquisitor_lethal_after_hero_exhausted()
    test_return_policy_lethal_from_log()
