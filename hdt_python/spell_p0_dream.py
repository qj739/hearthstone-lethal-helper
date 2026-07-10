"""伊瑟拉梦境池中的 3 张法术：梦境 / 伊瑟拉苏醒 / 梦魇（DREAM_01/02/05）。"""

from __future__ import annotations

from copy import deepcopy
from typing import List

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_enemies_damage,
    _apply_damage,
    _destroy_enemy_minion,
    _iter_spell_minion_target_indices,
    _register,
    _remove_dead_taunts,
)

# 伊瑟拉苏醒：不对伊瑟拉本体造成伤害
YSERA_MINION_IDS = frozenset({
    "EX1_572", "CORE_EX1_572", "EDR_100", "EDR_100t",
})


def _apply_dream(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    card=None,
    **_kw,
) -> SpellApplyResult:
    """梦境：将一个随从移回其拥有者的手牌（v1 按移出场面处理；有嘲讽时仅嘲讽）。"""
    indices = _iter_spell_minion_target_indices(taunts, card=card)
    if not indices:
        return SpellApplyResult()

    best_score = -1
    best_idx: int | None = None
    for i in indices:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        _destroy_enemy_minion(ts[i], ts, fs)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return SpellApplyResult()
    _destroy_enemy_minion(taunts[best_idx], taunts, fighters)
    return SpellApplyResult()


def _apply_ysera_awakens(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    spell_power=0, **_kw,
) -> SpellApplyResult:
    """伊瑟拉苏醒：除伊瑟拉外，对所有角色造成 5 点伤害。"""
    dmg = _sd(5, mult=mult, spell_power=spell_power)
    res = _apply_all_enemies_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )
    for f in fighters:
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        if f.get("card_id") in YSERA_MINION_IDS:
            continue
        res.opponent_lifesteal_heal += _apply_damage(
            f, dmg, taunts=taunts, fighters=fighters,
        )
    _remove_dead_taunts(taunts)
    res.self_hero_damage = dmg
    return res


def _apply_nightmare(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    spell_power=0, **_kw,
) -> SpellApplyResult:
    """梦魇：+5/+5，下回合初消灭（v1 只模拟当回合 +5 攻）。"""
    bonus = _sd(5, mult=mult, spell_power=spell_power)
    best_score = -1
    best_idx: int | None = None

    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        fs = deepcopy(fighters)
        ts = deepcopy(taunts)
        fs[i] = dict(fs[i])
        fs[i]["atk"] = fs[i].get("atk", 0) + bonus
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is not None:
        fighters[best_idx]["atk"] = fighters[best_idx].get("atk", 0) + bonus
    return SpellApplyResult()


_register(BoardSpellDef(
    card_ids=("DREAM_01",),
    base_cost=0,
    name="梦境",
    apply=_apply_dream,
))

_register(BoardSpellDef(
    card_ids=("DREAM_02",),
    base_cost=2,
    name="伊瑟拉苏醒",
    apply=_apply_ysera_awakens,
))

_register(BoardSpellDef(
    card_ids=("DREAM_05",),
    base_cost=0,
    name="梦魇",
    apply=_apply_nightmare,
))
