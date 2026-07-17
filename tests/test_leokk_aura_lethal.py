#!/usr/bin/env python3
"""雷欧克 NEW1_033：下场光环其他随从 +1 攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def


def _hero(gs, eid, pid, *, mana=10, used=0, health=30, damage=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = damage
    h.tags["DAMAGE"] = damage
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", exhausted=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": hp, "479": atk,
        "NUM_ATTACKS_THIS_TURN": 0,
        "EXHAUSTED": 1 if exhausted else 0,
        "NUM_TURNS_IN_PLAY": 0 if exhausted else 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({"ZONE": "HAND", "COST": cost, "ATK": atk, "HEALTH": hp, "479": atk})
    return m


def test_leokk_registered():
    assert get_battlecry_def("NEW1_033") is not None
    assert get_battlecry_def("VAN_NEW1_033") is not None


def test_call_of_the_wild_no_double_leokk_buff():
    """兽群呼唤：米莎 +1、霍弗 +1，不二次叠光环。"""
    defn = get_board_spell_def("CORE_OG_211")
    spell = type("C", (), {"card_id": "CORE_OG_211", "entity_id": 11, "tags": {}})()
    fighters = []
    apply_spell_sequence([], fighters, [(defn, 8, spell)])
    misha = next(f for f in fighters if f.get("card_id") == "NEW1_032")
    huffer = next(f for f in fighters if f.get("card_id") == "NEW1_034")
    assert misha.get("atk") == 5, misha.get("atk")
    assert huffer.get("atk") == 5, huffer.get("atk")


def test_leokk_from_hand_buffs_ready_board():
    """手牌打出雷欧克：场上可攻随从各 +1。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 23  # 7 血
    opp.damage = 23
    _minion(gs, 30, 1, 3, 3, card_id="REV_350t")
    _minion(gs, 31, 1, 3, 3, card_id="REV_350t")
    _hand_minion(gs, 50, 1, "NEW1_033", 3, 2, 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 8, (face, lc.overlay_combo_display_lines(), lc.overlay_spell_note())
    assert lc.calculate_lethal_potential()[2]


def test_leokk_on_board_buffs_hand_charge():
    """场上已有雷欧克：手牌霍弗冲锋按 5 攻计。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 25  # 5 血
    opp.damage = 25
    _minion(gs, 30, 1, 2, 4, card_id="NEW1_033", exhausted=True)
    # 其他随从 ATK 已含光环
    _minion(gs, 31, 1, 4, 3, card_id="REV_350t", exhausted=True)
    h = _hand_minion(gs, 50, 1, "NEW1_034", 3, 4, 2)
    h.tags["CHARGE"] = 1

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 5, (face, lc.overlay_combo_display_lines())
    assert lc.calculate_lethal_potential()[2]


if __name__ == "__main__":
    test_leokk_registered()
    test_call_of_the_wild_no_double_leokk_buff()
    test_leokk_from_hand_buffs_ready_board()
    test_leokk_on_board_buffs_hand_charge()
    # keep old call of wild
    from tests.test_call_of_the_wild_lethal import (
        test_call_of_the_wild_registered,
        test_call_of_the_wild_huffer_charge_face,
        test_call_of_the_wild_lethal,
    )
    test_call_of_the_wild_registered()
    test_call_of_the_wild_huffer_charge_face()
    test_call_of_the_wild_lethal()
    print("ok")
