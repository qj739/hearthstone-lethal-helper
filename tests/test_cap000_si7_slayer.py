#!/usr/bin/env python3
"""CAP_000 军情七处杀手：潜行友方攻击时 +2/+2，应计入斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.rush_combat import simulate_minion_face_hits
from hdt_python.secret_attack_board import stamp_si7_slayer_aura_on_fighters


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", can_attack=True, stealth=False):
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
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    if stealth:
        m.tags["STEALTH"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if not can_attack:
        m.tags["EXHAUSTED"] = 1
        m.tags["NUM_TURNS_IN_PLAY"] = 0
    return m


def test_si7_slayer_stealth_face_lethal():
    """4 攻潜行 + CAP_000 → 攻击时 6 伤，对手 6 血应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 24
    opp.damage = 24
    _minion(gs, 30, 1, 4, 4, card_id="EDR_523t", stealth=True)
    _minion(gs, 31, 1, 1, 2, card_id="CAP_000", can_attack=False, stealth=True)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 6, f"expected face>=6 got {face}"
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"should detect lethal total={total} face={face}"


def test_si7_slayer_no_buff_without_stealth():
    """无潜行时杀手不应抬攻。"""
    fighters = [
        {
            "kind": "minion", "card_id": "X", "atk": 4, "health": 4,
            "attacks_left": 1, "can_face": True, "stealth": False,
            "si7_slayer_on_attack": True,
        },
        {
            "kind": "minion", "card_id": "CAP_000", "atk": 1, "health": 2,
            "attacks_left": 0, "can_face": False, "stealth": True,
        },
    ]
    stamp_si7_slayer_aura_on_fighters(fighters)
    hits = simulate_minion_face_hits(fighters)
    assert hits == [4], f"expected [4] got {hits}"


def test_si7_slayer_buff_then_break_stealth():
    """潜行攻击一次吃 +2，破潜后同回合再攻不再叠杀手。"""
    fighters = [
        {
            "kind": "minion", "card_id": "X", "atk": 4, "health": 4,
            "attacks_left": 2, "can_face": True, "stealth": True,
            "si7_slayer_on_attack": True,
        },
        {
            "kind": "minion", "card_id": "CAP_000", "atk": 1, "health": 2,
            "attacks_left": 0, "can_face": False, "stealth": True,
        },
    ]
    hits = simulate_minion_face_hits(fighters)
    assert hits == [6, 6], f"expected [6, 6] got {hits}"
    assert fighters[0]["stealth"] is False
    assert fighters[0]["atk"] == 6


def test_si7_slayer_play_stamps_aura_for_face():
    """手牌打出杀手后，场上潜行随从打脸应吃到 +2。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.most_wanted_p0 import register_most_wanted

    register_most_wanted()
    defn = get_battlecry_def("CAP_000")
    assert defn is not None
    fighters = [
        {
            "kind": "minion", "card_id": "EDR_523t", "atk": 4, "health": 2,
            "attacks_left": 1, "can_face": True, "stealth": True,
        },
    ]
    defn.apply([], fighters, mult=1, enemy_shield=False)
    assert any(f.get("card_id") == "CAP_000" for f in fighters)
    assert fighters[0].get("si7_slayer_on_attack")
    hits = simulate_minion_face_hits(fighters)
    assert hits == [6], f"expected [6] got {hits}"


if __name__ == "__main__":
    test_si7_slayer_stealth_face_lethal()
    test_si7_slayer_no_buff_without_stealth()
    test_si7_slayer_buff_then_break_stealth()
    test_si7_slayer_play_stamps_aura_for_face()
    print("ok")
