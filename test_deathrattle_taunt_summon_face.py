#!/usr/bin/env python3
"""亡语召唤嘲讽：淤泥 / 山岭野熊 / 邪鬼皇后 等场攻模拟。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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


def _face(enemy_cid, enemy_atk, enemy_hp, enemy_taunt, our_minions):
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    for i, (atk, hp) in enumerate(our_minions):
        _minion(gs, 10 + i, 1, atk, hp)
    _minion(gs, 20, 2, enemy_atk, enemy_hp, taunt=enemy_taunt, card_id=enemy_cid)
    return LethalChecker(gs).overlay_board_face_damage()


def test_sludge_three_minions_face():
    """淤泥 3/5 → 1/2 泥浆；6/6+2/2+3/3 解场后 3/3 打脸。"""
    assert _face("FP1_012", 3, 5, True, [(6, 6), (2, 2), (3, 3)]) == 3
    print("OK sludge 3 face")


def test_mountain_bear_blocks_extra_face():
    """山岭野熊 5/6 → 两只 2/4 嘲讽；3 随从不够解完，场攻 0。"""
    assert _face("AV_337", 5, 6, True, [(6, 6), (2, 2), (3, 3)]) == 0
    print("OK mountain bear 0 face")


def test_wretched_queen_blocks_extra_face():
    """邪鬼皇后 4/4 → 两只 4/6 嘲讽；3 随从不够解完，场攻 0。"""
    assert _face("TOY_914", 4, 4, True, [(6, 6), (2, 2), (3, 3)]) == 0
    print("OK wretched queen 0 face")


def test_coilfang_warlord_no_body_taunt():
    """盘牙督军 9/5 本体无嘲讽：可不解督军直接打脸。"""
    assert _face("BT_761", 9, 5, False, [(6, 6), (2, 2)]) == 8
    assert _face("BT_761", 9, 5, False, [(6, 6), (2, 2), (3, 3)]) == 11
    print("OK coilfang warlord skip body")


if __name__ == "__main__":
    test_sludge_three_minions_face()
    test_mountain_bear_blocks_extra_face()
    test_wretched_queen_blocks_extra_face()
    test_coilfang_warlord_no_body_taunt()
    print("all passed")
