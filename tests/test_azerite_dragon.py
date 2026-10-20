#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""艾泽里特龙：战吼其他场面随从 +3/+3。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, mana=10, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, card_id="", ready=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "PLAY"
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0 if ready else 1
    if ready:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({"ZONE": "HAND", "COST": cost, "ATK": atk, "HEALTH": hp})
    return m


def test_buff_other_board():
    defn = get_battlecry_def("DEEP_999t4")
    assert defn is not None
    assert defn.base_cost == 4
    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 2, "health": 2,
         "attacks_left": 1, "can_face": True},
    ]
    res = defn.apply([], fighters, mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 0
    assert fighters[0]["atk"] == 5 and fighters[0]["health"] == 5
    body = fighters[-1]
    assert body["card_id"] == "DEEP_999t4"
    assert body["atk"] == 5 and body["health"] == 5
    assert int(body.get("attacks_left", 0) or 0) == 0


def test_lethal_from_hand():
    """2 攻场面 + 艾泽里特龙 → 5 攻打脸斩 5 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=4)
    _hero(gs, 2, 2, health=5)
    _minion(gs, 10, 1, 2, 2, card_id="FACE")
    _hand_minion(gs, 30, 1, "DEEP_999t4", 4, 5, 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _hp, _src, has_lethal = checker.calculate_lethal()
    note = checker.overlay_spell_note()
    assert has_lethal, (total, note)
    assert total >= 5, (total, note)
    assert "艾泽里特龙" in note, note


if __name__ == "__main__":
    test_buff_other_board()
    test_lethal_from_hand()
    print("OK azerite dragon")
