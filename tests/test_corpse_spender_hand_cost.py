#!/usr/bin/env python3
"""残骸费用 CORPSE_SPENDER：打出占残骸不占法力（如黑暗之赐翼手龙 TLC_436）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.board_damage import (
    collect_hand_charge_minions,
    hand_minion_cost,
)
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, mana=10, corpses=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["CORPSES"] = corpses
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_minion(gs, eid, pid, card_id, *, cost=5, atk=7, charge=True, corpse=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.tags.update({
        "ZONE": "HAND",
        "COST": cost,
        "ATK": atk,
        "479": atk,
    })
    if charge:
        m.tags["CHARGE"] = 1
    if corpse:
        m.tags["CORPSE_SPENDER"] = 1
        m.tags["CARD_ALTERNATE_COST"] = 3
    return m


def test_corpse_spender_mana_zero_with_corpses():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, mana=3, corpses=13)
    card = _hand_minion(gs, 40, 1, "TLC_436", cost=5, atk=7)
    assert hand_minion_cost(card) == 0
    assert hand_minion_cost(card, gs, 1) == 0
    charges = collect_hand_charge_minions(gs, 1)
    assert charges == [(card, 0, 7)]


def test_corpse_spender_unaffordable_without_corpses():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, mana=10, corpses=2)
    card = _hand_minion(gs, 40, 1, "TLC_436", cost=5, atk=7)
    assert hand_minion_cost(card, gs, 1) == 999


def test_normal_minion_still_uses_mana():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, mana=10, corpses=20)
    card = _hand_minion(gs, 40, 1, "CS2_173", cost=2, atk=2, charge=True, corpse=False)
    assert hand_minion_cost(card, gs, 1) == 2


if __name__ == "__main__":
    test_corpse_spender_mana_zero_with_corpses()
    test_corpse_spender_unaffordable_without_corpses()
    test_normal_minion_still_uses_mana()
    print("ok")
