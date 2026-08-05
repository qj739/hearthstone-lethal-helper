#!/usr/bin/env python3
"""刃缚精锐 BT_495：本回合英雄攻击过后，战吼造成 4 点伤害。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.atk = atk
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    if atk:
        h.tags["ATK"] = atk
        h.tags["479"] = atk
    gs.hero_entity_ids[pid] = eid
    return h


def _weapon(gs, eid, pid, atk, dur, *, card_id="W"):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.health = dur
    w.durability = dur
    w.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk,
        "DURABILITY": dur, "DAMAGE": 0,
    })
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
    return w


def _hand_bc(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_bladebound_registered():
    assert get_battlecry_def("BT_495") is not None
    assert get_battlecry_def("TOY_913t3") is not None
    print("OK bladebound registered")


def test_bladebound_no_hero_attack_no_damage():
    """英雄未攻击：战吼 0 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=26)  # 4 血
    _hand_bc(gs, 30, 1, "BT_495", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face < 4, f"no hero attack → no 4 dmg, got {face}"
    print("OK bladebound no attack", face)


def test_bladebound_after_weapon_attack_lethal():
    """先武器挥击再打刃缚：4 伤打脸斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=25)  # 5 血
    _weapon(gs, 40, 1, 1, 2, card_id="CS2_082")
    _hand_bc(gs, 30, 1, "BT_495", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 5, f"weapon 1 + bladebound 4 expected >=5, got {face} note={note}"
    assert lethal, (face, note)
    assert "刃缚" in note or "BT_495" in note, note
    print("OK bladebound after weapon", face, note, lethal)


def test_bladebound_already_attacked_this_turn():
    """本回合已挥击过：直接打出战吼 4 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    h = _hero(gs, 1, 1, mana=10)
    h.tags["NUM_ATTACKS_THIS_TURN"] = 1
    _hero(gs, 2, 2, hp=30, dmg=26)  # 4 血
    _hand_bc(gs, 30, 1, "BT_495", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 4, f"already attacked → 4 face, got {face}"
    assert lethal, face
    print("OK bladebound already attacked", face, lethal)


if __name__ == "__main__":
    test_bladebound_registered()
    test_bladebound_no_hero_attack_no_damage()
    test_bladebound_after_weapon_attack_lethal()
    test_bladebound_already_attacked_this_turn()
