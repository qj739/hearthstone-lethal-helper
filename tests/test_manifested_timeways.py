#!/usr/bin/env python3
"""时间流具象 TIME_019：战吼 AOE3 仅在控制光环时生效。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def, player_controls_aura
from hdt_python.arena_season_bulk import register_arena_season_gap

register_arena_season_gap()


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


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1, aura=False):
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
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    if aura:
        m.tags["AURA"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, *, cost=4, atk=3, hp=3, powered_up=False):
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
    return m


def test_timeways_registered_in_p0():
    defn = get_battlecry_def("TIME_019")
    assert defn is not None
    assert defn.name == "时间流具象"
    print("OK timeways registered")


def test_timeways_no_aura_no_aoe():
    """无光环：不应把战吼 3 伤打脸算进场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=21)  # 9 hp
    _minion(gs, 10, 1, 7, 5, card_id="CS2_101t8", turns=1)
    _hand_minion(gs, 40, 1, "TIME_019", cost=4, atk=3, hp=3, powered_up=False)

    assert not player_controls_aura(gs, 1)
    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    # 仅 7 场面；无光环不应 +3 吼
    assert total == 7, f"expected 7 without aura AOE, got {total}"
    print("OK timeways no aura no aoe", total)


def test_timeways_with_aura_aoe():
    """有光环：战吼 AOE3 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=21)  # 9 hp
    _minion(gs, 10, 1, 7, 5, card_id="CS2_101t8", turns=1)
    _minion(gs, 11, 1, 2, 2, card_id="ETC_337", turns=1, aura=True)
    _hand_minion(gs, 40, 1, "TIME_019", cost=4, atk=3, hp=3, powered_up=True)

    assert player_controls_aura(gs, 1)
    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    # 7 场面 + 光环随从 2（可攻）+ 吼 3 = 至少 10；光环随从若可攻则 12
    assert total >= 10, f"expected >=10 with aura AOE, got {total}"
    print("OK timeways with aura aoe", total)


def test_timeways_powered_up_alone():
    """仅 POWERED_UP 亮边也应触发 AOE（日志对齐）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=27)  # 3 hp
    _hand_minion(gs, 40, 1, "TIME_019", cost=4, atk=3, hp=3, powered_up=True)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total >= 3, f"expected powered-up AOE face >=3, got {total}"
    print("OK timeways powered up alone", total)


if __name__ == "__main__":
    test_timeways_registered_in_p0()
    test_timeways_no_aura_no_aoe()
    test_timeways_with_aura_aoe()
    test_timeways_powered_up_alone()
    print("all passed")
