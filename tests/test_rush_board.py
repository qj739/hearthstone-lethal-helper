#!/usr/bin/env python3
"""突袭随从：上场当回合可解嘲但不能计入打脸场攻"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import board_active_turn_for_display


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    gs.hero_entity_ids[pid] = eid
    return h


def _rush_minion(gs, eid, pid, atk, hp, *, just_played=True, tag_1196=0):
    """模拟 Power.log：1196 已清 0 但 JUST_PLAYED 仍为 1 的刚上场突袭。"""
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "TOY_312"
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["RUSH"] = 1
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    if just_played:
        m.tags["JUST_PLAYED"] = 1
    if tag_1196:
        m.tags["1196"] = tag_1196
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _normal_minion(gs, eid, pid, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "M1"
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 2
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_rush_no_face_same_turn_after_1196_clears():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    rush = _rush_minion(gs, 4, 1, 4, 4, just_played=True, tag_1196=0)
    _normal_minion(gs, 10, 1, 3, 3)

    view = rush.board_card_view(True)
    assert view.can_attack_minion, "rush should attack minions same turn"
    assert not view.can_attack_hero, "rush should not face same turn when JUST_PLAYED"

    board = gs.get_overlay_board(1)
    assert board.minion_damage == 3, f"face damage should be 3 not 7, got {board.minion_damage}"
    assert board.face_attack_damage_no_taunt() == 3

    checker = LethalChecker(gs)
    assert checker.overlay_board_face_damage() == 3
    print("OK rush no face same turn", board.minion_damage)


def test_rush_face_next_turn_preview():
    """对方回合预览下回合：突袭已在场一回合，应能打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    m = _rush_minion(gs, 4, 1, 4, 4, just_played=False, tag_1196=0)
    m.tags.pop("JUST_PLAYED", None)
    m.tags["NUM_TURNS_IN_PLAY"] = 1

    active = board_active_turn_for_display(gs, 1)
    view = m.board_card_view(active)
    assert view.can_attack_hero, f"rush should face on next turn preview, active={active}"

    board = gs.get_overlay_board(1)
    assert board.minion_damage == 4
    print("OK rush face next turn preview", board.minion_damage)


def test_cata_465t_whelp_no_face_after_1196_clears():
    """投喂加餐衍生物：1196 清零后仍为本回合突袭，不能打脸。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    for i, eid in enumerate([194, 195, 196, 197, 198], 1):
        m = gs.get_entity(eid)
        m.cardtype = "MINION"
        m.controller = 2
        m.zone = "PLAY"
        m.card_id = "CATA_465t"
        m.atk = 5
        m.health = 4
        m.tags.update({
            "ZONE": "PLAY", "ATK": 5, "479": 5, "HEALTH": 4,
            "RUSH": 1, "EXHAUSTED": 1, "1196": 0,
            "NUM_ATTACKS_THIS_TURN": 0, "ZONE_POSITION": i,
        })
        gs.board_slots.setdefault(2, {})[i] = eid

    view = gs.get_entity(194).board_card_view(True)
    assert view.can_attack_minion
    assert not view.can_attack_hero

    board = gs.get_overlay_board(2)
    assert board.minion_damage == 0
    assert board.face_attack_damage_no_taunt() == 0
    assert LethalChecker(gs).overlay_board_face_damage() == 0
    print("OK cata 465t whelp no face after 1196 clears")


def test_attackable_by_rush_tag_not_treated_as_rush():
    """ATTACKABLE_BY_RUSH 是老随从被突袭指定的标记，不应阻止打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    m = _normal_minion(gs, 10, 1, 5, 5)
    m.tags["ATTACKABLE_BY_RUSH"] = 1
    m.tags.pop("NUM_TURNS_IN_PLAY", None)
    m.tags["NUM_TURNS_IN_PLAY"] = 3

    view = m.board_card_view(True)
    assert view.can_attack_hero, "ATTACKABLE_BY_RUSH alone must not block hero"
    print("OK ATTACKABLE_BY_RUSH not rush")


if __name__ == "__main__":
    test_rush_no_face_same_turn_after_1196_clears()
    test_cata_465t_whelp_no_face_after_1196_clears()
    test_rush_face_next_turn_preview()
    test_attackable_by_rush_tag_not_treated_as_rush()
    print("all passed")
