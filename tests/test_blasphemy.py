#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""污亵：手牌中法力最高（含并列）时，所有敌人 2 点再来一次。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python import black_empire_p0  # noqa: F401
from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def


class _Card:
    def __init__(self, eid, cid, cost):
        self.entity_id = eid
        self.card_id = cid
        self.cost = cost
        self.tags = {"COST": cost}


class _GS:
    def __init__(self, hand):
        self.hand = hand
        self.player_ids = {}

    def get_hand(self, _pid):
        return self.hand

    def get_board(self, _pid):
        return []

    def get_hero(self, _pid):
        return None

    def get_weapon(self, _pid):
        return None

    def get_entity(self, _eid):
        return None


def _face(defn, hand, *, spent=None):
    taunts = [{"kind": "hero", "health": 20, "armor": 0, "entity_id": 1, "shield": False}]
    card = hand[0]
    res = defn.apply(
        taunts, [], mult=1, enemy_shield=False, spell_power=0,
        card=card, gs=_GS(hand), player_id=1, spent_hand_ids=spent,
    )
    return res.direct_face_damage


def test_repeat_when_highest_or_tied():
    defn = get_board_spell_def("BE_086")
    assert defn is not None and defn.base_cost == 4
    me = _Card(10, "BE_086", 4)
    assert _face(defn, [me]) == 4
    assert _face(defn, [me, _Card(11, "MINION", 4)]) == 4
    assert _face(defn, [me, _Card(12, "MINION", 6)]) == 2
    assert _face(defn, [me, _Card(12, "MINION", 6)], spent={12}) == 4


def test_sequence_spends_higher_card_first():
    defn = get_board_spell_def("BE_086")
    cheap = get_board_spell_def("TIME_026")
    me = _Card(10, "BE_086", 4)
    other = _Card(12, "TIME_026", 6)
    gs = _GS([me, other])
    hero = [{"kind": "hero", "health": 20, "armor": 0, "entity_id": 1, "shield": False}]
    only = apply_spell_sequence(
        hero, [], [(defn, 4, me)], gs=gs, player_id=1, enemy_shield=False,
    )
    assert only.direct_face_damage == 2
    hero2 = [{"kind": "hero", "health": 20, "armor": 0, "entity_id": 1, "shield": False}]
    both = apply_spell_sequence(
        hero2, [], [(cheap, 6, other), (defn, 4, me)],
        gs=gs, player_id=1, enemy_shield=False,
    )
    assert both.direct_face_damage == 4


if __name__ == "__main__":
    test_repeat_when_highest_or_tied()
    test_sequence_spends_higher_card_first()
    print("OK blasphemy")
