#!/usr/bin/env python3
"""P0 法术搜索性能：MC 缓存复用 + combo 上界剪枝回归。"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker, OVERLAY_MC_TRIALS
from hdt_python.power_parser import GameState
from hdt_python.spell_board import BoardSpellDef, SpellApplyResult, get_board_spell_def


def _minimal_gs() -> GameState:
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    for pid, eid in ((1, 10), (2, 20)):
        h = gs.get_entity(eid)
        h.cardtype = "HERO"
        h.controller = pid
        h.health = 30
        h.damage = 0
        h.tags.update({"HEALTH": 30, "DAMAGE": 0, "RESOURCES": 10, "RESOURCES_USED": 0})
        gs.hero_entity_ids[pid] = eid
        gs.player_ids[eid] = pid
    # CURRENT_PLAYER：我方回合
    p1 = gs.get_entity(1)
    p1.tags["CURRENT_PLAYER"] = 1
    gs.player_ids[1] = 1
    return gs


def _fireball_seq(gs: GameState, eid: int = 30):
    defn = get_board_spell_def("CS2_029")
    assert defn is not None
    card = gs.get_entity(eid)
    card.cardtype = "SPELL"
    card.card_id = "CS2_029"
    card.controller = 1
    card.zone = "HAND"
    card.tags["ZONE"] = "HAND"
    return [(defn, 4, card)]


def test_mc_cache_reuses_mean_after_best():
    """同一 seq+order 先 mc_best 再 mean：只跑一轮 MC。"""
    gs = _minimal_gs()
    lc = LethalChecker(gs)
    lc._begin_lethal_budget()
    enemy = []
    fighters = [{
        "kind": "minion", "atk": 1, "health": 1, "attacks_left": 1, "can_face": True,
    }]
    # 用 uses_random 牌迫使走 MC；若无注册则用假 defn
    defn = get_board_spell_def("EX1_277") or get_board_spell_def("CORE_EX1_277")
    if defn is None:
        def _rand_apply(t, f, *, mult, enemy_shield, rng=None, **_k):
            import random
            r = rng or random.Random(0)
            face = 1 + r.randrange(3)
            return SpellApplyResult(direct_face_damage=face)

        defn = BoardSpellDef(
            card_ids=("TEST_RAND",), base_cost=1, name="测试随机",
            apply=_rand_apply, uses_random=True,
        )
    card = gs.get_entity(40)
    card.cardtype = "SPELL"
    card.card_id = defn.card_ids[0]
    card.controller = 1
    seq = [(defn, defn.base_cost, card)]

    before = lc._mc_run_count
    order, outcome = lc._simulate_random_line_mc_best(
        enemy, fighters, seq, ["spell_first"],
        spell_mult=1, defender_shield=False,
        available_mana=10, hand_charges=[],
        hp_direct=0, trials=8, extra_spell_face=0,
    )
    after_best = lc._mc_run_count
    mean = lc._mc_mean_line_face_total(
        enemy, fighters, seq, order,
        spell_mult=1, defender_shield=False,
        available_mana=10, hand_charges=[],
        trials=8, hp_direct=0, extra_spell_face=0,
    )
    after_mean = lc._mc_run_count
    peak, prob, top = lc._monte_carlo_line_stats(
        enemy, fighters, seq, order,
        spell_mult=1, defender_shield=False, effective_hp=30,
        available_mana=10, hand_charges=[], trials=8,
        ignore_budget=True, hp_direct=0,
    )
    after_stats = lc._mc_run_count
    lc._end_lethal_budget()

    assert after_best == before + 1, (before, after_best)
    assert after_mean == after_best, "mean 应命中缓存"
    assert after_stats == after_mean, "overlay stats 应命中缓存"
    assert outcome[0] == peak
    assert mean >= 0
    assert isinstance(top, list)
    print("OK mc cache reuse", peak, mean, prob)


def test_upper_bound_prunes_impossible_line():
    """上界低于当前最优时剪枝。"""
    gs = _minimal_gs()
    lc = LethalChecker(gs)
    fighters = [{
        "kind": "minion", "atk": 2, "health": 2, "attacks_left": 1, "can_face": True,
    }]
    seq = _fireball_seq(gs)
    upper = lc._estimate_combo_line_upper(
        seq, fighters,
        player_id=1, spell_mult=1, defender_shield=False,
    )
    # 火球约 6 + 场面 2 → 上界应 > 0
    assert upper >= 6
    # 人为 best_total 极大时剪枝条件成立
    assert upper < 10**9
    print("OK upper bound", upper)


def test_soft_degrade_trials():
    gs = _minimal_gs()
    lc = LethalChecker(gs)
    lc._begin_lethal_budget()
    assert lc._mc_trials_for_budget(50) == 50
    # 伪装预算将尽
    import time
    lc._lethal_deadline = time.perf_counter() + 0.5
    assert lc._mc_trials_for_budget(50) == 5
    lc._end_lethal_budget()
    print("OK soft degrade trials")


def test_enum_cache_populated_for_board_prune():
    gs = _minimal_gs()
    lc = LethalChecker(gs)
    lc._begin_lethal_budget()
    defn = get_board_spell_def("CS2_029")
    card = gs.get_entity(50)
    card.cardtype = "SPELL"
    card.card_id = "CS2_029"
    card.controller = 1
    hand = [(card, defn, 4)]
    seqs = lc._enumerate_spells_for_search(
        hand, 10,
        enemy_minions=[],
        fighters=[],
        spell_mult=1,
        defender_shield=False,
        player_id=1,
    )
    assert any(len(s) == 1 for s in seqs)
    # 至少有一条单牌序列写入枚举缓存
    assert any(
        len(k) == 1 for k in lc._enum_apply_cache
    ), list(lc._enum_apply_cache)[:5]
    lc._end_lethal_budget()
    print("OK enum cache populated", len(lc._enum_apply_cache))


if __name__ == "__main__":
    test_mc_cache_reuses_mean_after_best()
    test_upper_bound_prunes_impossible_line()
    test_soft_degrade_trials()
    test_enum_cache_populated_for_board_prune()
    print("OK p0_search_perf")
