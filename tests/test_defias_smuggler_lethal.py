#!/usr/bin/env python3
"""迪菲亚私运者 JAIL_998：友方 +2 攻与突袭，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def, hand_battlecry_minions
from hdt_python.battlecry_p0 import _apply_defias_smuggler


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


def _minion(gs, eid, pid, atk, hp, *, card_id="m", exhausted=False):
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
    m.tags["EXHAUSTED"] = 1 if exhausted else 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, cost, *, prepared=0):
    s = gs.get_entity(eid)
    s.cardtype = "MINION"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.atk = 3
    s.health = 3
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    s.tags["ATK"] = 3
    s.tags["HEALTH"] = 3
    if prepared:
        s.tags["PREPARED"] = prepared
    return s


def test_defias_smuggler_registered_and_buffs():
    assert get_battlecry_def("JAIL_998") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2)
    _minion(gs, 30, 1, 8, 7, card_id="REV_952")
    _hand_minion(gs, 40, 1, "JAIL_998", 0, prepared=3)

    lc = LethalChecker(gs)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    assert fighters[0]["atk"] == 8
    _apply_defias_smuggler([], fighters, mult=1, gs=gs, player_id=1)
    assert fighters[0]["atk"] == 10
    assert any(c.card_id == "JAIL_998" for c, _, _ in hand_battlecry_minions(gs, 1, 10))


def test_defias_smuggler_enables_lethal():
    """8+5 场面 + 私运者 +2 最高攻 = 15 脸，对手 15 血可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=8)
    _hero(gs, 20, 2, dmg=15)
    _minion(gs, 30, 1, 8, 7, card_id="REV_952")
    _minion(gs, 31, 1, 5, 4, card_id="TIME_017")
    _hand_minion(gs, 40, 1, "JAIL_998", 0, prepared=3)

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    assert face >= 15, f"expected face>=15 got {face}"
    assert lethal, f"should detect lethal total={total} face={face}"


def test_defias_smuggler_rush_on_exhausted_clears_taunt():
    """仅疲劳友方时：战吼仍应 +2 并赋予突袭（可解嘲，当回合不打脸）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=20)
    sick = _minion(gs, 31, 1, 4, 4, card_id="sick", exhausted=True)
    sick.tags["NUM_TURNS_IN_PLAY"] = 0
    fighters: list = []
    taunts = [{"kind": "minion", "entity_id": 50, "atk": 1, "health": 2,
               "taunt": True, "shield": False}]
    _apply_defias_smuggler(taunts, fighters, mult=1, gs=gs, player_id=1)
    target = next(f for f in fighters if f.get("entity_id") == 31)
    assert target["atk"] == 6, target
    assert target.get("rush") is True, target
    assert target.get("attacks_left", 0) >= 1, target
    assert target.get("can_face") is False, target

    # 有可攻友方时：+2 计入斩杀打脸
    gs2 = GameState()
    gs2.local_player_id = 1
    gs2.opponent_player_id = 2
    gs2.active_player_id = 1
    gs2.in_game = True
    _hero(gs2, 10, 1, mana=10)
    _hero(gs2, 20, 2, dmg=24)  # 6 血
    ready = _minion(gs2, 30, 1, 5, 5, card_id="ready")
    ready.tags["NUM_TURNS_IN_PLAY"] = 2
    _hand_minion(gs2, 40, 1, "JAIL_998", 3)
    lc = LethalChecker(gs2)
    face = lc.overlay_board_face_damage()
    assert face >= 7, face
    _, _, lethal = lc.calculate_lethal_potential()
    assert lethal


if __name__ == "__main__":
    test_defias_smuggler_registered_and_buffs()
    test_defias_smuggler_enables_lethal()
    test_defias_smuggler_rush_on_exhausted_clears_taunt()
    print("ok")
