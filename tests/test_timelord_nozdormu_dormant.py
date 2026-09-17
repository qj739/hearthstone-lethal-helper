# tests/test_timelord_nozdormu_dormant.py — TIME_063 上场休眠不可突袭

from __future__ import annotations

from hdt_python.arena_season_bulk import register_arena_season_gap
from hdt_python.combat_sim import project_board_face_after_spell, unit_is_dormant
from hdt_python.rush_board import get_rush_def
from hdt_python.rush_p0 import _apply_timelord_nozdormu, _register_all_rush_minions


def test_timelord_nozdormu_registered_as_dormant_rush():
    register_arena_season_gap()
    _register_all_rush_minions()
    defn = get_rush_def("TIME_063")
    assert defn is not None
    assert defn.apply is _apply_timelord_nozdormu


def test_timelord_nozdormu_play_no_attack_this_turn():
    register_arena_season_gap()
    _register_all_rush_minions()
    defn = get_rush_def("TIME_063")
    fighters: list = []
    taunts = [
        {"kind": "minion", "health": 3, "atk": 1, "shield": False, "taunt": True},
    ]
    defn.apply(taunts, fighters, mult=1, enemy_shield=False, card=None)
    assert len(fighters) == 1
    unit = fighters[0]
    assert unit.get("card_id") == "TIME_063"
    assert unit_is_dormant(unit)
    assert int(unit.get("attacks_left", 0) or 0) == 0
    assert unit.get("can_face") is False
    # 休眠中不可解嘲 / 打脸
    face = project_board_face_after_spell(taunts, fighters, False)
    assert face == 0, face
    assert taunts[0]["health"] == 3
