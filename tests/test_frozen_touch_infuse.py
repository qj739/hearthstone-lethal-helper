#!/usr/bin/env python3
"""冰冻之触 REV_601：注能后打出回手，同回合可再打一次（共 6 伤）。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.spell_board import (
    apply_spell_sequence,
    get_board_spell_def,
    spell_effective_cost,
)
from hdt_python.spell_p0_direct import _apply_frozen_touch, _frozen_touch_infused


def _hand_spell(gs, eid, pid, card_id, *, cost=2, powered=False):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    if powered:
        s.tags["POWERED_UP"] = 1
    return s


def test_infused_returns_to_hand():
    card = type("C", (), {"card_id": "REV_601t", "tags": {}})()
    res = _apply_frozen_touch([], [], mult=1, enemy_shield=False, card=card)
    assert res.add_hand_spell_id == "REV_601"
    assert res.direct_face_damage == 3


def test_uninfused_no_return():
    card = type("C", (), {"card_id": "REV_601", "tags": {}})()
    res = _apply_frozen_touch([], [], mult=1, enemy_shield=False, card=card)
    assert res.add_hand_spell_id is None


def test_powered_up_rev601_counts_as_infused():
    card = type("C", (), {"card_id": "REV_601", "tags": {"POWERED_UP": 1}})()
    assert _frozen_touch_infused(card)
    res = _apply_frozen_touch([], [], mult=1, enemy_shield=False, card=card)
    assert res.add_hand_spell_id == "REV_601"


def test_double_touch_same_turn_with_mana():
    """4 费：注能之触 3 伤 + 回手再 3 伤 = 6。"""
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "REV_601t")
    defn = get_board_spell_def("REV_601t")
    seq = [(defn, 2, card)]
    res = apply_spell_sequence(
        [], [], seq, gs=gs, player_id=1, mana_budget=4,
    )
    assert res.direct_face_damage == 6


def test_double_touch_skipped_without_mana():
    """2 费：只能打一次 3 伤。"""
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "REV_601t")
    defn = get_board_spell_def("REV_601t")
    seq = [(defn, 2, card)]
    res = apply_spell_sequence(
        [], [], seq, gs=gs, player_id=1, mana_budget=2,
    )
    assert res.direct_face_damage == 3


def test_infused_play_from_power_log():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_09_16_03_26\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 222743
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[-1])
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    touch = next(c for c in gs.get_hand(2) if c.card_id == "REV_601t")
    assert _frozen_touch_infused(touch)
    assert spell_effective_cost(touch, gs, 2) == 2


if __name__ == "__main__":
    test_infused_returns_to_hand()
    test_uninfused_no_return()
    test_powered_up_rev601_counts_as_infused()
    test_double_touch_same_turn_with_mana()
    test_double_touch_skipped_without_mana()
    test_infused_play_from_power_log()
    print("OK frozen touch infuse")
