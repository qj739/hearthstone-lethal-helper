#!/usr/bin/env python3
"""德纳修斯大帝 REV_906：注能伤害来自 TAG_SCRIPT_DATA_NUM_1。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.battlecry_p0 import _apply_sire_denathrius, _denathrius_battlecry_damage
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import _apply_random_split_damage


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_minion(gs, eid, pid, card_id, cost, *, script_damage=None):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.tags["ZONE"] = "HAND"
    if script_damage is not None:
        m.tags["TAG_SCRIPT_DATA_NUM_1"] = script_damage
    return m


def test_denathrius_registered():
    assert get_battlecry_def("CORE_REV_906") is not None


def test_denathrius_reads_infuse_damage_from_log_tag():
    card = type("C", (), {
        "card_id": "CORE_REV_906",
        "tags": {"TAG_SCRIPT_DATA_NUM_1": 12},
    })()
    assert _denathrius_battlecry_damage(card, default=5) == 12


def test_denathrius_default_damage_without_tag():
    card = type("C", (), {"card_id": "CORE_REV_906", "tags": {}})()
    assert _denathrius_battlecry_damage(card, default=5) == 5


def test_denathrius_random_split_includes_hero():
    res = _apply_random_split_damage(
        [], [], 5, enemy_shield=False, include_enemy_hero=True,
    )
    assert res.direct_face_damage == 5


def test_denathrius_battlecry_lifesteal():
    card = type("C", (), {
        "card_id": "CORE_REV_906",
        "tags": {"TAG_SCRIPT_DATA_NUM_1": 4},
    })()
    res = _apply_sire_denathrius([], [], mult=1, enemy_shield=False, card=card)
    assert res.self_hero_heal == 4
    assert res.direct_face_damage == 4


def test_denathrius_uses_random_flag():
    defn = get_battlecry_def("CORE_REV_906")
    assert defn is not None
    assert defn.uses_random is True


def test_denathrius_lethal_with_infused_damage():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 12
    _hand_minion(gs, 11, 1, "CORE_REV_906", 10, script_damage=12)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face >= 12, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert has, (face, has, lc.overlay_spell_note())


if __name__ == "__main__":
    test_denathrius_registered()
    test_denathrius_reads_infuse_damage_from_log_tag()
    test_denathrius_default_damage_without_tag()
    test_denathrius_random_split_includes_hero()
    test_denathrius_battlecry_lifesteal()
    test_denathrius_uses_random_flag()
    test_denathrius_lethal_with_infused_damage()
    print("OK denathrius infuse damage")
