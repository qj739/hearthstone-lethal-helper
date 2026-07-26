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


if __name__ == "__main__":
    test_truth_seeker_registered()
    test_equipped_stamps_all_paladin_buff()
    test_after_attack_buffs_all_paladins_not_neutral()
    test_face_hits_include_buff_after_weapon_swing()
    test_truth_seeker_lethal_vs_11_hp()
    test_board_face_includes_buff()
    print("ALL PASS")
