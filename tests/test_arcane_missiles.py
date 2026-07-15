#!/usr/bin/env python3
"""奥术飞弹 EX1_277：3 伤随机分配到所有敌人（含英雄）。"""

import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells, apply_spell_sequence
from hdt_python.spell_p0_aoe import _apply_arcane_missiles


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, card_id, *, cost=1):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def test_registered():
    for cid in ("EX1_277", "CORE_EX1_277", "VAN_EX1_277"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name == "奥术飞弹"
        assert defn.base_cost == 1
        assert defn.uses_random is True


def test_empty_board_all_face():
    res = _apply_arcane_missiles(
        [], [], mult=1, enemy_shield=False, rng=random.Random(0),
    )
    assert res.direct_face_damage == 3


def test_spell_power_scales():
    res = _apply_arcane_missiles(
        [], [], mult=1, enemy_shield=False, spell_power=2, rng=random.Random(0),
    )
    assert res.direct_face_damage == 5  # (3+2)


def test_atiesh_double():
    res = _apply_arcane_missiles(
        [], [], mult=2, enemy_shield=False, rng=random.Random(0),
    )
    assert res.direct_face_damage == 6


def test_hand_and_lethal_empty_board():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=1)
    _hero(gs, 20, 2, dmg=28)  # 敌 2 血；飞弹期望伤 3（随机上界/空场）
    _hand_spell(gs, 40, 1, "EX1_277")

    plays = hand_board_spells(gs, 1, 1)
    assert any(c.card_id == "EX1_277" for c, _, _ in plays)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 3, (face, lc.overlay_combo_display_lines(), lc.overlay_spell_note())
    _, _, lethal = lc.calculate_lethal_potential()
    assert lethal, (face, lc.overlay_combo_display_lines())


if __name__ == "__main__":
    test_registered()
    test_empty_board_all_face()
    test_spell_power_scales()
    test_atiesh_double()
    test_hand_and_lethal_empty_board()
    print("ok")
