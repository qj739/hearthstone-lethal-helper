#!/usr/bin/env python3
"""不可打脸武器应优先清嘲；暗弦术+拦住他们！回合开始应能斩。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import register_arena_season_gap
import hdt_python.arena_season_bulk as asb
from hdt_python.combat_sim import find_best_taunt_clear_face, project_board_face_after_spell
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import BOARD_CLEAR_SPELLS


def _reregister_etc():
    asb._BULK_DONE = False
    asb._REGISTERED_LOG.clear()
    BOARD_CLEAR_SPELLS.pop("ETC_305", None)
    register_arena_season_gap()


def _hero(gs, eid, pid, *, hp=30, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = 0
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id="", shield=False):
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
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    if taunt:
        m.tags["TAUNT"] = 1
    if shield:
        m.tags["DIVINE_SHIELD"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, atk, dura, *, card_id="", can_attack_hero=False):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.durability = dura
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["DURABILITY"] = dura
    w.tags["NUM_ATTACKS_THIS_TURN"] = 0
    if not can_attack_hero:
        # 部分武器/效果不能打脸：用 tags 模拟（与实战 SW_314 一致由 can_attack 层处理）
        w.tags["CANT_ATTACK_HEROES"] = 1
    gs.weapon_entity_ids = getattr(gs, "weapon_entity_ids", {})
    gs.weapon_entity_ids[pid] = eid
    return w


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


def test_cant_face_weapon_preferred_over_clay():
    """4 攻不可打脸武器应一击 4 血嘲讽，保留可打脸黏土。"""
    fighters = [
        {"kind": "minion", "card_id": "BIG", "atk": 7, "health": 10,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "minion", "card_id": "SMALL", "atk": 2, "health": 1,
         "attacks_left": 1, "can_face": True, "shield": True},
        {"kind": "minion", "card_id": "CLAY", "atk": 4, "health": 1,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "minion", "card_id": "CLAY2", "atk": 4, "health": 4,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "weapon", "card_id": "SW_314", "atk": 4, "health": 30,
         "durability": 1, "attacks_left": 1, "can_face": False, "shield": False},
    ]
    taunts = [
        {"kind": "minion", "card_id": "T4", "atk": 3, "health": 4,
         "taunt": True, "shield": False},
        {"kind": "minion", "card_id": "T1", "atk": 1, "health": 1,
         "taunt": True, "shield": False},
    ]
    face = find_best_taunt_clear_face(fighters, taunts, False)
    # 武器换 4 血 + 2 攻换 1 血，打脸 7+4+4=15（勿用 4/4 黏土换嘲讽）
    assert face == 15, face


def test_darkchord_hold_turn_start_lethal():
    """复盘：三嘲讽 19 血，暗弦术拆 5 血嘲 + 拦住他们！+ 不可打脸武器清嘲 → 斩。"""
    _reregister_etc()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, hp=19)

    _minion(gs, 10, 1, 7, 10, card_id="END_036")
    _minion(gs, 11, 1, 2, 1, card_id="TIME_015", shield=True)
    _minion(gs, 12, 1, 4, 1, card_id="TOY_380t2")
    _minion(gs, 13, 1, 4, 4, card_id="TOY_380t2")
    _weapon(gs, 14, 1, 4, 1, card_id="SW_314", can_attack_hero=False)

    _minion(gs, 20, 2, 3, 4, taunt=True, card_id="CORE_UNG_084")
    _minion(gs, 21, 2, 1, 1, taunt=True, card_id="CS2_101t2")
    _minion(gs, 22, 2, 3, 5, taunt=True, card_id="TIME_700t")

    _hand_spell(gs, 30, 1, "ETC_305", 3)
    _hand_spell(gs, 31, 1, "JAIL_913", 3)

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    assert face >= 19, (face, note)
    assert "暗弦术" in note and "拦住他们" in note, note
    total, _, lethal = LethalChecker(gs).calculate_lethal_potential()
    assert lethal, (total, face, note)


def test_destroy_weak_prefers_high_taunt_for_weapon_oneshot():
    """暗弦术应按清嘲后打脸选目标：拆 5 血嘲，留给武器一击 4 血嘲。"""
    _reregister_etc()
    from copy import deepcopy
    from hdt_python.spell_board import get_board_spell_def

    fighters = [
        {"kind": "minion", "entity_id": 1, "card_id": "END_036", "atk": 7, "health": 10,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "minion", "entity_id": 2, "card_id": "CLAY", "atk": 4, "health": 4,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "weapon", "entity_id": 3, "card_id": "SW_314", "atk": 4, "health": 30,
         "durability": 1, "attacks_left": 1, "can_face": False, "shield": False},
    ]
    enemy = [
        {"kind": "minion", "entity_id": 10, "card_id": "CORE_UNG_084",
         "atk": 3, "health": 4, "taunt": True, "shield": False},
        {"kind": "minion", "entity_id": 11, "card_id": "CS2_101t2",
         "atk": 1, "health": 1, "taunt": True, "shield": False},
        {"kind": "minion", "entity_id": 12, "card_id": "TIME_700t",
         "atk": 3, "health": 5, "taunt": True, "shield": False},
    ]
    defn = get_board_spell_def("ETC_305")
    assert defn is not None
    e2 = deepcopy(enemy)
    f2 = deepcopy(fighters)
    defn.apply(e2, f2, mult=1, enemy_shield=False)
    alive = {m.get("card_id") for m in e2 if int(m.get("health") or 0) > 0}
    assert "TIME_700t" not in alive, alive
    assert "CORE_UNG_084" in alive, alive
    face = project_board_face_after_spell(e2, f2, False)
    # 武器清 4 血嘲后剩大随从打脸
    assert face >= 7, face


if __name__ == "__main__":
    test_cant_face_weapon_preferred_over_clay()
    test_destroy_weak_prefers_high_taunt_for_weapon_oneshot()
    test_darkchord_hold_turn_start_lethal()
    print("ok")
