# spell_p1_other.py — P1 其他法术

from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_damage_to_unit,
    _apply_direct_face,
    _apply_optimal_single_target_damage,
    _can_spell_hit_enemy_face,
    _iter_spell_minion_target_indices,
    _register,
    _remove_dead_taunts,
    _summon_friendly_fighter,
)


def _apply_optimal_friendly_buff(
    taunts: List[dict],
    fighters: List[dict],
    *,
    bonus_atk: int,
    bonus_health: int,
    enemy_shield: bool,
    can_face: Optional[bool] = None,
) -> None:
    best_score = -1
    best_idx: Optional[int] = None
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        fs = deepcopy(fighters)
        ts = deepcopy(taunts)
        fs[i] = dict(fs[i])
        fs[i]["atk"] = fs[i].get("atk", 0) + bonus_atk
        fs[i]["health"] = fs[i].get("health", 0) + bonus_health
        if can_face is not None:
            fs[i]["can_face"] = can_face
        score = project_board_face_after_spell(ts, fs, enemy_shield) or 0
        if score > best_score:
            best_score = score
            best_idx = i
    if best_idx is not None:
        fighters[best_idx]["atk"] = fighters[best_idx].get("atk", 0) + bonus_atk
        fighters[best_idx]["health"] = fighters[best_idx].get("health", 0) + bonus_health
        if can_face is not None:
            fighters[best_idx]["can_face"] = can_face


def _apply_dirge_of_despair(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """绝望哀歌：对任意角色 3 伤；击杀则从牌库召唤恶魔（v1 召唤 3/3 突袭）。"""
    amount = _sd(3, mult=mult, spell_power=spell_power)
    if amount <= 0:
        return SpellApplyResult()

    candidates: List[tuple] = []
    if _can_spell_hit_enemy_face(taunts):
        candidates.append(("enemy_hero", None))
    for i in _iter_spell_minion_target_indices(taunts):
        candidates.append(("enemy_minion", i))
    for i, f in enumerate(fighters):
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            candidates.append(("friendly_minion", i))

    best_score = -1
    best: Optional[tuple] = None

    for kind, idx in candidates:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        killed = False
        if kind == "enemy_hero":
            direct = _apply_direct_face(amount, enemy_shield)
            score = direct.direct_face_damage + project_board_face_after_spell(ts, fs, enemy_shield)
        elif kind == "enemy_minion":
            assert idx is not None
            target = ts[idx]
            was_alive = target.get("health", 0) > 0
            _, face, _ = _apply_damage_to_unit(
                target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
            )
            _remove_dead_taunts(ts)
            if was_alive and target.get("health", 0) <= 0:
                killed = True
                _summon_friendly_fighter(fs, 3, 3, rush=True)
            score = face + project_board_face_after_spell(ts, fs, enemy_shield)
        else:
            assert idx is not None
            target = fs[idx]
            was_alive = target.get("health", 0) > 0
            _apply_damage_to_unit(
                target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
            )
            if was_alive and target.get("health", 0) <= 0:
                killed = True
                _summon_friendly_fighter(fs, 3, 3, rush=True)
            score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best = (kind, idx, killed)

    if best is None:
        return SpellApplyResult()

    kind, idx, _killed = best
    res = SpellApplyResult()
    if kind == "enemy_hero":
        part = _apply_direct_face(amount, enemy_shield)
        res.direct_face_damage = part.direct_face_damage
    elif kind == "enemy_minion":
        assert idx is not None
        target = taunts[idx]
        was_alive = target.get("health", 0) > 0
        heal, face, _ = _apply_damage_to_unit(
            target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal = heal
        res.direct_face_damage = face
        _remove_dead_taunts(taunts)
        if was_alive and target.get("health", 0) <= 0:
            _summon_friendly_fighter(fighters, 3, 3, rush=True)
    else:
        assert idx is not None
        target = fighters[idx]
        was_alive = target.get("health", 0) > 0
        _apply_damage_to_unit(
            target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        if was_alive and target.get("health", 0) <= 0:
            _summon_friendly_fighter(fighters, 3, 3, rush=True)
    return res


def _apply_blessing_of_authority(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """威能祝福：+8/+8；本回合不能攻击英雄。"""
    _apply_optimal_friendly_buff(
        taunts, fighters,
        bonus_atk=_sd(8, mult=mult, spell_power=spell_power), bonus_health=_sd(8, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield, can_face=False,
    )
    return SpellApplyResult()


def _apply_stellar_balance(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """星体平衡：获得月火术、星火术（法术伤害+1 → 2/6 伤）。"""
    res = SpellApplyResult()
    res.add_hand_pending = [
        ("CS2_008", 0, _sd(2, mult=mult, spell_power=spell_power)),
        ("EX1_173", 6, (5 + 1) * mult),
    ]
    return res


def _apply_cursed_souvenir(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """咒怨纪念品：+3/+3（回合开始自伤 v1 不计）。"""
    _apply_optimal_friendly_buff(
        taunts, fighters,
        bonus_atk=_sd(3, mult=mult, spell_power=spell_power), bonus_health=_sd(3, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )
    return SpellApplyResult()


def _apply_demonic_assault(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """恶魔来袭：3 伤 + 两只 1/3 嘲讽虚空行者（当回合失调）。"""
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    for _ in range(_sd(2, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fighters, 1, 3, taunt=True)
    return res


def _register_p1_other() -> None:
    specs = [
        (("ETC_082",), 6, "绝望哀歌", _apply_dirge_of_despair, False),
        (("SCH_138",), 5, "威能祝福", _apply_blessing_of_authority, False),
        (("EDR_874",), 2, "星体平衡", _apply_stellar_balance, False),
        (("VAC_944",), 2, "咒怨纪念品", _apply_cursed_souvenir, False),
        (("SW_088",), 4, "恶魔来袭", _apply_demonic_assault, False),
    ]
    for card_ids, cost, name, fn, uses_random in specs:
        _register(
            BoardSpellDef(
                card_ids=card_ids,
                base_cost=cost,
                name=name,
                apply=fn,
                uses_random=uses_random,
            )
        )


_register_p1_other()
