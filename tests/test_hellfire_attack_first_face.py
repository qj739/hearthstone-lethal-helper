#!/usr/bin/env python3
"""回归：无嘲讽时地狱烈焰应先随从攻击再施法，避免少算 1/1 场攻。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


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


def _minion(gs, eid, pid, atk, hp, *, card_id=""):
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
    m.tags["HEALTH"] = hp
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


def test_hellfire_attack_first_keeps_1_1_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=9, used=8)
    opp = _hero(gs, 2, 2)
    opp.health = 7
    _minion(gs, 10, 1, 1, 1, card_id="TOY_006")
    _minion(gs, 11, 1, 6, 8, card_id="TSC_069")
    _minion(gs, 12, 1, 3, 5, card_id="VAC_432")
    _minion(gs, 13, 1, 6, 8, card_id="TSC_069")
    _hand_spell(gs, 20, 1, "CORE_CS2_062", 3)
    _hand_spell(gs, 21, 1, "GDB_305", 3)
    _hand_spell(gs, 22, 1, "CATA_785", 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    pure, minion, _, spell, _ = lc.overlay_board_breakdown()
    assert pure == 16, pure
    assert minion >= 16, (minion, face, lc.overlay_spell_note(), lc._overlay_best_order)
    assert face >= 23, (face, minion, spell, lc.overlay_spell_note())
    assert getattr(lc, "_overlay_best_order", "") == "attack_first"


if __name__ == "__main__":
    test_hellfire_attack_first_keeps_1_1_face()
    print("OK hellfire attack_first face")
