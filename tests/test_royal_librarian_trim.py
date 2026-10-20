#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""满手牌时，沉默嘲讽的王室图书管理员不能被裁掉。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.lethal_checker import LethalChecker, MAX_HAND_SPELLS_FOR_SEARCH
from hdt_python.power_parser import GameState
from hdt_python.spell_board import get_board_spell_def


class _Card:
    def __init__(self, eid, cid, cost):
        self.entity_id = eid
        self.card_id = cid
        self.cost = cost
        self.tags = {}
        self.is_spell = False
        self.atk = 4
        self.health = 4
        self.current_health = 4


def _taunt(**kw):
    base = {
        "kind": "minion", "health": 5, "atk": 3, "taunt": True, "zone_pos": 1,
        "shield": False, "lifesteal": False, "poisonous": False, "spell_immune": False,
    }
    base.update(kw)
    return base


def _fighter(**kw):
    base = {
        "kind": "minion", "health": 4, "atk": 3, "attacks_left": 1, "can_face": True,
        "shield": False, "lifesteal": False, "poisonous": False, "rush": False,
    }
    base.update(kw)
    return base


def test_silence_unlocks_face():
    defn = get_battlecry_def("CORE_SW_066")
    assert defn is not None
    taunts = [_taunt(entity_id=54, card_id="DEEP_005")]
    fighters = [
        _fighter(entity_id=1, atk=7, health=8),
        _fighter(entity_id=2, atk=2, health=1),
        _fighter(entity_id=3, atk=3, health=8),
    ]
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    checker = LethalChecker(gs)
    unlock = checker._estimate_taunt_unlock_face(
        defn, _Card(7, "CORE_SW_066", 4), taunts, fighters,
        defender_shield=False, player_id=1,
    )
    # 不解嘲时也可能用随从解嘲后有残余脸伤；沉默应额外抬高可打脸量
    assert unlock >= 7, unlock


def test_trim_keeps_librarian_when_hand_full():
    librarian = get_battlecry_def("CORE_SW_066")
    bury = get_board_spell_def("WW_352")
    assert librarian and bury
    # 造一堆低价值 0 伤牌 + 管理员 + 自埋自收，超过裁剪上限
    hand = []
    eid = 100
    for cid, cost, defn in [
        ("CORE_EDR_002", 2, get_board_spell_def("CORE_EDR_002") or librarian),
        ("YOG_513", 4, get_board_spell_def("YOG_513") or librarian),
        ("END_005", 5, get_board_spell_def("END_005") or librarian),
        ("BE_781t12", 6, get_board_spell_def("BE_781t12") or librarian),
        ("DEEP_007", 2, get_battlecry_def("DEEP_007") or librarian),
        ("TIME_035", 4, get_battlecry_def("TIME_035") or librarian),
        ("RLK_511", 2, get_battlecry_def("RLK_511") or librarian),
        ("BE_284", 3, get_board_spell_def("BE_284") or librarian),
    ]:
        if defn is None:
            continue
        hand.append((_Card(eid, cid, cost), defn, cost))
        eid += 1
    hand.append((_Card(7, "CORE_SW_066", 4), librarian, 4))
    hand.append((_Card(8, "WW_352", 3), bury, 3))
    assert len(hand) > MAX_HAND_SPELLS_FOR_SEARCH

    taunts = [_taunt(entity_id=54, card_id="DEEP_005")]
    fighters = [
        _fighter(entity_id=1, atk=7, health=8),
        _fighter(entity_id=2, atk=2, health=1),
        _fighter(entity_id=3, atk=3, health=8),
    ]
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    checker = LethalChecker(gs)
    kept = checker._trim_hand_spells_for_search(
        hand, available_mana=8, player_id=1,
        enemy_minions=taunts, fighters=fighters, defender_shield=False,
    )
    kept_ids = {c.card_id for c, _, _ in kept}
    assert "CORE_SW_066" in kept_ids, kept_ids
    assert len(kept) <= MAX_HAND_SPELLS_FOR_SEARCH


if __name__ == "__main__":
    test_silence_unlocks_face()
    test_trim_keeps_librarian_when_hand_full()
    print("OK royal librarian trim")
