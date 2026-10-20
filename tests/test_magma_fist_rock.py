#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""魔拳岩：优先把冲锋食尸鬼变为 6/7。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.location_board import get_location_def


def test_sets_charge_ghoul_to_6_7():
    defn = get_location_def("WW_001t11")
    assert defn is not None
    fighters = [
        {"kind": "minion", "entity_id": 183, "card_id": "BE_298",
         "atk": 2, "health": 2, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 188, "card_id": "HERO_11bpt",
         "atk": 1, "health": 1, "attacks_left": 1, "can_face": True, "charge": True},
    ]
    defn.apply([], fighters, mult=1, enemy_shield=False)
    by_id = {u["entity_id"]: u for u in fighters}
    assert by_id[188]["atk"] == 6 and by_id[188]["health"] == 7
    assert by_id[188]["attacks_left"] == 1 and by_id[188]["can_face"] is True
    assert by_id[183]["atk"] == 2 and by_id[183]["health"] == 2


if __name__ == "__main__":
    test_sets_charge_ghoul_to_6_7()
    print("OK magma fist rock")
