#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""库区守卫：落在两名可打脸随从中间，两侧 +2/+2。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def


class _Card:
    def __init__(self):
        self.card_id = "BE_151"
        self.tags = {"ATK": 3, "HEALTH": 3}
        self.atk = 3
        self.health = 3
        self.current_health = 3


def test_buffs_the_two_adjacent_attackers():
    defn = get_battlecry_def("BE_151")
    assert defn is not None
    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 1, "health": 5,
         "attacks_left": 0, "can_face": False, "zone_pos": 1},
        {"kind": "minion", "entity_id": 2, "atk": 2, "health": 2,
         "attacks_left": 1, "can_face": True, "zone_pos": 2},
        {"kind": "minion", "entity_id": 3, "atk": 4, "health": 3,
         "attacks_left": 1, "can_face": True, "zone_pos": 3},
    ]
    defn.apply([], fighters, mult=1, card=_Card())
    by_id = {u["entity_id"]: u for u in fighters if u.get("entity_id") in (1, 2, 3)}
    assert by_id[1]["atk"] == 1 and by_id[1]["health"] == 5
    assert by_id[2]["atk"] == 4 and by_id[2]["health"] == 4
    assert by_id[3]["atk"] == 6 and by_id[3]["health"] == 5
    body = next(u for u in fighters if u.get("card_id") == "BE_151")
    assert body["attacks_left"] == 0
    assert body["atk"] == 3
    assert int(body["zone_pos"]) == 3


def test_empty_board_only_body():
    defn = get_battlecry_def("BE_151")
    fighters = []
    defn.apply([], fighters, mult=1, card=_Card())
    assert len(fighters) == 1
    assert fighters[0]["atk"] == 3 and fighters[0]["health"] == 3


if __name__ == "__main__":
    test_buffs_the_two_adjacent_attackers()
    test_empty_board_only_body()
    print("OK vaultkeeper")
