#!/usr/bin/env python3
"""永世裂痕 TIME_441：对两个敌人各 4 伤，不可重复命中；空场最多 4 脸。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence
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


def _hand_spell(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
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
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_aeon_rend_empty_board_face_at_most_4():
    defn = get_board_spell_def("TIME_441")
    assert defn is not None
    assert defn.uses_random

    res = apply_spell_sequence(
        [], [], [(defn, 4, None)],
        enemy_shield=False, mana_budget=10,
    )
    assert res.direct_face_damage == 4, (
        f"empty board should hit face once for 4, got {res.direct_face_damage}"
    )


def test_aeon_rend_two_enemies_each_4():
    taunts = [
        {"kind": "minion", "entity_id": 1, "health": 5, "atk": 1,
         "shield": False, "taunt": False},
    ]
    defn = get_board_spell_def("TIME_441")
    res = apply_spell_sequence(
        taunts, [], [(defn, 4, None)],
        enemy_shield=False, mana_budget=10,
    )
    # 英雄 + 随从：各 4；打脸分量恰为 4
    assert res.direct_face_damage == 4, res.direct_face_damage
    assert taunts[0]["health"] == 1, taunts[0]


def test_aeon_rend_not_false_lethal_vs_9_empty():
    """复现：对手 9 血空场 + 裂痕，旧实现按 8 脸误斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=21)  # 9 血
    _hand_spell(gs, 30, 1, "TIME_441", 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, _, spell, hp = lc.overlay_board_breakdown()
    _, _, lethal = lc.calculate_lethal_potential()
    red = lc.overlay_red_prompt_ok()
    assert spell <= 4, (spell, face, lc.overlay_spell_note())
    assert face < 9, (face, spell, hp, lc.overlay_spell_note())
    assert not lethal and not red, (face, lethal, red, lc.overlay_spell_note())


if __name__ == "__main__":
    test_aeon_rend_empty_board_face_at_most_4()
    test_aeon_rend_two_enemies_each_4()
    test_aeon_rend_not_false_lethal_vs_9_empty()
    print("ok")
