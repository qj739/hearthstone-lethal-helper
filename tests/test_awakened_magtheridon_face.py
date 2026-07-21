#!/usr/bin/env python3
"""刚苏醒玛瑟里顿本回合不能打脸（DORMANT_AWAKENED_THIS_TURN）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.board_damage import (
    build_board_card,
    is_exhausted,
    _minion_summoned_this_turn,
)
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
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


def test_awakened_magtheridon_cannot_face_same_turn():
    """JUST_PLAYED 已清、NUM_TURNS>=1 时，仍须认 DORMANT_AWAKENED_THIS_TURN。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=20)

    ready = _minion(gs, 30, 1, 8, 8, card_id="READY")
    ready.tags["NUM_TURNS_IN_PLAY"] = 2
    ready.tags["EXHAUSTED"] = 0

    mag = _minion(gs, 31, 1, 12, 12, card_id="TOY_647")
    mag.tags.update({
        "DORMANT": 0,
        "DORMANT_AWAKENED_THIS_TURN": 1,
        "EXHAUSTED": 1,
        "JUST_PLAYED": 0,
        "1196": 0,
        "NUM_TURNS_IN_PLAY": 2,
    })

    assert _minion_summoned_this_turn(mag), "awakened Mag should count as summoned this turn"
    assert is_exhausted(mag), "awakened Mag must be exhausted this turn"
    view = build_board_card(mag, True, gs)
    assert not view.can_attack_hero, f"Mag must not face; got atk={view.attack}"
    assert view.attack == 0

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face == 8, f"only ready 8 should face; got {face} (Mag 12 wrongly included?)"
    print("OK awakened Mag no face", face)


def test_awakened_flag_cleared_next_turn_can_face():
    """下回合 DORMANT_AWAKENED 清零后可正常打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2)

    mag = _minion(gs, 31, 1, 12, 12, card_id="TOY_647")
    mag.tags.update({
        "DORMANT": 0,
        "DORMANT_AWAKENED_THIS_TURN": 0,
        "EXHAUSTED": 0,
        "JUST_PLAYED": 0,
        "NUM_TURNS_IN_PLAY": 1,
        "NUM_ATTACKS_THIS_TURN": 0,
    })
    view = build_board_card(mag, True, gs)
    assert view.can_attack_hero and view.attack == 12
    print("OK Mag next turn can face", view.attack)


if __name__ == "__main__":
    test_awakened_magtheridon_cannot_face_same_turn()
    test_awakened_flag_cleared_next_turn_can_face()
    print("all passed")
