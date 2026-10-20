#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""续连熵能：全体友方随从 +1/+1。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import get_board_spell_def, spell_sim_tier, SpellSimTier


def test_buffs_all_friendly():
    defn = get_board_spell_def("TIME_026")
    assert defn is not None
    assert defn.base_cost == 1
    assert spell_sim_tier(defn) == SpellSimTier.UTILITY
    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 2, "health": 3, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 2, "atk": 4, "health": 1, "attacks_left": 1, "can_face": True},
        {"kind": "hero", "entity_id": 3, "atk": 0, "health": 30, "attacks_left": 0},
    ]
    res = defn.apply([], fighters, mult=1, enemy_shield=False, spell_power=2)
    assert res.direct_face_damage == 0
    assert fighters[0]["atk"] == 3 and fighters[0]["health"] == 4
    assert fighters[1]["atk"] == 5 and fighters[1]["health"] == 2
    assert fighters[2]["atk"] == 0 and fighters[2]["health"] == 30


if __name__ == "__main__":
    test_buffs_all_friendly()
    print("OK continued entropy")
