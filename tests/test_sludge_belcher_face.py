#!/usr/bin/env python3
"""淤泥喷射者亡语嘲讽 + 混乱打击场攻用例。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id=""):
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
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"


def test_sludge_belcher_chaos_strike_face():
    """对方 3/5 淤泥，我方 6/6+2/2，手牌混乱打击。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 11, 1, 2, 2)
    _minion(gs, 20, 2, 3, 5, taunt=True, card_id="FP1_012")
    _hand_spell(gs, 30, 1, "CORE_BT_035", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    # 先法混乱打击；6/6 解淤泥，2/2 解亡语 1/2 泥浆，英雄 +2 打脸（6/6 已用完攻击次数）
    assert total == 2, f"expected 2 face, got {total}"
    assert board == 2, f"board face expected 2, got {board}"
    assert spell == 0, f"spell face expected 0, got {spell}"
    assert pure == 0, f"pure board without spell expected 0, got {pure}"
    assert "混乱打击" in note
    print("OK sludge belcher chaos strike", total, note)


if __name__ == "__main__":
    test_sludge_belcher_chaos_strike_face()
    print("all passed")
