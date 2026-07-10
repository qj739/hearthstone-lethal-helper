#!/usr/bin/env python3
"""destroy_any 批量注册法术须返回 SpellApplyResult，不能返回被消灭随从 dict。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python import spell_board as sb
from hdt_python.arena_season_bulk import register_arena_season_gap


def test_destroy_any_bulk_spells_return_spell_apply_result():
    register_arena_season_gap()
    defn = sb.get_board_spell_def("CATA_EVENT_402")
    assert defn is not None
    fighters = [{"kind": "minion", "atk": 3, "health": 3, "attacks_left": 1}]
    res = defn.apply([], list(fighters), mult=1, enemy_shield=False)
    assert isinstance(res, sb.SpellApplyResult)
    assert fighters[0]["health"] == 0


def test_end_028_kills_friendly_low_attack():
    register_arena_season_gap()
    defn = sb.get_board_spell_def("END_028")
    assert defn is not None
    taunts = [{"kind": "minion", "atk": 2, "health": 5}]
    fighters = [
        {"kind": "minion", "atk": 4, "health": 4, "attacks_left": 1},
        {"kind": "minion", "atk": 8, "health": 8, "attacks_left": 1},
    ]
    res = defn.apply(taunts, fighters, mult=1, enemy_shield=False)
    assert isinstance(res, sb.SpellApplyResult)
    assert not taunts
    assert fighters[0]["health"] == 0
    assert fighters[1]["health"] == 8


if __name__ == "__main__":
    test_destroy_any_bulk_spells_return_spell_apply_result()
    test_end_028_kills_friendly_low_attack()
    print("ok")
