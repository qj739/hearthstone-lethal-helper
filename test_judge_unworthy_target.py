#!/usr/bin/env python3
"""审判恶徒：须点敌方随从，空场不可对英雄使用。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    hand_board_spells,
    get_board_spell_def,
    apply_spell_sequence_with_meta,
    pick_judge_unworthy_target,
)
from hdt_python.spell_p0_aoe import _apply_judge_unworthy


def _hero(gs, eid, pid, *, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
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
    m.tags["479"] = atk
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = "TTN_853"
    s.cost = 4
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 4
    return s


def test_judge_unworthy_no_minion_no_damage():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=25)
    _hand_spell(gs, 30, 1)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    res, _, _ = apply_spell_sequence_with_meta(
        enemy, [], [(get_board_spell_def("TTN_853"), 4, gs.get_entity(30))],
        spell_mult=1, enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 0, f"empty board should not hit face, got {res.direct_face_damage}"
    assert not hand_board_spells(gs, 1, 10), "should not list spell without enemy minion"


def test_judge_unworthy_sets_minion_not_face_only():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=25)
    _minion(gs, 40, 2, 5, 8)
    _hand_spell(gs, 30, 1)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    picked = pick_judge_unworthy_target(enemy)
    assert picked is not None
    assert picked.get("kind") != "hero"

    res = _apply_judge_unworthy(enemy, [], mult=1, enemy_shield=False)
    assert res.direct_face_damage == 1
    assert hand_board_spells(gs, 1, 10), "should be playable with enemy minion"


if __name__ == "__main__":
    test_judge_unworthy_no_minion_no_damage()
    test_judge_unworthy_sets_minion_not_face_only()
    print("ok")
