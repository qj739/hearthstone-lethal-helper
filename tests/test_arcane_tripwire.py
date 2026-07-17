#!/usr/bin/env python3
"""奥术绊索 JAIL_881：5 伤随机分配到所有敌人（含英雄）。"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def, hand_board_spells
from hdt_python.spell_p0_aoe import _apply_arcane_tripwire


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


def _hand_spell(gs, eid, pid, card_id, *, cost=3):
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
    for cid in ("JAIL_881", "JAIL_881t"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name == "奥术绊索"
        assert defn.base_cost == 3
        assert defn.uses_random is True


def test_empty_board_all_face():
    res = _apply_arcane_tripwire(
        [], [], mult=1, enemy_shield=False, rng=random.Random(0),
    )
    assert res.direct_face_damage == 5


def test_spell_power_scales():
    res = _apply_arcane_tripwire(
        [], [], mult=1, enemy_shield=False, spell_power=1, rng=random.Random(0),
    )
    assert res.direct_face_damage == 6


def test_hand_and_lethal_empty_board():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=3)
    _hero(gs, 20, 2, dmg=26)  # 敌 4 血；绊索空场 5 伤
    _hand_spell(gs, 40, 1, "JAIL_881")

    plays = hand_board_spells(gs, 1, 3)
    assert any(c.card_id == "JAIL_881" for c, _, _ in plays)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 5, (face, lc.overlay_combo_display_lines(), lc.overlay_spell_note())
    _, _, lethal = lc.calculate_lethal_potential()
    assert lethal, (face, lc.overlay_combo_display_lines())


def test_token_also_registered():
    defn = get_board_spell_def("JAIL_881t")
    spell = type("C", (), {"card_id": "JAIL_881t", "entity_id": 11, "tags": {}})()
    fighters = []
    apply_spell_sequence([], fighters, [(defn, 3, spell)], rng=random.Random(1))
    # 空场全打脸：sequence 的 face 在结果里；这里仅确认可 apply 不炸
    assert defn.apply is not None


if __name__ == "__main__":
    test_registered()
    test_empty_board_all_face()
    test_spell_power_scales()
    test_hand_and_lethal_empty_board()
    test_token_also_registered()
    print("ok")
