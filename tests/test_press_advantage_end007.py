#!/usr/bin/env python3
"""发挥优势 END_007：打出前应计入 1 伤 + 英雄攻，不能因直伤前缀漏斩。"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import register_arena_season_gap
from hdt_python.battlecry_board import hand_all_board_plays
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import (
    get_board_spell_def,
    partition_hand_spells_by_tier,
    spell_mutates_fighters_aside_from_face,
)

register_arena_season_gap()


def _setup(*, opp_damage=13, weapon_atk=3, mana=6) -> GameState:
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 1
    for eid, pid, dmg in ((1, 1, 0), (2, 2, opp_damage)):
        h = gs.get_entity(eid)
        h.cardtype = "HERO"
        h.controller = pid
        h.zone = "PLAY"
        h.health = 30
        h.damage = dmg
        h.tags.update({
            "ZONE": "PLAY", "HEALTH": 30, "DAMAGE": dmg,
            "ATK": weapon_atk if pid == 1 else 0,
            "RESOURCES": mana, "RESOURCES_USED": 0,
            "EXHAUSTED": 0, "NUM_ATTACKS_THIS_TURN": 0,
        })
        gs.hero_entity_ids[pid] = eid
    w = gs.get_entity(3)
    w.cardtype = "WEAPON"
    w.controller = 1
    w.zone = "PLAY"
    w.card_id = "JAIL_730"
    w.atk = weapon_atk
    w.durability = 2
    w.damage = 0
    w.health = 2
    w.tags.update({
        "ZONE": "PLAY", "ATK": weapon_atk, "DURABILITY": 2,
        "HEALTH": 2, "DAMAGE": 0,
    })
    s = gs.get_entity(58)
    s.cardtype = "SPELL"
    s.controller = 1
    s.zone = "HAND"
    s.card_id = "END_007"
    s.cost = 2
    s.tags.update({"ZONE": "HAND", "COST": 2, "CARDTYPE": "SPELL"})
    return gs


def test_end007_mutates_fighters():
    d = get_board_spell_def("END_007")
    assert d is not None
    assert spell_mutates_fighters_aside_from_face(d)


def test_end007_stays_in_combo_not_direct_prefix():
    gs = _setup()
    plays = hand_all_board_plays(gs, 1, 6)
    combo, direct = partition_hand_spells_by_tier(plays)
    assert any(c.card_id == "END_007" for c, _, _ in combo)
    assert not any(c.card_id == "END_007" for c, _, _ in direct)


def test_end007_weapon_lethal_before_play():
    """对手 5 血：武器 3 + 发挥优势 1伤+1攻 = 5，打出前应够斩。"""
    gs = _setup(opp_damage=25, weapon_atk=3)  # 30-25=5
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    assert face >= 5, (face, lc.overlay_board_breakdown(), lc.overlay_hero_buff_face(), note)
    assert "发挥优势" in note


def test_end007_counts_hero_buff_with_weapon():
    gs = _setup(opp_damage=25, weapon_atk=3)  # 5 hp
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _pure, _mn, weapon, spell, _hp = lc.overlay_board_breakdown()
    hero_buff = lc.overlay_hero_buff_face()
    # 并入武器后 hero_buff 可能为 0，但 weapon+spell+buff >= 5
    assert face >= 5, (face, weapon, spell, hero_buff, lc.overlay_spell_note())
    assert weapon + spell + hero_buff >= 5, (weapon, spell, hero_buff)


if __name__ == "__main__":
    test_end007_mutates_fighters()
    test_end007_stays_in_combo_not_direct_prefix()
    test_end007_counts_hero_buff_with_weapon()
    test_end007_weapon_lethal_before_play()
    print("ok")
