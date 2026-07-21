#!/usr/bin/env python3
"""石裔指控者 REV_013 / REV_013t：注能后战吼 5 伤应计入斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def, hand_battlecry_minions


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_minion(gs, eid, pid, card_id, *, cost=5, atk=5, hp=5, powered_up=False, infused=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "HAND"
    m.tags["COST"] = cost
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    m.tags["479"] = atk
    if powered_up:
        m.tags["POWERED_UP"] = 1
    if infused:
        m.tags["INFUSED"] = 1
    return m


def test_stoneborn_tokens_registered():
    for cid in ("REV_013", "REV_013t", "CORE_REV_013"):
        assert get_battlecry_def(cid) is not None, cid
    print("OK stoneborn registered")


def test_rev_013t_always_deals_5():
    """已注能 token REV_013t：无需 POWERED_UP，战吼 5 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=25)  # 5 hp
    _hand_minion(gs, 40, 1, "REV_013t")

    assert any(c.card_id == "REV_013t" for c, _, _ in hand_battlecry_minions(gs, 1, 10))
    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 5, f"expected >=5 from REV_013t, got {total}"
    assert has_lethal, "REV_013t battlecry 5 should lethal vs 5 hp"
    print("OK REV_013t deals 5", total)


def test_rev_013_uninfused_no_damage():
    """未注能 REV_013：无战吼伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=25)
    _hand_minion(gs, 40, 1, "REV_013")

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total == 0, f"uninfused should be 0, got {total}"
    print("OK uninfused no damage", total)


def test_rev_013_powered_up_deals_5():
    """未变形但 POWERED_UP 亮边：仍计 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=25)
    _hand_minion(gs, 40, 1, "REV_013", powered_up=True)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total >= 5, f"powered-up REV_013 should deal 5, got {total}"
    print("OK powered-up REV_013 deals 5", total)


if __name__ == "__main__":
    test_stoneborn_tokens_registered()
    test_rev_013t_always_deals_5()
    test_rev_013_uninfused_no_damage()
    test_rev_013_powered_up_deals_5()
    print("all passed")
