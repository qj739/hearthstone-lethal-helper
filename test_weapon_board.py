#!/usr/bin/env python3
"""埃提耶识武器场攻：英雄479未同步时仍应计入武器攻击力"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import hero_weapon_strike_damage, hero_can_attack_with_weapon


def _hero(gs, eid, pid, *, atk479=None):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = 10
    h.tags["RESOURCES_USED"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    if atk479 is not None:
        h.tags["479"] = atk479
        h.atk = atk479
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "M1"
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


def _weapon(gs, eid, pid, card_id="TIME_890t", atk=1, dur=2):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = card_id
    w.controller = pid
    w.zone = "PLAY"
    w.atk = atk
    w.health = dur
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["479"] = atk
    w.tags["DURABILITY"] = dur
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
    return w


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    return s


def test_atiesh_weapon_strike_when_hero_479_zero():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    weapon = _weapon(gs, 40, 1)
    assert hero_weapon_strike_damage(hero, weapon) == 1
    assert hero_can_attack_with_weapon(hero, weapon, True)
    board = gs.get_overlay_board(1)
    assert board.hero_damage == 1, f"expected hero_damage=1, got {board.hero_damage}"
    assert gs.weapon_attack_damage(1) == 1
    print("OK atiesh strike hero479=0", board.hero_damage)


def test_atiesh_weapon_in_overlay_with_moonwell():
    """8攻随从 + 埃提耶识 + 月亮井：7/8/8 或 8/1/8 取决于随从；至少含武器+法术。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _minion(gs, 10, 1, 8, 3)
    _weapon(gs, 40, 1)
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, _ = checker.overlay_board_breakdown()
    w_atk = gs.get_overlay_board(1).hero_damage
    assert w_atk == 1, f"weapon face expected 1, got {w_atk}"
    assert spell == 8, f"moonwell with atiesh expected 8 spell, got {spell}"
    assert weapon_board == 1, f"weapon breakdown expected 1, got {weapon_board}"
    assert total == minion_board + weapon_board + spell
    assert total >= 8 + 1 + 8 - 1, f"expected at least 16 with weapon, got {total} minion={minion_board} weapon={weapon_board} spell={spell}"
    print("OK atiesh overlay minion+weapon+moonwell", total, minion_board, weapon_board, spell, w_atk)


def test_equipped_and_hand_weapon_no_double_count():
    """已装备武器 + 手牌武器：只计当前装备或替换后的新武器，不能两把叠加。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _weapon(gs, 40, 1, card_id="CS2_106", atk=3, dur=2)
    # 手牌 5/2 武器（竞技场常见注册）
    hand_w = gs.get_entity(50)
    hand_w.cardtype = "WEAPON"
    hand_w.controller = 1
    hand_w.zone = "HAND"
    hand_w.card_id = "BAR_844"
    hand_w.cost = 3
    hand_w.atk = 3
    hand_w.health = 4
    hand_w.tags["ZONE"] = "HAND"
    hand_w.tags["ATK"] = 3
    hand_w.tags["479"] = 3

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, _, _ = checker.overlay_board_breakdown()
    # 无法术最优：仅用已装备的 3 攻武器
    assert weapon_board == 3, (total, minion_board, weapon_board, checker.overlay_spell_note())
    assert total == 3, (total, checker.overlay_spell_note())
    print("OK equipped only without playing hand weapon", total, weapon_board)


def _hand_weapon(gs, eid, pid, card_id, cost, *, atk=3, dur=2):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "HAND"
    w.card_id = card_id
    w.cost = cost
    w.atk = atk
    w.health = dur
    w.tags["ZONE"] = "HAND"
    w.tags["COST"] = cost
    w.tags["ATK"] = atk
    w.tags["479"] = atk
    w.tags["DURABILITY"] = dur
    return w


def test_hand_arcanite_ripper_with_minion_no_taunt():
    """3 费挂奥金利斧 + 场面 2/1：随从 2 + 武器 3 = 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1)
    hero.tags["RESOURCES"] = 3
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 1)
    _hand_weapon(gs, 50, 1, "ETC_423", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, _ = checker.overlay_board_breakdown()
    assert total == 5, (total, minion_board, weapon_board, spell, checker.overlay_spell_note())
    assert minion_board == 2, minion_board
    assert weapon_board == 3, weapon_board
    assert spell == 0, spell
    assert "奥金利斧" in checker.overlay_spell_note()
    print("OK hand arcanite ripper 2/1 no taunt", total, minion_board, weapon_board)


def test_dk_ghoul_on_board_counts_as_skill_not_minion():
    """已用技能、食尸鬼在场上：计技不计随（技能已耗尽不再模拟召唤）。"""
    from test_spell_board import _hero, _hero_power, _minion

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    g = _minion(gs, 115, 1, 1, 1, card_id="HERO_11bpt", charge=True)
    g.tags["NUM_TURNS_IN_PLAY"] = 0
    g.tags["ATK"] = 1
    g.tags["479"] = 1
    _hero_power(gs, 50, 1, "HERO_11bp", 2, exhausted=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp_skill = checker.overlay_board_breakdown()
    assert total == 1, (total, minion_board, weapon_board, spell, hp_skill)
    assert minion_board == 0 and hp_skill == 1, (
        minion_board, hp_skill, checker.overlay_spell_note()
    )
    print("OK dk ghoul on board as skill", total, minion_board, hp_skill)


def test_opp_turn_hammer_muncher_board_floor():
    """对方回合：已装备敲狼锤 + 嚼嚼怪，overlay 应含下回合攻击与回合结束。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 6)
    gs.get_entity(10).card_id = "RLK_720"
    _weapon(gs, 40, 1, card_id="DMF_705", atk=3, dur=2)

    checker = LethalChecker(gs)
    assert checker.is_opponent_turn()
    face = checker.overlay_board_face_damage()
    pure, minion_bd, weapon_bd, spell, hp = checker.overlay_board_breakdown()
    assert weapon_bd == 3, weapon_bd
    assert face >= 13, f"expected >=13 (5+3+5 et), got {face} bd={minion_bd}/{weapon_bd}/{spell}"
    assert minion_bd >= 10, minion_bd
    print("OK opp turn hammer+muncher", face, pure, minion_bd, weapon_bd)


def test_equipped_hammer_stamps_after_attack_buff():
    """已装备的敲狼锤应挂载攻击后 +1/+1 元数据（与手牌打出一致）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _minion(gs, 10, 1, 2, 2)
    _weapon(gs, 40, 1, card_id="DMF_705", atk=3, dur=2)

    checker = LethalChecker(gs)
    fighters = checker._build_fighters(gs.get_overlay_board(1), 1)
    weapon_f = next(f for f in fighters if f.get("kind") == "weapon")
    assert weapon_f.get("card_id") == "DMF_705"
    assert weapon_f.get("buff_friendly_stats_after") == (1, 1), weapon_f
    print("OK equipped hammer after-attack meta", weapon_f.get("buff_friendly_stats_after"))


if __name__ == "__main__":
    test_atiesh_weapon_strike_when_hero_479_zero()
    test_atiesh_weapon_in_overlay_with_moonwell()
    test_equipped_and_hand_weapon_no_double_count()
    test_hand_arcanite_ripper_with_minion_no_taunt()
    test_dk_ghoul_on_board_counts_as_skill_not_minion()
    test_opp_turn_hammer_muncher_board_floor()
    test_equipped_hammer_stamps_after_attack_buff()
    print("all passed")
