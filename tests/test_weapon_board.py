#!/usr/bin/env python3
"""埃提耶识武器场攻：英雄479未同步时仍应计入武器攻击力"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import (
    INFINITE_ATK,
    hero_weapon_strike_damage,
    hero_can_attack_with_weapon,
    hero_weapon_can_face,
)


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


def test_hand_weapon_after_hero_attacked_no_extra_swing():
    """英雄本回合已攻击后，打出手牌武器不应再计一次挥击。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    hero.tags["RESOURCES"] = 10
    hero.tags["RESOURCES_USED"] = 0
    hero.tags["NUM_ATTACKS_THIS_TURN"] = 1
    hero.tags["EXHAUSTED"] = 1
    _hero(gs, 2, 2)
    _hand_weapon(gs, 50, 1, "ETC_423", 3, atk=3, dur=2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, _ = checker.overlay_board_breakdown()
    assert weapon_board == 0, (total, weapon_board, checker.overlay_spell_note())
    assert total == 0, (total, minion_board, weapon_board, spell, checker.overlay_spell_note())
    print("OK hand weapon after hero attacked = 0", total)


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
    # 5 随从 + 3 武器 + 5 回合结束；ET 进 total，不并入 minion_bd
    assert face >= 13, f"expected >=13 (5+3+5 et), got {face} bd={minion_bd}/{weapon_bd}/{spell}"
    assert minion_bd >= 5, minion_bd
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


def test_hand_of_infinity_cannot_face():
    """无穷之手：无穷攻可解场，但场攻/斩杀不得把武器伤计入打脸。"""
    from hdt_python.spell_board import apply_spell_sequence
    from hdt_python.weapon_board import get_weapon_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 30
    _weapon(gs, 40, 1, card_id="END_012", atk=INFINITE_ATK, dur=2)
    hero.tags["CANNOT_ATTACK_HEROES"] = 1
    hero.tags["ATK"] = INFINITE_ATK
    hero.tags["479"] = INFINITE_ATK

    assert not hero_weapon_can_face(hero, gs.get_weapon(1))
    board = gs.get_overlay_board(1)
    assert board.hero_damage == 0, board.hero_damage

    checker = LethalChecker(gs)
    fighters = checker._build_fighters(board, 1)
    weapon_f = next(f for f in fighters if f.get("kind") == "weapon")
    assert weapon_f.get("can_face") is False
    assert weapon_f.get("atk") == INFINITE_ATK
    face = checker.overlay_board_face_damage()
    _, _, weapon_bd, _, _ = checker.overlay_board_breakdown()
    assert weapon_bd == 0, weapon_bd
    assert face == 0, face

    # 有嘲讽时：武器可参与清场，但清完后仍不能打脸
    _minion(gs, 20, 2, 2, 5)
    gs.get_entity(20).tags["TAUNT"] = 1
    checker2 = LethalChecker(gs)
    face2 = checker2.overlay_board_face_damage()
    _, _, weapon_bd2, _, _ = checker2.overlay_board_breakdown()
    assert weapon_bd2 == 0, weapon_bd2
    assert face2 == 0, face2

    # 手牌打出模拟：同样 can_face=False
    defn = get_weapon_def("END_012")
    assert defn is not None
    fs: list = []
    apply_spell_sequence([], fs, [(defn, 3, None)])
    w = next(f for f in fs if f.get("kind") == "weapon")
    assert w.get("can_face") is False
    assert w.get("atk") == INFINITE_ATK
    print("OK hand of infinity cannot face")


def test_split_fighter_face_divine_shield_once():
    """对手英雄圣盾只破一次：随从+武器合并后扣最小一击，不能分项各扣一次。"""
    fighters = [
        {"kind": "minion", "atk": 7, "health": 7, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "atk": 3, "health": 2, "attacks_left": 1, "can_face": True},
        {
            "kind": "weapon", "atk": 2, "health": 30, "attacks_left": 1,
            "can_face": True, "durability": 2,
        },
    ]
    minion, weapon, hero_buff, hp = LethalChecker._split_fighter_face(
        fighters, defender_shield=True,
    )
    # 最优破盾浪费 2，剩余 7+3=10 随从；不可出现随从 7 且武器 0（分项双扣）
    assert minion + weapon + hero_buff + hp == 10, (minion, weapon, hero_buff, hp)
    assert weapon == 0 and minion == 10, (minion, weapon)
    print("OK split fighter face divine shield once", minion, weapon)


def test_abusive_sergeant_lethal_through_hero_divine_shield():
    """叫嚣的中士：先战吼+2 再打脸；对手英雄圣盾时仍应用最小一击破盾。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=2)
    opp = _hero(gs, 2, 2)
    opp.health = 11
    opp.tags["DIVINE_SHIELD"] = 1
    _minion(gs, 10, 1, 7, 7)
    gs.get_entity(10).card_id = "GVG_079"
    _minion(gs, 11, 1, 3, 2)
    gs.get_entity(11).card_id = "TOY_811"
    gs.get_entity(11).tags["RUSH"] = 1
    _weapon(gs, 40, 1, card_id="TOY_810", atk=2, dur=3)
    m = gs.get_entity(50)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "HAND"
    m.card_id = "CORE_CS2_188"
    m.atk = 1
    m.health = 5
    m.cost = 1
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 1
    m.tags["HEALTH"] = 5
    m.tags["COST"] = 1
    m.tags["TAUNT"] = 1

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note() or ""
    assert face >= 11, f"expected lethal face>=11, got {face} note={note}"
    assert "叫嚣的中士" in note, note
    assert getattr(checker, "_overlay_best_order", "") == "spell_first", (
        checker._overlay_best_order
    )
    print("OK abusive sergeant lethal through hero DS", face, note)


def test_hand_lights_justice_buffed_plus_fireball_lethal():
    """手牌圣光的正义（BUFF 成 2 攻）+ 火球：对手 7 血时应在装备前识别斩杀。

    复现 2026-07-30 对局：未注册 CS2_091 时只计火球 6，装备后才亮斩。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    hero.tags["RESOURCES"] = 10
    hero.tags["RESOURCES_USED"] = 5  # 剩 5 费：火球 4 + 武器 1
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.damage = 23  # 7 血
    _hand_spell(gs, 30, 1, "CORE_CS2_029", 4)
    _hand_weapon(gs, 50, 1, "CS2_091", 1, atk=2, dur=5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note() or ""
    assert weapon_board == 2, (total, weapon_board, spell, note)
    assert spell == 6, (total, weapon_board, spell, note)
    assert total >= 8, (total, minion_board, weapon_board, spell, note)
    assert "圣光的正义" in note or "CS2_091" in note, note
    assert "火球" in note, note
    print("OK lights justice+fireball lethal before equip", total, note)


def test_unregistered_hand_weapon_uses_live_stats():
    """未收录 card_id 的手牌武器仍按实体攻/耐久计入挥击。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    hero.tags["RESOURCES"] = 2
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 2, 2)
    _hand_weapon(gs, 50, 1, "ZZ_TEST_WEAPON_X", 1, atk=4, dur=2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, weapon_board, _, _ = checker.overlay_board_breakdown()
    assert weapon_board == 4, (total, weapon_board, checker.overlay_spell_note())
    assert total == 4, (total, checker.overlay_spell_note())
    print("OK unregistered hand weapon live stats", total)


def test_hand_horn_of_the_windlord_windfury_lethal():
    """手牌风领主的管号：风怒应计 3+3=6，装备前即可识别斩杀。

    复现 2026-07-31 对局：装备前场攻不足，装备后才按实体风怒双挥亮斩。
    """
    from hdt_python.weapon_board import get_weapon_def

    assert get_weapon_def("JAM_011") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    hero.tags["RESOURCES"] = 6
    hero.tags["RESOURCES_USED"] = 0
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.damage = 24  # 6 血
    w = _hand_weapon(gs, 50, 1, "JAM_011", 6, atk=3, dur=4)
    w.tags["WINDFURY"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note() or ""
    assert weapon_board == 6, (total, weapon_board, spell, note)
    assert total >= 6, (total, minion_board, weapon_board, spell, note)
    assert "风领主的管号" in note, note
    print("OK horn of windlord hand windfury lethal", total, note)


def test_default_hand_weapon_reads_windfury_tag():
    """未收录但带 WINDFURY 标签的手牌武器应按双挥计伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk479=0)
    hero.tags["RESOURCES"] = 2
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 2, 2)
    w = _hand_weapon(gs, 50, 1, "ZZ_TEST_WF_WEAPON", 1, atk=2, dur=3)
    w.tags["WINDFURY"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, weapon_board, _, _ = checker.overlay_board_breakdown()
    assert weapon_board == 4, (total, weapon_board, checker.overlay_spell_note())
    print("OK default hand weapon windfury tag", total)


if __name__ == "__main__":
    test_atiesh_weapon_strike_when_hero_479_zero()
    test_atiesh_weapon_in_overlay_with_moonwell()
    test_equipped_and_hand_weapon_no_double_count()
    test_hand_weapon_after_hero_attacked_no_extra_swing()
    test_hand_arcanite_ripper_with_minion_no_taunt()
    test_dk_ghoul_on_board_counts_as_skill_not_minion()
    test_opp_turn_hammer_muncher_board_floor()
    test_equipped_hammer_stamps_after_attack_buff()
    test_hand_of_infinity_cannot_face()
    test_split_fighter_face_divine_shield_once()
    test_abusive_sergeant_lethal_through_hero_divine_shield()
    test_hand_lights_justice_buffed_plus_fireball_lethal()
    test_unregistered_hand_weapon_uses_live_stats()
    test_hand_horn_of_the_windlord_windfury_lethal()
    test_default_hand_weapon_reads_windfury_tag()
    print("all passed")
