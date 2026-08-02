#!/usr/bin/env python3
"""饭圈迷弟 JAM_027：抉择取 +2 攻与突袭，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def, hand_battlecry_minions
from hdt_python.battlecry_p0 import _apply_fanboy


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


def _hand_minion(gs, eid, pid, card_id, cost, *, atk=2, hp=2):
    s = gs.get_entity(eid)
    s.cardtype = "MINION"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.atk = atk
    s.health = hp
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    s.tags["ATK"] = atk
    s.tags["HEALTH"] = hp
    return s


def test_fanboy_registered_and_buffs():
    assert get_battlecry_def("JAM_027") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2)
    _minion(gs, 30, 1, 4, 4, card_id="TIME_052")
    _hand_minion(gs, 40, 1, "JAM_027", 2)

    fighters = LethalChecker(gs)._build_fighters(gs.get_overlay_board(1), 1)
    assert fighters[0]["atk"] == 4
    _apply_fanboy([], fighters, mult=1, gs=gs, player_id=1)
    target = next(f for f in fighters if f.get("entity_id") == 30)
    assert target["atk"] == 6
    assert target.get("rush") is True
    assert any(c.card_id == "JAM_027" for c, _, _ in hand_battlecry_minions(gs, 1, 10))


def test_fanboy_enables_lethal():
    """场面 4+6，迷弟给最高攻 +2 → 12 脸，对手 12 血可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=18)  # 12 血
    _minion(gs, 30, 1, 4, 4, card_id="TIME_052")
    _minion(gs, 31, 1, 6, 5, card_id="ready")
    _hand_minion(gs, 40, 1, "JAM_027", 2)

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    assert face >= 12, f"expected face>=12 got {face}"
    assert lethal, f"should detect lethal total={total} face={face}"


def test_fanboy_rush_on_exhausted():
    """仅疲劳友方：仍应 +2 并赋予突袭（可解嘲，当回合不打脸）。"""
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
    _apply_fanboy([], fighters, mult=1, gs=gs, player_id=1)
    target = next(f for f in fighters if f.get("entity_id") == 31)
    assert target["atk"] == 6, target
    assert target.get("rush") is True, target
    assert target.get("attacks_left", 0) >= 1, target
    assert target.get("can_face") is False, target


if __name__ == "__main__":
    test_fanboy_registered_and_buffs()
    test_fanboy_enables_lethal()
    test_fanboy_rush_on_exhausted()
    print("ok")
