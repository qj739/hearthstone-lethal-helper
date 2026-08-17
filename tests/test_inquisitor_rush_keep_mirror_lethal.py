#!/usr/bin/env python3
"""无嘲讽时审判官突袭不得去撞高攻怪送死，应保留跟刀打脸。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.combat_sim import exhaust_rush_on_enemy_minions, fighters_face_damage
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.rush_board import get_rush_def
from hdt_python.spell_board import apply_spell_sequence_with_meta


def _hero(gs, eid, pid, *, hp=30, mana=10, used=0, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = 0
    h.atk = atk
    h.tags.update({
        "RESOURCES": mana, "RESOURCES_USED": used,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "ATK": atk, "479": atk,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", turns=2, rush=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": hp,
        "NUM_TURNS_IN_PLAY": turns, "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0,
    })
    if rush:
        m.tags["RUSH"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, atk, dura, card_id="W"):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.durability = dura
    w.tags.update({
        "ZONE": "PLAY", "ATK": atk, "DURABILITY": dura, "HEALTH": dura,
        "NUM_ATTACKS_THIS_TURN": 0,
    })
    gs.weapon_entity_ids = getattr(gs, "weapon_entity_ids", {})
    gs.weapon_entity_ids[pid] = eid
    return w


def _hand_rush(gs, eid, pid, card_id, atk, hp, cost):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.cost = cost
    m.tags.update({
        "ZONE": "HAND", "ATK": atk, "HEALTH": hp, "COST": cost, "RUSH": 1,
    })
    return m


def test_exhaust_rush_keeps_inquisitor_for_mirror():
    """对面有高攻无嘲：审判官不应被强制突袭送死。"""
    fighters = [
        {"kind": "minion", "entity_id": 1, "card_id": "A", "atk": 5, "health": 5,
         "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "weapon", "entity_id": 2, "card_id": "W", "atk": 3, "health": 30,
         "durability": 1, "attacks_left": 1, "can_face": True, "shield": False},
        {"kind": "minion", "entity_id": 3, "card_id": "CS3_020", "atk": 8, "health": 8,
         "attacks_left": 1, "can_face": False, "rush": True,
         "mirrors_hero_attack": True, "shield": False},
    ]
    enemy = [
        {"kind": "minion", "entity_id": 10, "card_id": "FAT", "atk": 12, "health": 15,
         "taunt": False, "shield": False},
    ]
    fs2, board2 = exhaust_rush_on_enemy_minions(fighters, enemy, False)
    inq = next(f for f in fs2 if f.get("card_id") == "CS3_020")
    assert int(inq.get("health") or 0) > 0, inq
    assert fighters_face_damage(fs2, False) >= 5 + 3 + 8, fighters_face_damage(fs2, False)


def test_hand_inquisitor_mirror_lethal_vs_fat_board():
    """复盘：打出审判官 + 武器挥击跟刀，对面肥怪无嘲也应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=8, used=0, atk=3)
    _hero(gs, 2, 2, hp=29)
    _minion(gs, 10, 1, 4, 5, card_id="A")
    _minion(gs, 11, 1, 1, 1, card_id="B")
    _minion(gs, 12, 1, 3, 4, card_id="C")
    _minion(gs, 13, 1, 4, 4, card_id="D")
    _minion(gs, 14, 1, 5, 4, card_id="E")
    _minion(gs, 15, 1, 5, 4, card_id="F")
    _weapon(gs, 20, 1, 3, 1, "JAIL_730")
    _hand_rush(gs, 30, 1, "CS3_020", 8, 8, 8)
    _minion(gs, 40, 2, 12, 15, card_id="REV_247", turns=3)
    _minion(gs, 41, 2, 12, 15, card_id="REV_247", turns=3)

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    assert face >= 29, (face, note)
    total, _, lethal = LethalChecker(gs).calculate_lethal_potential()
    assert lethal, (total, face, note)


if __name__ == "__main__":
    test_exhaust_rush_keeps_inquisitor_for_mirror()
    test_hand_inquisitor_mirror_lethal_vs_fat_board()
    print("ok")
