#!/usr/bin/env python3
"""霜巫十字绣可打脸；配合注能冰冻之触回手应识别斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence


def _hero(gs, eid, pid, *, dmg=0, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def _minion(gs, eid, pid, atk, hp, *, card_id="m", taunt=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    if taunt:
        m.tags["TAUNT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hero_power(gs, eid, pid, card_id="HERO_08bp", cost=2):
    e = gs.get_entity(eid)
    e.cardtype = "HERO_POWER"
    e.controller = pid
    e.zone = "PLAY"
    e.card_id = card_id
    e.cost = cost
    e.tags["ZONE"] = "PLAY"
    e.tags["COST"] = cost
    e.tags["CARDTYPE"] = "HERO_POWER"
    return e


def test_cross_stitch_can_face():
    """霜巫十字绣：对角色 3 伤，空场应打脸。"""
    res = apply_spell_sequence(
        [], [],
        [(get_board_spell_def("TOY_377"), 1, type("C", (), {"card_id": "TOY_377", "tags": {}})())],
    )
    assert res.direct_face_damage == 3, res.direct_face_damage
    print("OK cross stitch faces for 3")


def test_stitch_plus_infused_touch_lethal_through_taunt():
    """
    对手 10 血有嘲讽：十字绣打脸 3 + 注能之触回手 3+3 + 火冲 1 = 10。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, dmg=20)  # 10 hp
    _hero_power(gs, 3, 1)
    _minion(gs, 20, 2, 3, 7, card_id="TOY_380", taunt=True)
    _hand_spell(gs, 40, 1, "TOY_377", 1)
    touch = _hand_spell(gs, 41, 1, "REV_601t", 2)
    touch.tags["INFUSED"] = 1

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    note = getattr(lc, "_overlay_spell_note", "")
    assert total >= 10, f"expected >=10, got {total} note={note}"
    lt, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"should lethal, total={total} lt={lt} note={note}"
    print("OK stitch+touch lethal through taunt", total, note)


if __name__ == "__main__":
    test_cross_stitch_can_face()
    test_stitch_plus_infused_touch_lethal_through_taunt()
    print("all passed")
