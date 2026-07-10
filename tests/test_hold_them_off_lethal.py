#!/usr/bin/env python3
"""拦住他们！ JAIL_913：友方随从 +5/+5，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
)
from hdt_python.spell_p0_other import _apply_hold_them_off


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
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
    m.tags["479"] = atk
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


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


def test_hold_them_off_buffs_attacker():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=19)
    _minion(gs, 30, 1, 1, 3, card_id="REV_002")
    _hand_spell(gs, 40, 1, "JAIL_913", 5)

    lc = LethalChecker(gs)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    assert fighters[0]["atk"] == 1
    _apply_hold_them_off([], fighters, mult=1, enemy_shield=False, gs=gs, player_id=1)
    assert fighters[0]["atk"] == 6
    assert fighters[0]["health"] == 8

    assert get_board_spell_def("JAIL_913") is not None
    assert any(s.card_id == "JAIL_913" for s, _, _ in hand_board_spells(gs, 1, 10))


def test_hold_them_off_enables_lethal():
    """1 攻随从 + 拦住他们 +5 = 6 攻，对手 6 血可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=24)
    _minion(gs, 30, 1, 1, 3, card_id="REV_002")
    _hand_spell(gs, 40, 1, "JAIL_913", 5)

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    assert face >= 6, f"expected face>=6 got {face}"
    assert lethal, f"should detect lethal total={total} face={face}"


if __name__ == "__main__":
    test_hold_them_off_buffs_attacker()
    test_hold_them_off_enables_lethal()
    print("ok")
