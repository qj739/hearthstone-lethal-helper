#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""混乱化形 6 点可打脸；附眼战槌按 2 攻武器接入。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python import black_empire_p0  # noqa: F401
from hdt_python.spell_board import get_board_spell_def
from hdt_python.weapon_board import get_weapon_def


def test_six_face():
    defn = get_board_spell_def("DEEP_031")
    assert defn is not None
    assert defn.base_cost == 6
    taunts = [{"kind": "hero", "health": 8, "armor": 0, "entity_id": 1}]
    res = defn.apply(taunts, [], mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 6


def test_weapon_registered():
    weapon = get_weapon_def("BE_349")
    assert weapon is not None
    assert weapon.base_cost == 4


if __name__ == "__main__":
    test_six_face()
    test_weapon_registered()
    print("OK chaotic tendril")
