# spell_p1_buff.py — P1 加攻法术

from __future__ import annotations

from copy import deepcopy
from typing import List, Optional, Tuple

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _add_temp_hero_attack,
    _friendly_spell_target_minions,
    _register,
)


def _apply_multi_strike(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """多重打击：+2 攻；额外一次仅能攻击敌方随从。"""
    atk = _sd(2, mult=mult, spell_power=spell_power)
    _add_temp_hero_attack(fighters, atk, can_face=True)
    _add_temp_hero_attack(fighters, atk, can_face=False)
    return SpellApplyResult()


def _apply_buffed_fighters(
    fighters: List[dict],
    source: str,
    key: object,
    unit: dict,
    bonus: int,
) -> None:
    if source == "fighter":
        idx = int(key)
        fighters[idx] = dict(fighters[idx])
        fighters[idx]["atk"] = fighters[idx].get("atk", 0) + bonus
        return
    buffed = dict(unit)
    buffed["atk"] = buffed.get("atk", 0) + bonus
    buffed.setdefault("attacks_left", 1 if buffed.get("atk", 0) > 0 else 0)
    buffed.setdefault("can_face", True)
    buffed.setdefault("health", 1)
    buffed.setdefault("kind", "minion")
    fighters.append(buffed)


def _apply_for_quelthalas(taunts, fighters, *, mult, enemy_shield, gs=None, player_id=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """为了奎尔萨拉斯！：友方随从 +3 攻；英雄 +2 攻。魔免随从不可指定，无合法目标则不可打出。"""
    bonus = _sd(3, mult=mult, spell_power=spell_power)
    targets = _friendly_spell_target_minions(fighters, gs=gs, player_id=player_id)
    if not targets:
        return SpellApplyResult()

    best_score = -1
    best_pick: Optional[Tuple[str, object, dict]] = None
    for source, key, unit in targets:
        fs = deepcopy(fighters)
        ts = deepcopy(taunts)
        _apply_buffed_fighters(fs, source, key, unit, bonus)
        _add_temp_hero_attack(fs, _sd(2, mult=mult, spell_power=spell_power))
        score = project_board_face_after_spell(ts, fs, enemy_shield) or 0
        if score > best_score:
            best_score = score
            best_pick = (source, key, unit)

    if best_pick is None:
        return SpellApplyResult()
    source, key, unit = best_pick
    _apply_buffed_fighters(fighters, source, key, unit, bonus)
    _add_temp_hero_attack(fighters, _sd(2, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _register_p1_buff() -> None:
    specs = [
        (("TSC_006",), 2, "多重打击", _apply_multi_strike, False),
        (("RLK_918",), 2, "为了奎尔萨拉斯！", _apply_for_quelthalas, False),
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


_register_p1_buff()
