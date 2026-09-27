#!/usr/bin/env python3
"""灼烧之风：手牌有火焰法术时应按 6 伤；英雄掉血时清掉失效护甲。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, Entity
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence


def test_scorching_winds_hand_fire_fallback_without_powered_up():
    gs = GameState()
    gs.local_player_id = 1
    winds = gs.get_entity(30)
    winds.cardtype = "SPELL"
    winds.card_id = "FIR_910"
    winds.controller = 1
    winds.zone = "HAND"
    winds.tags["ZONE"] = "HAND"
    winds.tags["POWERED_UP"] = 0

    fire = gs.get_entity(31)
    fire.cardtype = "SPELL"
    fire.card_id = "FIR_911"
    fire.controller = 1
    fire.zone = "HAND"
    fire.tags["ZONE"] = "HAND"
    fire.tags["SPELL_SCHOOL"] = 2

    defn = get_board_spell_def("FIR_910")
    res = apply_spell_sequence(
        [], [], [(defn, 3, winds)], enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 6, res.direct_face_damage
    print("OK scorching winds hand fire fallback")


def test_hero_damage_clears_stale_armor():
    from hdt_python.power_parser import PowerLogParser

    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    p._live_mode = False
    hero = gs.get_entity(66)
    hero.cardtype = "HERO"
    hero.health = 30
    hero.damage = 24
    hero.tags["ARMOR"] = 3
    hero.tags["DAMAGE"] = 24

    p._apply_tag(66, "DAMAGE", "27")
    assert int(hero.tags.get("ARMOR", 0) or 0) == 0, hero.tags.get("ARMOR")
    assert hero.damage == 27
    print("OK stale armor cleared on hero damage")


if __name__ == "__main__":
    test_scorching_winds_hand_fire_fallback_without_powered_up()
    test_hero_damage_clears_stale_armor()
    print("all passed")
