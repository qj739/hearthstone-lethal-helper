#!/usr/bin/env python3
"""回归：英雄/场面法强应计入法术伤害与斩杀判定。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    apply_spell_sequence,
    get_board_spell_def,
    scaled_spell_damage,
    total_spell_power,
)


def _hero(gs, eid, pid, *, mana=10, used=0, spell_power_base=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["CURRENT_SPELLPOWER_BASE"] = spell_power_base
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


def test_total_spell_power_includes_hero_base():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, spell_power_base=2)
    assert total_spell_power(gs, 1) == 2


def test_sleet_storm_scales_with_spell_power():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, spell_power_base=2)
    spell = _hand_spell(gs, 10, 1, "CATA_485", 1)
    defn = get_board_spell_def("CATA_485")
    assert defn is not None
    res = apply_spell_sequence(
        [], [], [(defn, 1, spell)],
        gs=gs, player_id=1, enemy_shield=False,
    )
    assert res.direct_face_damage == scaled_spell_damage(2, spell_power=2), res.direct_face_damage


def test_two_spell_power_spells_lethal():
    """+2 法强下两张激寒急流应可斩杀 16 血对手。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0, spell_power_base=2)
    opp = _hero(gs, 2, 2)
    opp.health = 8
    opp.damage = 0
    s1 = _hand_spell(gs, 11, 1, "CATA_485", 1)
    s2 = _hand_spell(gs, 12, 1, "CATA_485", 1)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    per_spell = scaled_spell_damage(2, spell_power=2)
    assert face >= per_spell * 2, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert has, (face, has, lc.overlay_spell_note())


if __name__ == "__main__":
    test_total_spell_power_includes_hero_base()
    test_sleet_storm_scales_with_spell_power()
    test_two_spell_power_spells_lethal()
    print("OK spell power lethal")
