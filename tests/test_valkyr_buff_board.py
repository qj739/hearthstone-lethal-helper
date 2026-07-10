#!/usr/bin/env python3
"""瓦格里勇士：无 NUM_TURNS_IN_PLAY 时视为召唤疲劳。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.board_damage import build_board_card


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    gs.hero_entity_ids[pid] = eid
    return h


def _valkyr(gs, eid, pid, atk, *, turns_in_play=None, tag_4741=0):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "TTN_470t"
    m.atk = atk
    m.health = atk
    m.tags["ZONE"] = "PLAY"
    m.tags["479"] = atk
    m.tags["ATK"] = atk
    m.tags["RUSH"] = 1
    m.tags["1196"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    if turns_in_play is not None:
        m.tags["NUM_TURNS_IN_PLAY"] = turns_in_play
    if tag_4741:
        m.tags["4741"] = tag_4741
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_missing_num_turns_in_play_is_exhausted():
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    m = _valkyr(gs, 10, 1, 3, turns_in_play=None, tag_4741=0)
    view = build_board_card(m, True, gs)
    assert not view.can_attack_hero, "无 NUM_TURNS_IN_PLAY 的随从本回合不应打脸"
    assert view.can_attack_minion, "突袭仍应能解随从"


def test_double_buff_still_attackable_without_4741_lock():
    """4741 锁已移除：同回合连 buff 后突袭仍可解场。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    m = _valkyr(gs, 10, 1, 3, turns_in_play=None, tag_4741=2)
    view = build_board_card(m, True, gs)
    assert not view.can_attack_hero
    assert view.can_attack_minion


def test_next_turn_can_attack_after_buff():
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    m = _valkyr(gs, 10, 1, 4, turns_in_play=1, tag_4741=2)
    view = build_board_card(m, False, gs)
    assert view.can_attack_hero


if __name__ == "__main__":
    test_missing_num_turns_in_play_is_exhausted()
    test_double_buff_still_attackable_without_4741_lock()
    test_next_turn_can_attack_after_buff()
    print("all passed")
