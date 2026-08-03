#!/usr/bin/env python3
"""镂骨恶犬 JAM_004：突袭顺劈应一并清掉相邻嘲讽，再打脸斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, mana=10, hp=30, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _board_minion(gs, eid, pid, atk, hp, *, card_id="CS2_033", taunt=False, pos=1):
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
    m.tags["ZONE_POSITION"] = pos
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    if taunt:
        m.tags["TAUNT"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid
    return m


def _hand_hollow(gs, eid, pid, cost=6):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = "JAM_004"
    m.atk = 3
    m.health = 4
    m.cost = cost
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 3
    m.tags["HEALTH"] = 4
    m.tags["COST"] = cost
    m.tags["RUSH"] = 1
    m.tags["LIFESTEAL"] = 1
    m.tags["ZONE_POSITION"] = 1
    return m


def test_hollow_hound_cleave_three_taunts_lethal():
    """三只 3 血嘲讽并排：恶犬打中间顺劈清场，场上 6 攻打脸斩 6 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=24)  # 6 血
    _board_minion(gs, 10, 1, 6, 6, pos=1)
    _board_minion(gs, 20, 2, 1, 3, taunt=True, card_id="T_L", pos=1)
    _board_minion(gs, 21, 2, 1, 3, taunt=True, card_id="T_M", pos=2)
    _board_minion(gs, 22, 2, 1, 3, taunt=True, card_id="T_R", pos=3)
    _hand_hollow(gs, 30, 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 6, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    _, _, is_lethal = checker.calculate_lethal_potential()
    assert is_lethal, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    assert checker.overlay_red_prompt_ok(), "should prompt lethal"
    print("OK hollow hound cleave three taunts lethal", total, checker.overlay_spell_note())


def test_hollow_hound_cleave_two_taunts_then_face():
    """两只相邻 3 血嘲讽：恶犬打其一顺劈清两只，场攻打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=25)  # 5 血
    _board_minion(gs, 10, 1, 5, 5, pos=1)
    _board_minion(gs, 20, 2, 1, 3, taunt=True, card_id="T_L", pos=1)
    _board_minion(gs, 21, 2, 1, 3, taunt=True, card_id="T_R", pos=2)
    _hand_hollow(gs, 30, 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 5, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    _, _, is_lethal = checker.calculate_lethal_potential()
    assert is_lethal, (total, is_lethal)
    print("OK hollow hound cleave two taunts", total)


if __name__ == "__main__":
    test_hollow_hound_cleave_three_taunts_lethal()
    test_hollow_hound_cleave_two_taunts_then_face()
    print("ALL PASS")
