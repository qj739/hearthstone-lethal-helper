#!/usr/bin/env python3
"""求真之锤 JAIL_329：英雄攻击后，全体友方圣骑士随从 +2/+2。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.weapon_board import get_weapon_def
from hdt_python.weapon_p0 import apply_after_attack_friendly_buffs


def _hero(gs, eid, pid, *, atk479=None, hp=30, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
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


def _minion(gs, eid, pid, atk, hp, *, card_id="CS2_101t", paladin=True):
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
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    if paladin:
        m.tags["CLASS"] = "PALADIN"
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, card_id="JAIL_329", atk=3, dur=3):
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


def test_truth_seeker_registered():
    defn = get_weapon_def("JAIL_329")
    assert defn is not None, "JAIL_329 should be registered"
    print("OK JAIL_329 registered", defn.name)


def test_equipped_stamps_all_paladin_buff():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _weapon(gs, 40, 1)

    checker = LethalChecker(gs)
    fighters = checker._build_fighters(gs.get_overlay_board(1), 1)
    weapon_f = next(f for f in fighters if f.get("kind") == "weapon")
    assert weapon_f.get("buff_all_paladin_stats_after") == (2, 2), weapon_f
    pal = next(f for f in fighters if f.get("kind") == "minion")
    assert pal.get("paladin") is True, pal
    print("OK equipped Truth Seeker meta", weapon_f.get("buff_all_paladin_stats_after"))


def test_after_attack_buffs_all_paladins_not_neutral():
    fighters = [
        {
            "kind": "weapon",
            "atk": 3,
            "health": 30,
            "attacks_left": 1,
            "durability": 3,
            "buff_all_paladin_stats_after": (2, 2),
        },
        {
            "kind": "minion",
            "card_id": "CS2_101t",
            "atk": 1,
            "health": 1,
            "attacks_left": 1,
            "can_face": True,
            "paladin": True,
        },
        {
            "kind": "minion",
            "card_id": "CS2_101t",
            "atk": 2,
            "health": 2,
            "attacks_left": 1,
            "can_face": True,
            "paladin": True,
        },
        {
            "kind": "minion",
            "card_id": "EX1_116",
            "atk": 6,
            "health": 5,
            "attacks_left": 1,
            "can_face": True,
            "paladin": False,
        },
    ]
    apply_after_attack_friendly_buffs(fighters[0], fighters)
    assert fighters[1]["atk"] == 3 and fighters[1]["health"] == 3
    assert fighters[2]["atk"] == 4 and fighters[2]["health"] == 4
    assert fighters[3]["atk"] == 6 and fighters[3]["health"] == 5
    print("OK all paladin buff, neutral untouched")


def test_face_hits_include_buff_after_weapon_swing():
    """无嘲讽：先挥锤再随从打脸，随从应吃到 +2 攻。"""
    fighters = [
        {
            "kind": "weapon",
            "atk": 3,
            "health": 30,
            "attacks_left": 1,
            "durability": 3,
            "can_face": True,
            "buff_all_paladin_stats_after": (2, 2),
        },
        {
            "kind": "minion",
            "atk": 2,
            "health": 2,
            "attacks_left": 1,
            "can_face": True,
            "paladin": True,
        },
        {
            "kind": "minion",
            "atk": 2,
            "health": 2,
            "attacks_left": 1,
            "can_face": True,
            "paladin": True,
        },
    ]
    # 3 武器 + (2+2)*2 随从 = 11；若不 buff 则仅 7
    dmg = LethalChecker._fighters_face_damage(fighters)
    assert dmg == 11, dmg
    assert fighters[1]["atk"] == 2
    print("OK face damage with Truth Seeker buff", dmg)


def test_truth_seeker_lethal_vs_11_hp():
    """场攻 2+2+武器3=7，buff 后 4+4+3=11，应斩 11 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2, hp=30, dmg=19)  # 11 血
    _minion(gs, 10, 1, 2, 2)
    _minion(gs, 11, 1, 2, 2)
    _weapon(gs, 40, 1)

    checker = LethalChecker(gs)
    total, _, is_lethal = checker.calculate_lethal_potential()
    assert total >= 11, total
    assert is_lethal, (total, is_lethal)
    print("OK Truth Seeker lethal vs 11 HP", total)


def test_board_face_includes_buff():
    """BoardView.face 与 fighters 打脸一致计入 buff。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _minion(gs, 11, 1, 2, 2)
    _weapon(gs, 40, 1)

    board = gs.get_overlay_board(1)
    face = board.face_attack_damage_no_taunt()
    assert face == 11, face
    print("OK board face with buff", face)


def test_zero_atk_paladin_gets_truth_seeker_buff_face():
    """0 攻圣骑（点唱机图腾）挥锤后应变 2 攻并计入打脸。

    场面：2 攻随从 + 0 攻图腾 + 求真之锤。
    正确：武3 + (2+2) + (0+2) = 9；漏算图腾则为 7。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    _hero(gs, 2, 2, hp=30, dmg=21)  # 9 血
    _minion(gs, 10, 1, 2, 2, card_id="TIME_015")
    _minion(gs, 11, 1, 0, 4, card_id="JAM_010")  # 点唱机图腾
    _weapon(gs, 40, 1)

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    assert face >= 9, (face, getattr(checker, "_overlay_spell_note", ""))
    assert checker.overlay_red_prompt_ok(), face
    board = gs.get_overlay_board(1)
    assert board.face_attack_damage_no_taunt() >= 9
    print("OK zero-atk totem Truth Seeker face", face)


def _hand_weapon(gs, eid, pid, card_id="JAIL_329", atk=3, dur=3, cost=7):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = card_id
    w.controller = pid
    w.zone = "HAND"
    w.atk = atk
    w.health = dur
    w.tags["ZONE"] = "HAND"
    w.tags["ATK"] = atk
    w.tags["479"] = atk
    w.tags["DURABILITY"] = dur
    w.tags["COST"] = cost
    w.tags["ZONE_POSITION"] = 1
    return w


def test_hand_truth_seeker_lethal_before_equip():
    """求真之锤在手牌时就应识别斩杀（装备→挥锤→圣骑+2），无需先装备。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    hero = gs.get_entity(1)
    hero.tags["RESOURCES"] = 10
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 2, 2, hp=30, dmg=19)  # 11 血
    _minion(gs, 10, 1, 2, 2)
    _minion(gs, 11, 1, 2, 2)
    _hand_weapon(gs, 40, 1)

    checker = LethalChecker(gs)
    # 搜索路径经 _face_parts_from_fighters；修复前只有 7（漏 buff）
    fs = checker._build_fighters(gs.get_overlay_board(1), 1)
    from hdt_python.spell_board import apply_spell_sequence
    from hdt_python.weapon_board import get_weapon_def
    from copy import deepcopy

    card = gs.get_entity(40)
    defn = get_weapon_def("JAIL_329")
    assert defn is not None
    fs2 = deepcopy(fs)
    apply_spell_sequence(
        [], fs2, [(defn, 7, card)], spell_mult=1, enemy_shield=False,
        gs=gs, player_id=1, mana_budget=10,
    )
    parts = checker._face_parts_from_fighters(fs2, 0, 0, False)
    assert parts[0] >= 11, parts
    assert parts[0] == LethalChecker._fighters_face_damage(fs2), (
        parts, LethalChecker._fighters_face_damage(fs2),
    )

    total, _, is_lethal = checker.calculate_lethal_potential()
    assert total >= 11, total
    assert is_lethal, (total, is_lethal)
    print("OK hand Truth Seeker lethal before equip", total)


def test_frozen_hero_no_truth_seeker_buff_current_or_next_turn():
    """英雄冰冻时不能挥锤：本回合与对方回合下回合预览都不得计入圣骑 +2/+2。"""
    from copy import deepcopy
    from hdt_python.spell_board import apply_spell_sequence
    from hdt_python.weapon_board import get_weapon_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, atk479=0)
    hero = gs.get_entity(1)
    hero.tags["FROZEN"] = 1
    hero.tags["RESOURCES"] = 10
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 2, 2, hp=30, dmg=19)  # 11 血；无 buff 时场攻仅 4，不能斩
    _minion(gs, 10, 1, 2, 2)
    _minion(gs, 11, 1, 2, 2)
    _hand_weapon(gs, 40, 1)

    checker = LethalChecker(gs)
    fs = checker._build_fighters(gs.get_overlay_board(1), 1)
    assert not any(f.get("kind") == "weapon" for f in fs), fs
    card = gs.get_entity(40)
    defn = get_weapon_def("JAIL_329")
    assert defn is not None

    for next_turn in (False, True):
        fs2 = deepcopy(fs)
        apply_spell_sequence(
            [], fs2, [(defn, 7, card)], spell_mult=1, enemy_shield=False,
            gs=gs, player_id=1, mana_budget=10, next_turn_preview=next_turn,
        )
        weapon = next(f for f in fs2 if f.get("kind") == "weapon")
        assert weapon.get("attacks_left", 0) == 0, (next_turn, weapon)
        face = LethalChecker._fighters_face_damage(fs2)
        assert face == 4, (next_turn, face, fs2)
        # 圣骑未被假 buff
        pals = [f for f in fs2 if f.get("kind") == "minion"]
        assert all(f["atk"] == 2 for f in pals), (next_turn, pals)

    total, _, is_lethal = checker.calculate_lethal_potential()
    assert total < 11, total
    assert not is_lethal, (total, is_lethal)

    # 对方回合下回合预览：仍冰冻则不能把求真之锤 buff 算进 Overlay
    gs.active_player_id = 2
    assert checker.is_opponent_turn()
    total2, _, is_lethal2 = checker.calculate_lethal_potential()
    assert total2 < 11, total2
    assert not is_lethal2, (total2, is_lethal2)
    face_ov = checker.overlay_board_face_damage()
    assert face_ov < 11, face_ov
    print("OK frozen hero skips Truth Seeker buff", total, total2, face_ov)


if __name__ == "__main__":
    test_truth_seeker_registered()
    test_equipped_stamps_all_paladin_buff()
    test_after_attack_buffs_all_paladins_not_neutral()
    test_face_hits_include_buff_after_weapon_swing()
    test_truth_seeker_lethal_vs_11_hp()
    test_board_face_includes_buff()
    test_zero_atk_paladin_gets_truth_seeker_buff_face()
    test_hand_truth_seeker_lethal_before_equip()
    test_frozen_hero_no_truth_seeker_buff_current_or_next_turn()
    print("ALL PASS")
