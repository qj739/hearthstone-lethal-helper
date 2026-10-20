#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自埋自收：3 点可打脸。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import get_board_spell_def


def test_three_face():
    defn = get_board_spell_def("WW_352")
    assert defn is not None
    assert defn.base_cost == 3
    taunts = [{"kind": "hero", "health": 10, "armor": 0, "entity_id": 1}]
    res = defn.apply(taunts, [], mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 3


if __name__ == "__main__":
    test_three_face()
    print("OK bury and reap")
