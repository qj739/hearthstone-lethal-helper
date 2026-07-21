#!/usr/bin/env python3
"""侦探服 JAIL_447t：友方随从 +4/+4 并赋予突袭，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells


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


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1):
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


def test_detectives_clothes_registered():
    assert get_board_spell_def("JAIL_447t") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _hand_spell(gs, 40, 1, "JAIL_447t", 4)
    assert any(s.card_id == "JAIL_447t" for s, _, _ in hand_board_spells(gs, 1, 10))
    print("OK detectives clothes registered")


def test_detectives_clothes_buff_face_lethal():
    """可攻击 2 攻 + 侦探服 +4 = 6，对手 6 血应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=24)  # 6 hp
    _minion(gs, 10, 1, 2, 3, turns=1)
    _hand_spell(gs, 40, 1, "JAIL_447t", 4)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 6, f"expected >=6 face after clothes, got {total}"
    assert has_lethal, "2+4 clothes should lethal vs 6 hp"
    print("OK detectives clothes face lethal", total)


def test_detectives_clothes_rush_clears_taunt_not_face_on_sick():
    """失调随从得突袭：可解嘲讽，本回合仍不能打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=25)  # 5 hp
    sick = _minion(gs, 10, 1, 5, 5, turns=0)
    sick.tags["EXHAUSTED"] = 1
    sick.tags["JUST_PLAYED"] = 1
    taunt = _minion(gs, 20, 2, 1, 4, turns=1)
    taunt.tags["TAUNT"] = 1
    _hand_spell(gs, 40, 1, "JAIL_447t", 4)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    # 5+4=9 解 4 血嘲讽溢出 5，但突袭不能打脸 → 打脸应为 0（或仅溢出若实现溢出）
    # 突袭攻击嘲讽：溢出打脸规则因卡而异；本引擎突袭 can_face=False，溢出通常不计脸
    assert total == 0, f"sick+rush should not face, got {total}"
    print("OK detectives clothes rush no face on sick", total)


if __name__ == "__main__":
    test_detectives_clothes_registered()
    test_detectives_clothes_buff_face_lethal()
    test_detectives_clothes_rush_clears_taunt_not_face_on_sick()
    print("all passed")
