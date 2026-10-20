#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""太阳的祝福：友方随从 +2/+3。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import (
    SPELL_REQUIRES_FRIENDLY_MINION,
    SpellSimTier,
    get_board_spell_def,
    spell_sim_tier,
)


def test_plus_two_three():
    defn = get_board_spell_def("BE_152t")
    assert defn is not None
    assert defn.base_cost == 2
    assert "BE_152t" in SPELL_REQUIRES_FRIENDLY_MINION
    assert spell_sim_tier(defn) == SpellSimTier.UTILITY
    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 3, "health": 4,
         "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 2, "atk": 1, "health": 5,
         "attacks_left": 0, "can_face": False},
    ]
    res = defn.apply([], fighters, mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 0
    assert fighters[0]["atk"] == 5 and fighters[0]["health"] == 7
    assert fighters[1]["atk"] == 1 and fighters[1]["health"] == 5


if __name__ == "__main__":
    test_plus_two_three()
    print("OK suns blessing")
