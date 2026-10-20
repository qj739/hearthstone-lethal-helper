#!/usr/bin/env python3
"""TLC_436 重生翼手龙：残骸代费突袭须进斩杀（含未进当季突袭表 / 黑暗之赐）。

复现 2026-10-12 漏斩：场面已攻完后对手 9 血，手牌 8 攻突袭翼手龙 + 场上饱胀水蛭回合计偷 1。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.board_damage import collect_hand_rush_minions, hand_minion_cost
from hdt_python.power_parser import GameState
from hdt_python.rush_board import get_rush_def, hand_rush_minions, resolve_rush_def
from hdt_python.spell_board import apply_spell_sequence


def _hero(gs, eid, pid, *, mana=10, corpses=0, damage=0, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.zone = "PLAY"
    h.health = health
    h.damage = damage
    h.tags.update({
        "ZONE": "PLAY",
        "CARDTYPE": "HERO",
        "HEALTH": health,
        "DAMAGE": damage,
        "RESOURCES": mana,
        "RESOURCES_USED": 0,
        "CORPSES": corpses,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def test_tlc436_registered_and_resolve_fallback():
    assert get_rush_def("TLC_436") is not None
    # 未进表的突袭 id 也能 resolve
    assert resolve_rush_def("FAKE_RUSH_XYZ") is not None


def test_tlc436_corpse_cost_zero_in_hand_rush():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, mana=4, corpses=4)
    card = gs.get_entity(128)
    card.cardtype = "MINION"
    card.controller = 1
    card.zone = "HAND"
    card.card_id = "TLC_436"
    card.tags.update({
        "ZONE": "HAND",
        "COST": 3,
        "ATK": 8,
        "HEALTH": 8,
        "RUSH": 1,
        "LIFESTEAL": 1,
        "CORPSE_SPENDER": 1,
        "CARD_ALTERNATE_COST": 3,
    })
    assert hand_minion_cost(card, gs, 1) == 0
    rushes = hand_rush_minions(gs, 1, available_mana=4)
    assert any(c.card_id == "TLC_436" and cost == 0 for c, _d, cost in rushes)
    collected = collect_hand_rush_minions(gs, 1, available_mana=4)
    assert collected == [(card, 0, 8)]


def test_tlc436_apply_summons_rush_8():
    defn = get_rush_def("TLC_436")
    gs = GameState()
    card = gs.get_entity(40)
    card.cardtype = "MINION"
    card.card_id = "TLC_436"
    card.tags.update({"ATK": 8, "HEALTH": 8, "RUSH": 1})
    fighters: list = []
    apply_spell_sequence([], fighters, [(defn, 0, card)], enemy_shield=False)
    rush = next(f for f in fighters if f.get("rush"))
    assert rush["atk"] == 8
    assert rush.get("can_face") is False  # 突袭初始不可解嘲讽外打脸；空场由 combat 开脸


if __name__ == "__main__":
    test_tlc436_registered_and_resolve_fallback()
    test_tlc436_corpse_cost_zero_in_hand_rush()
    test_tlc436_apply_summons_rush_8()
    print("OK tlc436")
