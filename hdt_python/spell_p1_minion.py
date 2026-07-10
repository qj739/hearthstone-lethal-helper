# spell_p1_minion.py — P1 解场伤法术

from __future__ import annotations

from copy import deepcopy
from typing import Optional

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_best_minion_damage,
    _apply_damage_to_unit,
    _iter_spell_minion_target_indices,
    _register,
    _remove_dead_taunts,
)


def _apply_spirit_bond(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """灵魂联结：3 伤；击杀召唤 3/2 突袭狼。"""
    return _apply_best_minion_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        summon_on_kill=(3, 2, True),
        **_kw,
    )


def _apply_unstable_shadow_blast(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """不稳定的暗影震爆：6 伤；溢出伤害命中我方英雄。"""
    amount = _sd(6, mult=mult, spell_power=spell_power)
    if amount <= 0:
        return SpellApplyResult()

    best_score = -1
    best_idx: Optional[int] = None

    for i in _iter_spell_minion_target_indices(taunts, card=card):
        t = taunts[i]
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            ts[i],
        )
        _, _, dealt = _apply_damage_to_unit(
            target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return SpellApplyResult()

    res = SpellApplyResult()
    target = taunts[best_idx]
    heal, _, dealt = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    res.self_hero_damage = max(0, amount - dealt)
    _remove_dead_taunts(taunts)
    return res


def _register_p1_minion() -> None:
    specs = [
        (("EDR_262",), 3, "灵魂联结", _apply_spirit_bond, False),
        (("WC_021",), 2, "不稳定的暗影震爆", _apply_unstable_shadow_blast, False),
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


_register_p1_minion()
