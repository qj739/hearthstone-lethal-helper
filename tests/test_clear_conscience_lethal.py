#!/usr/bin/env python3
"""问心无愧 MAW_021：友方随从 +2/+3，应计入斩杀搜索。"""

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


def test_clear_conscience_registered_and_buffs():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=19)
    _minion(gs, 30, 1, 5, 5)
    _hand_spell(gs, 40, 1, "MAW_021", 3)

    assert get_board_spell_def("MAW_021") is not None
    assert any(s.card_id == "MAW_021" for s, _, _ in hand_board_spells(gs, 1, 10))

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 7, f"5+2 buff expected face>=7 got {face}"


def test_clear_conscience_enables_lethal():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=24)
    _minion(gs, 30, 1, 5, 5)
    _hand_spell(gs, 40, 1, "MAW_021", 3)

    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal_potential()
    assert lethal, "5 atk + 问心无愧 +2 = 7 should be lethal vs 6 hp"


def test_clear_conscience_does_not_enable_awakened_sick_face():
    """刚苏醒/召唤失调的高攻随从可被问心无愧点选，但本回合仍不能打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=20)  # 敌 10 血
    ready = _minion(gs, 30, 1, 3, 5, card_id="ready")
    ready.tags["NUM_TURNS_IN_PLAY"] = 2
    sick = _minion(gs, 31, 1, 12, 12, card_id="TOY_647")
    sick.tags["NUM_TURNS_IN_PLAY"] = 0
    sick.tags["DORMANT_AWAKENED_THIS_TURN"] = 1
    sick.tags["EXHAUSTED"] = 1
    _hand_spell(gs, 40, 1, "MAW_021", 3)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    # 仅 3 攻可出手：buff 应落在可攻随从上 → 5；绝不能把 12 攻玛瑟算进脸
    assert face < 10, f"sick Mag must not face; expected face~5 got {face}"
    assert face >= 5, f"ready minion should get +2 buff; got {face}"
    _, _, lethal = lc.calculate_lethal_potential()
    assert not lethal, "should not false-lethal via awakened Magtheridon face"


if __name__ == "__main__":
    test_clear_conscience_registered_and_buffs()
    test_clear_conscience_enables_lethal()
    test_clear_conscience_does_not_enable_awakened_sick_face()
    print("ok")
