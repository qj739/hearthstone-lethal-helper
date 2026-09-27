#!/usr/bin/env python3
"""石头 WW_001t：发掘衍生，1 费对一个敌人造成 3 点伤害。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells


def _hero(gs, eid, pid, *, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.atk = atk
    h.tags["DAMAGE"] = dmg
    h.tags["ATK"] = atk
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1, taunt=False):
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
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    if taunt:
        m.tags["TAUNT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def test_stone_registered():
    assert get_board_spell_def("WW_001t") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _hand_spell(gs, 40, 1, "WW_001t", 1)
    assert any(s.card_id == "WW_001t" for s, _, _ in hand_board_spells(gs, 1, 10))
    print("OK stone registered")


def test_stone_face_lethal():
    """仅石头打脸：对手 3 血应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=1)
    _hero(gs, 2, 2, dmg=27)  # 3 hp
    _hand_spell(gs, 40, 1, "WW_001t", 1)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 3, f"expected >=3 from stone, got {total}"
    assert has_lethal, "stone 3 should lethal vs 3 hp"
    print("OK stone face lethal", total)


def test_stone_finishes_board_lethal_like_log():
    """复现漏斩：场面打脸 8 + 英雄 3 = 11，对手 14 血；石头补 3 才能斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=5, atk=3)
    _hero(gs, 2, 2, dmg=16)  # 14 hp
    _minion(gs, 22, 1, 3, 3, card_id="TIME_614")
    _minion(gs, 23, 1, 1, 1, card_id="TLC_443")
    _minion(gs, 24, 1, 4, 2, card_id="TLC_427")  # 3+1+4+hero3=11
    _hand_spell(gs, 40, 1, "WW_001t", 1)

    lc = LethalChecker(gs)
    _, note, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"board+hero+stone should lethal vs 14: {note}"

    gs2 = GameState()
    gs2.local_player_id = 1
    gs2.opponent_player_id = 2
    gs2.in_game = True
    gs2.active_player_id = 1
    _hero(gs2, 1, 1, mana=5, atk=3)
    _hero(gs2, 2, 2, dmg=16)
    _minion(gs2, 22, 1, 3, 3, card_id="TIME_614")
    _minion(gs2, 23, 1, 1, 1, card_id="TLC_443")
    _minion(gs2, 24, 1, 4, 2, card_id="TLC_427")
    lc2 = LethalChecker(gs2)
    _, _, no_stone = lc2.calculate_lethal_potential()
    assert not no_stone, "without stone 11 face < 14 hp"
    print("OK stone finishes board lethal", note)


if __name__ == "__main__":
    test_stone_registered()
    test_stone_face_lethal()
    test_stone_finishes_board_lethal_like_log()
    print("ALL OK")
