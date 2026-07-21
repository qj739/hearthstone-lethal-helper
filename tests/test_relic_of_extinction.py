#!/usr/bin/env python3
"""灭绝圣物 REV_834：只能打敌方随从，不能打英雄。"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import register_arena_season_gap
from hdt_python.spell_board import get_board_spell_def
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker

register_arena_season_gap()


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", dormant=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": 1,
    })
    if dormant:
        m.tags["DORMANT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost, *, script=0):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    if script:
        s.tags["TAG_SCRIPT_DATA_NUM_1"] = script
    return s


def test_extinction_registered():
    for cid in ("REV_834", "CORE_REV_834"):
        assert get_board_spell_def(cid) is not None, cid
    print("OK extinction registered")


def test_extinction_empty_board_no_face():
    """无随从时空放：0 打脸。"""
    defn = get_board_spell_def("REV_834")
    res = defn.apply([], [], mult=1, enemy_shield=False, rng=random.Random(0))
    assert res.direct_face_damage == 0, res.direct_face_damage
    print("OK empty board no face")


def test_extinction_never_faces_with_minion():
    """有随从时随机点名仍不应打脸。"""
    defn = get_board_spell_def("REV_834")
    for seed in range(20):
        taunts = [{"health": 5, "atk": 2, "shield": False, "spell_immune": False, "entity_id": 1}]
        res = defn.apply(
            taunts, [], mult=1, enemy_shield=False, rng=random.Random(seed),
        )
        assert res.direct_face_damage == 0, f"seed={seed} face={res.direct_face_damage}"
        assert taunts[0]["health"] < 5 or taunts[0]["health"] == 0
    print("OK never faces with minion")


def test_extinction_skips_dormant_no_face():
    """仅休眠随从时无可点目标 → 0 伤（不打英雄）。"""
    defn = get_board_spell_def("REV_834")
    taunts = [{
        "health": 3, "atk": 1, "shield": False, "spell_immune": False,
        "entity_id": 1, "dormant": True,
    }]
    res = defn.apply(taunts, [], mult=1, enemy_shield=False, rng=random.Random(0))
    assert res.direct_face_damage == 0
    assert taunts[0]["health"] == 3, "dormant should be untouched"
    print("OK skips dormant no face")


def test_extinction_overlay_not_false_lethal():
    """对手空场 2 血 + 手牌灭绝：不应误报斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=28)  # 2 血
    _hand_spell(gs, 30, 1, "REV_834", 1, script=4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, _, spell, _ = lc.overlay_board_breakdown()
    _, _, lethal = lc.calculate_lethal_potential()
    assert spell == 0, f"extinction must not count as face, spell={spell}"
    assert face == 0, f"expected 0 face, got {face}"
    assert not lethal, "must not false-lethal via extinction on empty board"
    print("OK overlay no false lethal", face)


if __name__ == "__main__":
    test_extinction_registered()
    test_extinction_empty_board_no_face()
    test_extinction_never_faces_with_minion()
    test_extinction_skips_dormant_no_face()
    test_extinction_overlay_not_false_lethal()
    print("all passed")
