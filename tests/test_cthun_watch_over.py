#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""凌空守望：克苏恩的愤怒 7 点随机 + 克苏恩的领域 +2/+3。"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python import black_empire_p0  # noqa: F401  注册 BE_778
from hdt_python.spell_board import get_board_spell_def


def test_watch_over_buffs_and_can_face():
    defn = get_board_spell_def("BE_778")
    assert defn is not None and defn.uses_random
    taunts = [{"kind": "hero", "health": 14, "armor": 0, "entity_id": 1}]
    fighters = [
        {"kind": "minion", "entity_id": 60, "card_id": "TIME_045",
         "atk": 1, "health": 4, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 47, "card_id": "YOG_523",
         "atk": 4, "health": 4, "attacks_left": 1, "can_face": True},
    ]
    res = defn.apply(
        taunts, fighters, mult=1, enemy_shield=False, rng=random.Random(0),
    )
    assert res.direct_face_damage == 7
    atks = sorted(u["atk"] for u in fighters)
    assert atks == [3, 6]


def test_wrath_registered():
    assert get_board_spell_def("BE_013t1") is not None
    assert get_board_spell_def("BE_013t2") is not None


if __name__ == "__main__":
    test_watch_over_buffs_and_can_face()
    test_wrath_registered()
    print("OK cthun watch over")
