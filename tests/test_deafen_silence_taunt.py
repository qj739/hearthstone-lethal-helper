#!/usr/bin/env python3
"""致聋术 JAM_022：沉默嘲讽后应计入斩杀/场攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id=""):
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
    if taunt:
        m.tags["TAUNT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost=1):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def test_deafen_registered():
    defn = get_board_spell_def("JAM_022")
    assert defn is not None
    assert defn.name == "致聋术"


def test_deafen_silence_taunt_enables_face():
    """8/8 嘲讽 + 己方 3/3×2：致聋沉默嘲后应能打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    for eid in (10, 11):
        _minion(gs, eid, 1, 3, 3, card_id=f"M{eid}")
    _minion(gs, 20, 2, 8, 8, taunt=True, card_id="BIG")
    _hand_spell(gs, 30, 1, "JAM_022", 1)

    checker = LethalChecker(gs)
    assert checker.overlay_board_face_damage() == 6


def test_deafen_combo_damage_kills_small_taunt():
    """连击致聋术：沉默+2 伤可干掉 2 血嘲讽。"""
    from hdt_python.spell_p0_remove import _apply_deafen

    taunts = [
        {"entity_id": 20, "health": 2, "atk": 1, "taunt": True, "kind": "minion"},
    ]
    fighters = [
        {"kind": "minion", "entity_id": 10, "atk": 5, "health": 3,
         "attacks_left": 1, "can_face": True},
    ]
    _apply_deafen(taunts, fighters, mult=1, enemy_shield=False, combo_active=True)
    assert not any(t.get("taunt") for t in taunts if t.get("health", 0) > 0)
    assert not any(t.get("health", 0) > 0 for t in taunts)


if __name__ == "__main__":
    test_deafen_registered()
    test_deafen_silence_taunt_enables_face()
    test_deafen_combo_damage_kills_small_taunt()
    print("ok")
