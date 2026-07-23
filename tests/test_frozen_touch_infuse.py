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


def test_pack_infused_touch_counts_bounce():
    """无嘲讽直伤前缀：注能之触应计 3+3=6，并占用 4 费。"""
    from hdt_python.spell_board import (
        pack_no_taunt_direct_face_spells,
        get_board_spell_def,
        partition_hand_spells_by_tier,
    )
    from hdt_python.battlecry_board import hand_all_board_plays

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    touch = _hand_spell(gs, 40, 1, "REV_601t")
    hand = [(touch, get_board_spell_def("REV_601t"), 2)]
    steps, face, mana, raw = pack_no_taunt_direct_face_spells(
        hand, 4, gs=gs, player_id=1,
    )
    assert face == 6, face
    assert raw == 6, raw
    assert mana == 4, mana
    assert len(steps) == 1


def test_log_infused_touch_lethal_before_play():
    """日志回放：15 血 + 场 9 + 注能之触双次 6 (+火冲) 应斩。"""
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_22_12_18_28\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    from hdt_python.lethal_checker import LethalChecker

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 1097000
    starts = [
        i for i, l in enumerate(lines[:target])
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = starts[-1]
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            if lines[i].strip():
                p.process_line(lines[i].rstrip())
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    touch = next(c for c in gs.get_hand(2) if c.card_id == "REV_601t")
    assert _frozen_touch_infused(touch)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    eff = lc.get_opponent_effective_hp()
    assert face >= eff, (face, eff, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert lc.overlay_red_prompt_ok() or lc.calculate_lethal()[2]
    print("OK log infused touch lethal", face, eff, lc.overlay_spell_note())


if __name__ == "__main__":
    test_infused_returns_to_hand()
    test_uninfused_no_return()
    test_powered_up_rev601_counts_as_infused()
    test_double_touch_same_turn_with_mana()
    test_double_touch_skipped_without_mana()
    test_infused_play_from_power_log()
    test_pack_infused_touch_counts_bounce()
    test_log_infused_touch_lethal_before_play()
    print("OK frozen touch infuse")
