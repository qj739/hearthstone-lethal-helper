#!/usr/bin/env python3
"""回归：批量生产 MIS_707 是对己方英雄伤害，不能算打脸。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import get_board_spell_def
from hdt_python.arena_season_bulk import _classify_spell, register_arena_season_gap
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def test_classify_self_damage():
    text = (
        "Draw 2 cards. Deal $3 damage to your hero. "
        "Shuffle 2 copies of this into your deck."
    )
    spec = _classify_spell(text)
    assert spec.kind == "self_damage", spec
    assert spec.amount == 3, spec
    print("OK classify self_damage", spec)


def test_mass_production_apply_is_self_damage():
    register_arena_season_gap()
    defn = get_board_spell_def("MIS_707")
    assert defn is not None
    assert defn.name == "批量生产"
    res = defn.apply([], [], mult=1, enemy_shield=False)
    assert res.direct_face_damage == 0, res
    assert res.self_hero_damage == 3, res
    print("OK apply self_hero_damage=3", res)


def test_mass_production_not_counted_as_face_lethal():
    """手牌仅有批量生产时，不应贡献 3 点打脸斩杀。"""
    register_arena_season_gap()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True

    def _hero(eid, pid, *, hp=30, dmg=0, mana=10):
        h = gs.get_entity(eid)
        h.cardtype = "HERO"
        h.controller = pid
        h.health = hp
        h.damage = dmg
        h.tags["DAMAGE"] = dmg
        h.tags["RESOURCES"] = mana
        h.tags["RESOURCES_USED"] = 0
        gs.hero_entity_ids[pid] = eid

    _hero(1, 1, mana=10)
    _hero(2, 2, hp=30, dmg=27)  # 3 血
    c = gs.get_entity(30)
    c.cardtype = "SPELL"
    c.controller = 1
    c.zone = "HAND"
    c.card_id = "MIS_707"
    c.cost = 1
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = 1

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face < 3 or "批量" not in (lc.overlay_spell_note() or ""), (
        face, lc.overlay_spell_note()
    )
    assert not lethal, f"self-damage should not face-lethal, face={face}"
    print("OK not face lethal", face, lc.overlay_spell_note())


if __name__ == "__main__":
    test_classify_self_damage()
    test_mass_production_apply_is_self_damage()
    test_mass_production_not_counted_as_face_lethal()
