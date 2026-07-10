#!/usr/bin/env python3
"""通灵最强音 ETC_210：手牌 TAG_SCRIPT_DATA_NUM_1 为当前伤害。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    spell_script_damage,
    apply_spell_sequence_with_meta,
)
from hdt_python.spell_p0_direct import _apply_climactic_necrotic_explosion


def _hero(gs, eid, pid, *, dmg=0, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, *, script_dmg):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = "ETC_210"
    s.cost = 10
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 10
    s.tags["TAG_SCRIPT_DATA_NUM_1"] = script_dmg
    s.tags["TAG_SCRIPT_DATA_NUM_2"] = 4
    s.tags["TAG_SCRIPT_DATA_NUM_3"] = 8
    s.tags["TAG_SCRIPT_DATA_NUM_4"] = 2
    return s


def test_climactic_necrotic_script_damage():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    card = _hand_spell(gs, 30, 1, script_dmg=10)
    assert spell_script_damage(card, default=0) == 10
    assert get_board_spell_def("ETC_210") is not None


def test_climactic_necrotic_lethal_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10, used=0)
    _hero(gs, 20, 2, dmg=20)
    card = _hand_spell(gs, 30, 1, script_dmg=10)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    res, _, _ = apply_spell_sequence_with_meta(
        enemy, [], [(get_board_spell_def("ETC_210"), 10, card)],
        spell_mult=1, enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 10
    assert res.self_hero_heal == 10

    assert any(s.card_id == "ETC_210" for s, _, _ in hand_board_spells(gs, 1, 10))
    total, _, lethal = lc.calculate_lethal_potential()
    assert lethal, f"10 dmg vs 10 hp should lethal, total={total}"


def test_climactic_necrotic_zero_script_no_damage():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    card = _hand_spell(gs, 30, 1, script_dmg=0)
    enemy = []
    res = _apply_climactic_necrotic_explosion(
        enemy, [], mult=1, enemy_shield=False, card=card,
    )
    assert res.direct_face_damage == 0


if __name__ == "__main__":
    test_climactic_necrotic_script_damage()
    test_climactic_necrotic_lethal_face()
    test_climactic_necrotic_zero_script_no_damage()
    print("ok")
