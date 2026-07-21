#!/usr/bin/env python3
"""防晒霜 VAC_917t：友方随从 +1/+2，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells


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


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1):
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
    m.tags["NUM_TURNS_IN_PLAY"] = turns
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


def test_sunscreen_registered():
    assert get_board_spell_def("VAC_917t") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _hand_spell(gs, 40, 1, "VAC_917t", 1)
    assert any(s.card_id == "VAC_917t" for s, _, _ in hand_board_spells(gs, 1, 10))
    print("OK sunscreen registered")


def test_sunscreen_buff_face_lethal():
    """可攻击 4 攻 + 防晒霜 +1 = 5，对手 5 血应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=25)  # 5 hp
    _minion(gs, 10, 1, 4, 3, turns=1)
    _hand_spell(gs, 40, 1, "VAC_917t", 1)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 5, f"expected >=5 face after sunscreen, got {total}"
    assert has_lethal, "4+1 sunscreen should lethal vs 5 hp"
    print("OK sunscreen face lethal", total)


if __name__ == "__main__":
    test_sunscreen_registered()
    test_sunscreen_buff_face_lethal()
    print("all passed")
