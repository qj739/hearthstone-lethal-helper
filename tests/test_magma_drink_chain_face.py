#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦芽岩浆连喝：无嘲讽时须计满三杯打脸，不能只算首杯。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import (
    DRINK_SPELL_IDS,
    estimate_no_taunt_direct_face_damage,
    get_board_spell_def,
    partition_hand_spells_by_tier,
    spell_sim_tier,
    SpellSimTier,
)


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


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost})
    return s


def test_drink_stays_in_combo():
    assert "VAC_323" in DRINK_SPELL_IDS
    assert spell_sim_tier(get_board_spell_def("VAC_323")) == SpellSimTier.CLEAR_AND_FACE
    gs = GameState()
    card = _hand_spell(gs, 1, 1, "VAC_323", 2)
    defn = get_board_spell_def("VAC_323")
    combo, direct = partition_hand_spells_by_tier([(card, defn, 2)])
    assert not direct
    assert len(combo) == 1
    assert estimate_no_taunt_direct_face_damage(defn, card) == 3


def test_lethal_before_attacks():
    """16 场面 + 三杯岩浆 3 = 19，对手 18 血：攻击前就应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=7)
    _hero(gs, 2, 2, health=18)
    _minion(gs, 10, 1, 4, 4, card_id="A")
    _minion(gs, 11, 1, 2, 1, card_id="B")
    _minion(gs, 12, 1, 2, 2, card_id="C")
    _minion(gs, 13, 1, 4, 1, card_id="D")
    _minion(gs, 14, 1, 2, 1, card_id="E")
    _minion(gs, 15, 1, 2, 3, card_id="F")
    _hand_spell(gs, 30, 1, "VAC_323", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _hp, _src, has_lethal = checker.calculate_lethal()
    note = checker.overlay_spell_note()
    _pure, _board, _w, spell, _hp_s = checker.overlay_board_breakdown()
    # 攻击前：16 场面 + 连喝 3 >= 19；分项可能记在穿插线里
    assert total >= 19, (total, spell, note)
    assert has_lethal, (total, note)


if __name__ == "__main__":
    test_drink_stays_in_combo()
    test_lethal_before_attacks()
    print("OK magma drink chain face")
