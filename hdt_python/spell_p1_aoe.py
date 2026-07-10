# spell_p1_aoe.py — P1 复杂 AOE 法术

from __future__ import annotations

import random
from copy import deepcopy
from typing import Optional

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_defile,
    _apply_enemy_minions_aoe,
    _apply_random_split_damage,
    _destroy_enemy_minion,
    _lethal_target_enemy_minions,
    _register,
)

MC_DEFAULT_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _apply_broxigars_last_stand(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """布洛克斯加的奋战：全场 1 伤循环直至无死亡（抽牌 v1 不计）。"""
    return _apply_defile(taunts, fighters, mult=mult, enemy_shield=enemy_shield)


def _apply_death_roll(taunts, fighters, *, mult, enemy_shield, rng=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """死亡翻滚：消灭敌方随从，按其攻击力随机分配到所有敌人。"""
    living = _lethal_target_enemy_minions(taunts)
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    best_atk = 0

    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            None,
        )
        if target is None or target.get("health", 0) <= 0:
            continue
        atk = int(target.get("atk", 0) or 0)
        _destroy_enemy_minion(target, ts, fs)
        split = _apply_random_split_damage(
            ts, fs, _sd(atk, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
            rng=_rng(rng), include_enemy_hero=True,
        )
        score = (
            (split.direct_face_damage or 0)
            + project_board_face_after_spell(ts, fs, enemy_shield)
        )
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")
            best_atk = atk

    if best_eid is None:
        return SpellApplyResult()

    target = next(
        (x for x in taunts if x.get("entity_id") == best_eid and x.get("health", 0) > 0),
        None,
    )
    if target is None:
        return SpellApplyResult()

    _destroy_enemy_minion(target, taunts, fighters)
    split = _apply_random_split_damage(
        taunts, fighters, _sd(best_atk, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        rng=_rng(rng), include_enemy_hero=True,
    )
    return split


def _apply_table_flip(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """掀桌子：对所有敌方随从 3 伤（减费 v1 不模拟）。"""
    return _apply_enemy_minions_aoe(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _register_p1_aoe() -> None:
    specs = [
        (("CATA_526",), 2, "布洛克斯加的奋战", _apply_broxigars_last_stand, False),
        (("VAC_416",), 5, "死亡翻滚", _apply_death_roll, True),
        (("TOY_883",), 10, "掀桌子", _apply_table_flip, False),
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


_register_p1_aoe()
