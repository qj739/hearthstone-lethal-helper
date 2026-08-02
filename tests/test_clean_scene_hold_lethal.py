#!/usr/bin/env python3
"""回归：拦住他们！+ 净场(已注能) 清嘲后打脸斩杀。

复盘 Power.log 2026-07-29：对手 9 血、两只 3/5 嘲讽旋舞之影；
我方折纸仙鹤 6/3 + 琥珀女祭司 1/4 + 激活的魔像 4/1。
先 JAIL_913 给仙鹤 +5/+5（11/8），再 REV_252t 消灭攻≤6 随从，
仙鹤 11 打脸斩。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import register_arena_season_gap
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0, card_id="HERO_09"):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.card_id = card_id
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["ATK"] = 0
    h.tags["479"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", taunt=False, pos=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.zone_pos = pos
    m.tags["ZONE"] = "PLAY"
    m.tags["ZONE_POSITION"] = pos
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["HEALTH"] = hp
    m.tags["TAUNT"] = 1 if taunt else 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_clean_scene_infused_registered():
    register_arena_season_gap()
    d = get_board_spell_def("REV_252t")
    assert d is not None, "REV_252t 未注册"
    assert d.base_cost == 5
    # 已注能：消灭攻≤6（双方）
    taunts = [
        {"kind": "minion", "atk": 3, "health": 5, "entity_id": 1},
        {"kind": "minion", "atk": 6, "health": 3, "entity_id": 2},
        {"kind": "minion", "atk": 7, "health": 7, "entity_id": 3},
    ]
    fighters = [
        {"kind": "minion", "atk": 1, "health": 4, "entity_id": 10},
        {"kind": "minion", "atk": 11, "health": 8, "entity_id": 11},
    ]
    d.apply(taunts, fighters, mult=1, enemy_shield=False)
    # 死随从会从 taunts 列表移除；7 攻应存活
    assert len(taunts) == 1 and taunts[0]["atk"] == 7 and taunts[0]["health"] == 7
    assert fighters[0]["health"] == 0
    assert fighters[1]["health"] == 8
    print("OK REV_252t destroy_atk_le(6)")


def test_hold_then_clean_lethal_vs_9():
    """拦住他们！→净场→折纸仙鹤 11 打脸，对手 9 血应斩。"""
    register_arena_season_gap()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, hp=30, dmg=21, card_id="HERO_07")  # 9 血

    # 我方：女祭司 1/4、仙鹤 6/3、魔像 4/1
    _minion(gs, 10, 1, 1, 4, card_id="TIME_431", pos=1)
    _minion(gs, 11, 1, 6, 3, card_id="TOY_895", pos=2)
    _minion(gs, 12, 1, 4, 1, card_id="JAIL_883", pos=3)
    # 对手：两只 3/5 嘲讽旋舞之影
    _minion(gs, 20, 2, 3, 5, card_id="REV_372t", taunt=True, pos=1)
    _minion(gs, 21, 2, 3, 5, card_id="REV_372t", taunt=True, pos=2)

    # 预备后拦住他们 3 费 + 净场 5 费
    _hand_spell(gs, 30, 1, "JAIL_913", 3)
    _hand_spell(gs, 31, 1, "REV_252t", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, has = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note()
    assert face >= 9, (face, note, lc.overlay_board_breakdown())
    assert has, (face, total, has, note)
    assert lc.overlay_red_prompt_ok()
    print("OK hold+clean lethal vs 9", face, note)


if __name__ == "__main__":
    test_clean_scene_infused_registered()
    test_hold_then_clean_lethal_vs_9()
    print("ALL PASS")
