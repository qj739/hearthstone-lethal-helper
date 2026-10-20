#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深岩之洲晶簇：回合结束对所有敌人造成 2 点伤害。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.end_turn_board import END_TURN_BY_CARD, end_turn_face_damage
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
    return h


def _board_minion(gs, eid, pid):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "DEEP_999t2"
    m.atk = 1
    m.health = 2
    m.cost = 2
    m.tags.update({
        "ZONE": "PLAY", "ATK": 1, "HEALTH": 2, "COST": 2,
        "EXHAUSTED": 1, "NUM_ATTACKS_THIS_TURN": 0,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_on_board_face():
    assert "DEEP_999t2" in END_TURN_BY_CARD
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, health=2)
    _board_minion(gs, 10, 1)
    face, notes = end_turn_face_damage(gs.get_board(1), [], False)
    assert face == 2, (face, notes)
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _hp, _src, has_lethal = checker.calculate_lethal()
    assert total >= 2, total
    assert has_lethal, total


def test_from_hand_before_play():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=2)
    _hero(gs, 2, 2, health=2)
    hand = gs.get_entity(30)
    hand.cardtype = "MINION"
    hand.controller = 1
    hand.zone = "HAND"
    hand.card_id = "DEEP_999t2"
    hand.cost = 2
    hand.atk = 1
    hand.health = 2
    hand.tags.update({"ZONE": "HAND", "ATK": 1, "HEALTH": 2, "COST": 2})
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _hp, _src, has_lethal = checker.calculate_lethal()
    note = checker.overlay_spell_note()
    assert total >= 2, (total, note)
    assert has_lethal, (total, note)
    assert "深岩之洲晶簇" in note, note


if __name__ == "__main__":
    test_on_board_face()
    test_from_hand_before_play()
    print("OK azerite cluster")
