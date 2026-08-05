#!/usr/bin/env python3
"""疲劳审判官仍应跟刀：武器挥击后追加 8 伤（耐久推演不得抹掉跟刀）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.atk = atk
    h.tags.update({
        "DAMAGE": dmg, "RESOURCES": mana, "RESOURCES_USED": used,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "ATK": atk, "479": atk,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", turns=1, exhausted=0, attacks=0, dmg=0):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = dmg
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp, "DAMAGE": dmg,
        "NUM_ATTACKS_THIS_TURN": attacks,
        "EXHAUSTED": exhausted, "NUM_TURNS_IN_PLAY": turns,
    })
    if card_id == "CS3_020":
        m.tags["RUSH"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, cid, atk, dur):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = cid
    w.atk = atk
    w.durability = dur
    w.damage = 0
    w.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk,
        "HEALTH": dur, "DURABILITY": dur, "DAMAGE": 0,
    })
    return w


def _hero_power(gs, eid, pid, cid, cost=1):
    e = gs.get_entity(eid)
    e.cardtype = "HERO_POWER"
    e.controller = pid
    e.zone = "PLAY"
    e.card_id = cid
    e.cost = cost
    e.tags.update({"ZONE": "PLAY", "COST": cost, "EXHAUSTED": 0})
    return e


def test_exhausted_inquisitor_weapon_claws_lethal():
    """
    复盘 2026-08-05：审判官突袭解嘲后已疲劳；武器 2 耐久 + 恶魔之爪。
    应计：场攻 + 武器(+爪) + 跟刀 8 ≥ 对手 22 血。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=8, atk=2)
    _hero(gs, 2, 2, hp=30, dmg=8)  # 22 血
    _hero_power(gs, 50, 1, "HERO_10bp", 1)
    _weapon(gs, 40, 1, "TIME_444", 2, 2)
    _minion(gs, 10, 1, 1, 1, card_id="REV_943t", turns=4)
    _minion(gs, 11, 1, 1, 1, card_id="REV_943t", turns=4)
    _minion(gs, 12, 1, 5, 4, card_id="END_004", turns=2)
    _minion(gs, 13, 1, 6, 5, card_id="TOY_652", turns=2)
    _minion(gs, 14, 1, 8, 8, card_id="CS3_020", turns=1, exhausted=1, attacks=1, dmg=3)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    _, _, lethal = lc.calculate_lethal_potential()
    # 1+1+5+6 + 武器3(含爪) + 跟刀8 = 24
    assert face >= 22, f"expected >=22 with mirror, got {face} note={note}"
    assert lethal, (face, note)
    print("OK exhausted inquisitor + weapon + claws", face, note)


def test_face_hit_buckets_preserves_weapon_durability():
    """打脸分桶不得写回武器耐久，否则二次估值跟刀会丢。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, atk=2)
    _hero(gs, 2, 2, hp=30, dmg=20)
    _weapon(gs, 40, 1, "TIME_444", 2, 1)  # 1 耐久更易复现
    _minion(gs, 14, 1, 8, 8, card_id="CS3_020", turns=1, exhausted=1, attacks=1)

    lc = LethalChecker(gs)
    fs = lc._build_fighters(gs.get_overlay_board(1), 1)
    weapon = next(f for f in fs if f.get("kind") == "weapon")
    assert weapon["durability"] == 1
    a = lc._split_fighter_face(fs)
    assert weapon["durability"] == 1, weapon
    b = lc._split_fighter_face(fs)
    # 两次估值都应含跟刀 8：武器 2 + 跟刀 8 = 10（无其他随从攻击）
    assert a[0] >= 8 and b[0] >= 8, (a, b)
    assert a == b, (a, b)
    print("OK durability preserved + stable mirror", a)


if __name__ == "__main__":
    test_face_hit_buckets_preserves_weapon_durability()
    test_exhausted_inquisitor_weapon_claws_lethal()
