#!/usr/bin/env python3
"""甜筒殡淇淋 VAC_427：2 费 3 伤，可打脸。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    apply_spell_sequence_with_meta,
    player_corpses,
)


def _hero(gs, eid, pid, *, dmg=0, mana=10, used=0, corpses=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    if corpses:
        h.tags["CORPSES"] = corpses
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, *, powered=False):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = "VAC_427"
    s.cost = 2
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 2
    if powered:
        s.tags["POWERED_UP"] = 1
    return s


def test_corpsicle_face_lethal():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10, used=0, corpses=5)
    _hero(gs, 20, 2, dmg=27)
    _hand_spell(gs, 30, 1)

    assert player_corpses(gs, 1) == 5
    assert get_board_spell_def("VAC_427") is not None
    assert hand_board_spells(gs, 1, 10)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    card = gs.get_entity(30)
    res, _, _ = apply_spell_sequence_with_meta(
        enemy, [], [(get_board_spell_def("VAC_427"), 2, card)],
        spell_mult=1, enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 3

    total, _, lethal = lc.calculate_lethal_potential()
    assert lethal, f"3 hp should lethal with corpsicle, total={total}"


def test_corpsicle_face_without_corpses():
    """无残骸也可打 3 伤打脸（残骸仅影响回合结束是否回手）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10, used=0, corpses=0)
    _hero(gs, 20, 2, dmg=27)
    _hand_spell(gs, 30, 1)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    card = gs.get_entity(30)
    res, _, _ = apply_spell_sequence_with_meta(
        enemy, [], [(get_board_spell_def("VAC_427"), 2, card)],
        spell_mult=1, enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 3
    assert hand_board_spells(gs, 1, 10)


if __name__ == "__main__":
    test_corpsicle_face_lethal()
    test_corpsicle_face_without_corpses()
    print("ok")
