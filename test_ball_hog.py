#!/usr/bin/env python3
"""球霸野猪人 TOY_642：战吼/亡语仅对最低血量敌人（含英雄）造成伤害。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.spell_board import (
    estimate_no_taunt_direct_face_damage,
    _SyntheticSpellCard,
)


def _hero(gs, eid, pid, hp=30, armor=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = 0
    h.tags["ARMOR"] = armor
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, card_id="M"):
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


def _hand_bc(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost


def test_ball_hog_hits_lowest_minion_not_face():
    """对手 3/3 + 29 血英雄，打出球霸：战吼 3 点打随从，不打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=29)
    _minion(gs, 20, 2, 3, 3, card_id="OPP_33")
    _hand_bc(gs, 30, 1, "TOY_642", 4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    assert spell == 0, f"battlecry should not face, spell={spell}"
    assert "球霸野猪人" in note or total <= 3, (total, note, board, spell)
    print("OK ball hog hits minion not face", total, note, spell)


def test_ball_hog_hits_face_when_hero_lowest():
    """对手 2 血 + 12/12，打出球霸：战吼打脸 3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=2)
    _minion(gs, 20, 2, 12, 12, card_id="BIG")
    _hand_bc(gs, 30, 1, "TOY_642", 4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()

    assert spell >= 3, f"expected >=3 face, got spell={spell} total={total}"
    print("OK ball hog face when hero lowest", total, spell)


def test_ball_hog_estimate_no_taunt_with_enemy_board():
    """无嘲讽直伤估算：场上有 3/3 时不应把战吼 3 点当打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=29)
    _minion(gs, 20, 2, 3, 3)
    card = _SyntheticSpellCard("TOY_642", 4)
    defn = get_battlecry_def("TOY_642")
    dmg = estimate_no_taunt_direct_face_damage(
        defn, card, gs=gs, player_id=1, enemy_shield=False,
    )
    assert dmg == 0, dmg
    print("OK ball hog estimate no face with 3/3", dmg)


def test_ball_hog_apply_direct():
    defn = get_battlecry_def("TOY_642")
    taunts = [{"health": 3, "atk": 3, "shield": False, "spell_immune": False, "entity_id": 1}]
    fighters = []
    res = defn.apply(taunts, fighters, mult=1, enemy_shield=False, gs=None, player_id=None)
    assert res.direct_face_damage == 0, res.direct_face_damage
    print("OK ball hog apply no face vs 3hp minion")


if __name__ == "__main__":
    test_ball_hog_apply_direct()
    test_ball_hog_estimate_no_taunt_with_enemy_board()
    test_ball_hog_hits_lowest_minion_not_face()
    test_ball_hog_hits_face_when_hero_lowest()
    print("all passed")
