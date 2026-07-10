#!/usr/bin/env python3
"""兽群呼唤 OG_211：霍弗冲锋 + 雷欧克 +1 攻应参与斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
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
    return s


def test_call_of_the_wild_registered():
    assert get_board_spell_def("CORE_OG_211") is not None
    assert get_board_spell_def("OG_211") is not None


def test_call_of_the_wild_huffer_charge_face():
    """空场：霍弗 4 + 雷欧克光环 1 = 5 冲锋场攻。"""
    defn = get_board_spell_def("CORE_OG_211")
    spell = type("C", (), {"card_id": "CORE_OG_211", "entity_id": 11, "tags": {}})()
    fighters = []
    apply_spell_sequence([], fighters, [(defn, 8, spell)])
    huffer = next(f for f in fighters if f.get("card_id") == "NEW1_034")
    assert huffer.get("charge") and huffer.get("attacks_left") == 1
    assert huffer.get("atk") == 5, huffer.get("atk")


def test_call_of_the_wild_lethal():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=8, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 5
    _hand_spell(gs, 11, 1, "CORE_OG_211", 8)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face >= 5, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert has, (face, has, lc.overlay_spell_note())


if __name__ == "__main__":
    test_call_of_the_wild_registered()
    test_call_of_the_wild_huffer_charge_face()
    test_call_of_the_wild_lethal()
    print("OK call of the wild")
