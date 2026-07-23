#!/usr/bin/env python3
"""审判 JAIL_326：选择友方随从，将双方其他随从属性变为与其相同。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_23_11_52_47\Power.log"
)
# 打出审判前（象牙骑士 6 攻模板）
TARGET = 708600


def test_registered():
    defn = get_board_spell_def("JAIL_326")
    assert defn is not None
    assert defn.name == "审判"
    print("OK JAIL_326 registered")


def test_judgment_copies_stats_to_other_minions():
    """友方 6/2 模板 → 其他友方/敌方变为 6/2。"""
    defn = get_board_spell_def("JAIL_326")
    fighters = [
        {"kind": "minion", "entity_id": 8, "atk": 6, "health": 2,
         "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 79, "atk": 1, "health": 1,
         "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 27, "atk": 2, "health": 3,
         "attacks_left": 1, "can_face": True},
    ]
    taunts = [
        {"kind": "minion", "entity_id": 38, "atk": 3, "health": 4},
    ]
    apply_spell_sequence(taunts, fighters, [(defn, 6, None)])
    tmpl = next(f for f in fighters if f["entity_id"] == 8)
    assert tmpl["atk"] == 6 and tmpl["health"] == 2
    for eid in (79, 27):
        u = next(f for f in fighters if f["entity_id"] == eid)
        assert u["atk"] == 6 and u["health"] == 2, u
    assert taunts[0]["atk"] == 6 and taunts[0]["health"] == 2
    print("OK judgment copies stats")


def test_judgment_lethal_from_power_log():
    """回放：审判复制象牙骑士属性后应识别斩杀（对手 14 血）。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < TARGET)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, TARGET):
            p.process_line(lines[i].rstrip())
    hand_ids = [c.card_id for c in gs.get_hand(gs.local_player_id)]
    assert "JAIL_326" in hand_ids, hand_ids
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _total, _src, lethal = lc.calculate_lethal_potential()
    assert face >= 14, (face, lc.overlay_spell_note(), lc.overlay_combo_display_lines())
    assert lethal, (face, lc.overlay_combo_display_lines())
    note = " ".join(lc.overlay_combo_display_lines())
    assert "审判" in note or "审判" in (lc.overlay_spell_note() or ""), note
    print("OK judgment lethal from log", face)


if __name__ == "__main__":
    test_registered()
    test_judgment_copies_stats_to_other_minions()
    test_judgment_lethal_from_power_log()
