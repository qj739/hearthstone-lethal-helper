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
    _mc, prob, uses_random, _top = lc.overlay_face_stats()
    assert uses_random is True
    assert prob >= 0.2


def _minion(gs, eid, pid, atk, health, *, zone_pos=1, dormant=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.atk = atk
    m.health = health
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = health
    m.tags["DAMAGE"] = 0
    m.tags["ZONE_POSITION"] = zone_pos
    if dormant:
        m.tags["DORMANT"] = 1
    return m


def test_missiles_with_board_not_false_certain_lethal():
    """对面有 1/1+2/2+2/1、英雄 7 血时：三飞弹+火冲不能当确定斩（随机打脸约 9%）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=8)
    _hero(gs, 20, 2, dmg=23)  # 7 血
    _minion(gs, 30, 2, 1, 1, zone_pos=1)
    _minion(gs, 31, 2, 2, 2, zone_pos=2)
    _minion(gs, 32, 2, 2, 1, zone_pos=3)
    for i, eid in enumerate((40, 41, 42)):
        _hand_spell(gs, eid, 1, "EX1_277")

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    mc_max, prob, uses_random, _top = lc.overlay_face_stats()
    assert uses_random is True, (face, mc_max, prob, lc.overlay_spell_note())
    # 乐观上限可够斩，但概率远低于红字阈值，不可红
    assert mc_max >= 7 or face >= 6, (face, mc_max, prob)
    assert not lc.overlay_red_prompt_ok(), (face, mc_max, prob, lc.overlay_spell_note())
    assert prob < 0.2, (prob, mc_max, face)


def test_missiles_skip_dormant_certain_lethal():
    """对面仅休眠玛瑟里顿时：飞弹只打脸；火球×2+飞弹+随从应对 19 血确定斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=11)  # 19 血
    dormant = _minion(gs, 30, 2, 12, 12, zone_pos=1, dormant=True)
    dormant.card_id = "TOY_647"
    # 我方 4 攻可打
    mine = _minion(gs, 50, 1, 4, 2, zone_pos=1)
    mine.tags["1196"] = 0
    mine.tags["EXHAUSTED"] = 0
    mine.tags["NUM_TURNS_IN_PLAY"] = 2
    mine.tags["NUM_ATTACKS_THIS_TURN"] = 0
    _hand_spell(gs, 40, 1, "EX1_277", cost=1)
    _hand_spell(gs, 41, 1, "CORE_CS2_029", cost=4)  # 火球
    _hand_spell(gs, 42, 1, "CORE_CS2_029", cost=4)

    # 单次：休眠不进池 → 3 点全打脸
    res = _apply_arcane_missiles(
        [{"entity_id": 30, "health": 12, "atk": 12, "dormant": True}],
        [],
        mult=1,
        enemy_shield=False,
        rng=random.Random(0),
    )
    assert res.direct_face_damage == 3, res.direct_face_damage

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    mc_max, prob, uses_random, _top = lc.overlay_face_stats()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert face >= 19, (face, lc.overlay_spell_note())
    assert has_lethal, (face, mc_max, prob, uses_random, lc.overlay_spell_note())
    assert lc.overlay_red_prompt_ok(), (face, mc_max, prob)
    # 休眠被排除后飞弹无随机目标，应视为确定线（或不依赖低概率）
    assert prob >= 0.99 or uses_random is False, (prob, uses_random)
    print("OK dormant missiles lethal", face, prob, lc.overlay_spell_note())


if __name__ == "__main__":
    test_registered()
    test_empty_board_all_face()
    test_spell_power_scales()
    test_atiesh_double()
    test_hand_and_lethal_empty_board()
    test_missiles_with_board_not_false_certain_lethal()
    test_missiles_skip_dormant_certain_lethal()
    print("ok")
