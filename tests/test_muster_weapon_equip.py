#!/usr/bin/env python3
"""作战动员 / 正义圣契：装备 1/4 须替换已有武器，不得叠成「武N+英1」。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


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
    h.tags["ATK"] = 0
    h.tags["479"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _weapon(gs, eid, pid, card_id, atk, dur):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = card_id
    w.controller = pid
    w.zone = "PLAY"
    w.atk = atk
    w.health = dur
    w.damage = 0
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["479"] = atk
    w.tags["DURABILITY"] = dur
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
        hero.tags["ATK"] = atk
        hero.tags["479"] = atk
    return w


def _minion(gs, eid, pid, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "M"
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
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


def test_muster_replaces_stronger_weapon_no_hero_buff():
    """已装备 2 攻武器时，作战动员应替换为 1/4，不应再叠英1。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5)
    _weapon(gs, 40, 1, "TOY_810", 2, 1)
    _hand_spell(gs, 30, 1, "CORE_GVG_061", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    buff = checker.overlay_hero_buff_face()
    note = checker.overlay_spell_note() or ""
    # 最优：不打作战动员，保留 5 随从 + 2 武器 = 7
    assert board == 5, (total, board, weapon, buff, note)
    assert weapon == 2, (total, board, weapon, buff, note)
    assert buff == 0, (total, board, weapon, buff, note)
    assert total == 7, (total, board, weapon, buff, note)
    assert "作战动员" not in note, note
    print("OK muster not preferred over stronger weapon", total, note)


def test_muster_equips_when_no_weapon():
    """无武器时作战动员装备 1/4，计入武1而非英1。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "CORE_GVG_061", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    buff = checker.overlay_hero_buff_face()
    note = checker.overlay_spell_note() or ""
    assert board == 0, (total, board, weapon, buff, note)
    assert weapon == 1, (total, board, weapon, buff, note)
    assert buff == 0, (total, board, weapon, buff, note)
    assert total == 1, (total, board, weapon, buff, note)
    assert "作战动员" in note, note
    print("OK muster alone weapon 1", total, note)


def test_opp_turn_muster_no_fake_hero1():
    """对方回合预览：有 2 攻武器时不应出现英1（误把动员当英雄攻）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2  # 对方回合
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5)
    _weapon(gs, 40, 1, "TOY_810", 2, 1)
    _hand_spell(gs, 30, 1, "CORE_GVG_061", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    buff = checker.overlay_hero_buff_face()
    _, board, weapon, _, _ = checker.overlay_board_breakdown()
    assert buff == 0, (total, board, weapon, buff)
    assert weapon == 2, (total, board, weapon, buff)
    assert total == 7, (total, board, weapon, buff)
    print("OK opp-turn preview no英1", total, board, weapon, buff)


if __name__ == "__main__":
    test_muster_replaces_stronger_weapon_no_hero_buff()
    test_muster_equips_when_no_weapon()
    test_opp_turn_muster_no_fake_hero1()
    print("all passed")
