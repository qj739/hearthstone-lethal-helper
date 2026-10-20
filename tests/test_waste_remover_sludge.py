#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""淤泥桶 WW_044t：仅手牌打出计入；牌库底毁桶（WW_042）暂不计。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.spell_board import get_board_spell_def
from hdt_python.end_turn_board import END_TURN_BY_CARD


def test_sludge_barrel_spell_registered():
    defn = get_board_spell_def("WW_044t")
    assert defn is not None
    taunts = [{"kind": "hero", "health": 13, "armor": 0, "entity_id": 1}]
    res = defn.apply(taunts, [], mult=1, enemy_shield=False, spell_power=0)
    assert res.direct_face_damage == 4


def test_waste_remover_end_turn_not_registered():
    """牌库底淤泥不可靠，WW_042 不计入回合结束斩杀。"""
    assert "WW_042" not in END_TURN_BY_CARD


if __name__ == "__main__":
    test_sludge_barrel_spell_registered()
    print("OK sludge spell")
    test_waste_remover_end_turn_not_registered()
    print("OK no WW_042 end turn")
