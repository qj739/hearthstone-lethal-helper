#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""毒性吐息：友方亡灵剧毒。技能召出的食尸鬼可解掉打不死的嘲讽。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import SpellSimTier, get_board_spell_def, spell_sim_tier


def _hero(gs, eid, pid, mana=10, used=0, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id=""):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "PLAY"
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
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


def _hero_power(gs, eid, pid, card_id, cost=2):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = cost
    p.tags["ZONE"] = "PLAY"
    p.tags["COST"] = cost
    return p


def test_poison_only_undead():
    defn = get_board_spell_def("CORE_EDR_002")
    assert defn is not None
    assert get_board_spell_def("EDR_002") is not None
    assert defn.base_cost == 2
    assert spell_sim_tier(defn) == SpellSimTier.UTILITY
    fighters = [
        {"kind": "minion", "entity_id": 1, "card_id": "BEAST",
         "atk": 1, "health": 1, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 2, "card_id": "HERO_11bpt",
         "atk": 1, "health": 1, "attacks_left": 1, "can_face": True, "undead": True},
    ]
    taunts = [{
        "kind": "minion", "taunt": True, "health": 7, "atk": 6,
        "entity_id": 9, "shield": False,
    }]
    res = defn.apply(taunts, fighters, mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 0
    assert not fighters[0].get("poisonous")
    assert fighters[1].get("poisonous") is True


def test_lethal_before_hero_power():
    """6/7 嘲讽挡住 4 攻。技能召食尸鬼，吐息给剧毒，解嘲后 4 攻斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=4)
    _hero(gs, 2, 2, health=4)
    _minion(gs, 10, 1, 4, 4, card_id="FACE")
    _minion(gs, 20, 2, 6, 7, taunt=True, card_id="BE_204")
    _hand_spell(gs, 30, 1, "CORE_EDR_002", 2)
    _hero_power(gs, 50, 1, "HERO_11bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _pure, _board, _weapon, _spell, hp_skill = checker.overlay_board_breakdown()
    _hp, _dmg, has_lethal = checker.calculate_lethal()
    note = checker.overlay_spell_note()
    assert has_lethal, (total, note, hp_skill)
    assert total >= 4, (total, note)
    assert "毒性吐息" in note, note
    assert "食尸鬼冲锋" in note, note


if __name__ == "__main__":
    test_poison_only_undead()
    test_lethal_before_hero_power()
    print("OK toxic breath")
