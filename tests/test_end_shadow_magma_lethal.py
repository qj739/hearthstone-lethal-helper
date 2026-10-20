#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""时光之末的阴影 + 麦芽岩浆：法强后换嘲再连喝，解开复生嘲讽斩杀。"""
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
    h.tags["DAMAGE"] = 0
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, card_id="", taunt=False, reborn=False, ready=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0 if ready else 1
    if ready:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    if taunt:
        m.tags["TAUNT"] = 1
    if reborn:
        m.tags["REBORN"] = 1
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


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost})
    return s


def test_shadow_registered():
    defn = get_battlecry_def("END_031")
    assert defn is not None
    fighters = []
    defn.apply([], fighters, mult=1, enemy_shield=False, spell_power=0)
    assert fighters[-1]["spellpower"] == 1
    assert int(fighters[-1].get("attacks_left", 0) or 0) == 0


def test_lethal_before_plays():
    """10 血 + 5/9 复生嘲讽。阴影加法强，换嘲后三杯岩浆清场，日斑打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, health=10)
    _minion(gs, 10, 1, 5, 2, card_id="BE_749", ready=True)
    _minion(gs, 11, 1, 6, 2, card_id="WW_434", ready=True)
    _minion(gs, 20, 2, 5, 9, card_id="WW_001t13", taunt=True, reborn=True)
    _hand_minion(gs, 30, 1, "END_031", 3, 3, 3)
    _hand_spell(gs, 31, 1, "VAC_323", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _hp, _src, has_lethal = checker.calculate_lethal()
    note = checker.overlay_spell_note()
    assert has_lethal, (total, note)
    assert total >= 10, (total, note)
    assert "时光之末的阴影" in note or "麦芽岩浆" in note, note


if __name__ == "__main__":
    test_shadow_registered()
    test_lethal_before_plays()
    print("OK end shadow magma lethal")
