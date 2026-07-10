#!/usr/bin/env python3
"""END_022 时光扭曲先知：打出 + 火焰冲击点伤 + 法术法强斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.damaged_spell_power import (
    BOARD_DAMAGED_SPELL_POWER,
    damage_friendly_fighter,
)
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import scaled_spell_damage


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.card_id = "HERO_08"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["CLASS"] = "MAGE"
    gs.hero_entity_ids[pid] = eid
    return h


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


def _hand_minion(gs, eid, pid, card_id, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({"ZONE": "HAND", "ATK": atk, "HEALTH": hp})
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    return s


def test_end_022_registered():
    assert "END_022" in BOARD_DAMAGED_SPELL_POWER


def test_damaged_spell_power_unit():
    f = {"kind": "minion", "card_id": "END_022", "health": 3, "damage": 0, "max_health": 3}
    damage_friendly_fighter(f, 1)
    assert f.get("spellpower") == 2


def test_end_022_play_ping_spell_lethal():
    """5 费：先知(1) + 火焰冲击(2) 点伤激活 + 冰冻之触(2) = 3+2=5 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=5, used=0)
    _hero_power(gs, 50, 1, "HERO_08bp", 2)
    opp = _hero(gs, 2, 2)
    opp.health = 5
    _hand_minion(gs, 11, 1, "END_022", 1, 1, 3)
    _hand_spell(gs, 12, 1, "REV_601", 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    per_touch = scaled_spell_damage(3, spell_power=2)
    assert per_touch == 5, per_touch
    assert face >= per_touch, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert has, (face, has, lc.overlay_spell_note())


if __name__ == "__main__":
    test_end_022_registered()
    test_damaged_spell_power_unit()
    test_end_022_play_ping_spell_lethal()
    print("OK end_022 lethal")
