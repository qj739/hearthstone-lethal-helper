#!/usr/bin/env python3
"""阿达尔之手 CORE_BT_292：友方 +2/+1，应与光速抢购等 buff 组合计入斩杀。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_23_11_52_47\Power.log"
)
# 打出阿达尔之手前（象牙骑士 8 攻，对手 18 血 + 4 血嘲讽）
TARGET_BEFORE_ADAL = 746183


def test_registered():
    for cid in ("CORE_BT_292", "BT_292"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name == "阿达尔之手"
        assert defn.base_cost == 2
    print("OK CORE_BT_292 registered")


def test_hand_of_adal_buffs_plus_2_1():
    defn = get_board_spell_def("CORE_BT_292")
    fighters = [
        {
            "kind": "minion",
            "entity_id": 52,
            "atk": 8,
            "health": 2,
            "attacks_left": 1,
            "can_face": True,
        },
    ]
    apply_spell_sequence([], fighters, [(defn, 2, None)])
    assert fighters[0]["atk"] == 10
    assert fighters[0]["health"] == 3
    print("OK hand of adal +2/+1")


def test_hand_of_adal_plus_flash_sale_lethal_from_log():
    """回放：阿达尔之手(+2象牙) + 光速抢购(+1全场) → 清 4 嘲后刚好 18 斩。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < TARGET_BEFORE_ADAL)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, TARGET_BEFORE_ADAL):
            p.process_line(lines[i].rstrip())
    gs.in_game = True
    hand_ids = [c.card_id for c in gs.get_hand(gs.local_player_id)]
    assert "CORE_BT_292" in hand_ids, hand_ids
    assert "TOY_716" in hand_ids, hand_ids

    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _total, _src, lethal = lc.calculate_lethal_potential()
    assert face >= 18, (face, lc.overlay_spell_note(), lc.overlay_combo_display_lines())
    assert lethal, (face, lc.overlay_combo_display_lines())
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert "阿达尔之手" in note, note
    assert "光速抢购" in note, note
    print("OK hand of adal + flash sale lethal from log", face)


if __name__ == "__main__":
    test_registered()
    test_hand_of_adal_buffs_plus_2_1()
    test_hand_of_adal_plus_flash_sale_lethal_from_log()
