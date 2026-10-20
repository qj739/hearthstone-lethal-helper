#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""吸取灵魂：3 点只能打随从，脚本伤害不能当成打脸。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import (
    estimate_no_taunt_direct_face_damage,
    get_board_spell_def,
    spell_script_damage,
)


class _Card:
    def __init__(self):
        self.card_id = "CORE_ICC_055"
        self.tags = {"TAG_SCRIPT_DATA_NUM_1": 3}
        self.entity_id = 9


def test_minion_only():
    defn = get_board_spell_def("CORE_ICC_055")
    assert defn is not None
    hero = [{"kind": "hero", "health": 10, "armor": 0, "entity_id": 1}]
    res = defn.apply(hero, [], mult=1, enemy_shield=False, spell_power=0, card=_Card())
    assert res.direct_face_damage == 0
    assert hero[0]["health"] == 10

    board = [
        {"kind": "minion", "entity_id": 10, "health": 5, "atk": 2, "taunt": False, "zone_pos": 1},
        {"kind": "hero", "health": 10, "armor": 0, "entity_id": 1},
    ]
    res = defn.apply(board, [], mult=1, enemy_shield=False, spell_power=0, card=_Card())
    assert res.direct_face_damage == 0
    assert board[0]["health"] == 2
    assert board[1]["health"] == 10
    assert res.self_hero_heal == 3
    assert spell_script_damage(_Card()) == 0
    assert estimate_no_taunt_direct_face_damage(defn, _Card()) == 0


if __name__ == "__main__":
    test_minion_only()
    print("OK drain soul")
