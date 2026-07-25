#!/usr/bin/env python3
"""服装裁缝 ETC_420：战吼按自身当前攻/血（含 BUFF）给友方同等加成。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def


def _hero(gs, eid, pid, *, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", turns=1):
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
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_tailor(gs, eid, pid, *, atk=2, hp=2, cost=3):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = "ETC_420"
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "HAND"
    m.tags["COST"] = cost
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["HEALTH"] = hp
    return m


def test_outfit_tailor_registered():
    defn = get_battlecry_def("ETC_420")
    assert defn is not None and defn.name == "服装裁缝"
    print("OK ETC_420 registered", defn.name)


def test_outfit_tailor_base_buffs_face_attacker():
    """基础 2/2 裁缝：给场上 3/3 +2/+2 → 5 攻打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3, card_id="FACE")
    _hand_tailor(gs, 30, 1, atk=2, hp=2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note() or ""
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    # 3+2=5 打脸；裁缝本回合失调不攻
    assert board == 5, (total, board, spell, note)
    assert total == 5, (total, board, note)
    assert "服装裁缝" in note, note
    print("OK base tailor +2/+2 face", total, note)


def test_outfit_tailor_uses_buffed_hand_stats():
    """手牌被 BUFF 到 6/6：战吼给友方 +6/+6，场攻 2→8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    oh = _hero(gs, 2, 2)
    oh.health = 8
    oh.damage = 0
    _minion(gs, 10, 1, 2, 2, card_id="FACE")
    _hand_tailor(gs, 30, 1, atk=6, hp=6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note() or ""
    _, board, _, _, _ = checker.overlay_board_breakdown()
    assert board == 8, (total, board, note)
    assert total == 8, (total, board, note)
    _, _, lethal = checker.calculate_lethal_potential()
    assert lethal, (total, note)
    print("OK buffed tailor +6/+6 lethal", total, note)


def test_outfit_tailor_no_friendly_no_buff_face():
    """无其他友方时：裁缝上场失调，不产生场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _hand_tailor(gs, 30, 1, atk=5, hp=5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK tailor alone no face", total)


if __name__ == "__main__":
    test_outfit_tailor_registered()
    test_outfit_tailor_base_buffs_face_attacker()
    test_outfit_tailor_uses_buffed_hand_stats()
    test_outfit_tailor_no_friendly_no_buff_face()
    print("all passed")
