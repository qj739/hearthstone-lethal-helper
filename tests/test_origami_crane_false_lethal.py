#!/usr/bin/env python3
"""折纸仙鹤换血嘲讽：不应假斩，亡者大军+甜筒不应卡死。"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, hp=30, damage=0, mana=10, corpses=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.zone = "PLAY"
    h.health = hp
    h.damage = damage
    h.tags.update({
        "ZONE": "PLAY", "ARMOR": 0, "RESOURCES": mana, "RESOURCES_USED": 0,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "CORPSES": corpses,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", taunt=False, damage=0, pos=None):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = damage
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_TURNS_IN_PLAY": 1, "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0,
    })
    if taunt:
        m.tags["TAUNT"] = 1
    if pos is None:
        pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots.setdefault(pid, {})[pos] = eid
    return m


def _hand(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags.update({"ZONE": "HAND", "COST": cost})
    return c


def _scene(gs):
    """复现 2026-07-31：折纸仙鹤 6/15 嘲讽 + 银背 1/4，场面 16 攻，对手 16 血。"""
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 20
    _hero(gs, 1, 1, hp=30, damage=13, mana=10, corpses=17)
    _hero(gs, 2, 2, hp=30, damage=14)
    _minion(gs, 152, 1, 3, 2, card_id="CORE_EX1_362", pos=1)
    _minion(gs, 163, 1, 3, 1, card_id="JAIL_454t", pos=2)
    _minion(gs, 165, 1, 3, 3, card_id="TOY_642", pos=3)
    _minion(gs, 167, 1, 7, 7, card_id="REV_510", pos=4)
    _minion(gs, 60, 2, 6, 17, card_id="TOY_895", taunt=True, damage=2, pos=1)
    _minion(gs, 154, 2, 1, 1, card_id="TOY_307t", pos=2)
    _minion(gs, 190, 2, 1, 4, card_id="CS2_127", taunt=True, pos=3)


def test_origami_crane_taunt_not_false_lethal():
    gs = GameState()
    _scene(gs)
    _hand(gs, 28, 1, "RLK_060", 5)
    _hand(gs, 137, 1, "VAC_427", 2)

    t0 = time.perf_counter()
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    elapsed = time.perf_counter() - t0
    _, _, has = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note() or ""

    assert elapsed < 5.0, f"taunt clear hung: {elapsed:.2f}s"
    assert face < 16, (face, note, lc.overlay_board_breakdown())
    assert not has, (face, has, note)
    assert not lc.lethal_calc_timed_out() or face < 16
    print("OK origami crane no false lethal", face, f"{elapsed:.3f}s", note)


def test_army_corpsicle_taunt_clear_fast():
    gs = GameState()
    _scene(gs)
    _hand(gs, 28, 1, "RLK_060", 5)
    _hand(gs, 137, 1, "VAC_427", 2)
    t0 = time.perf_counter()
    face = LethalChecker(gs).overlay_board_face_damage()
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, f"still too slow: {elapsed:.2f}s face={face}"
    print("OK army+corpsicle fast", face, f"{elapsed:.3f}s")


if __name__ == "__main__":
    test_army_corpsicle_taunt_clear_fast()
    test_origami_crane_taunt_not_false_lethal()
    print("all passed")
