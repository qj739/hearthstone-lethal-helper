# combo_p0.py — 竞技场连击随从（6 张，TOY_516 由 rush_p0 处理）

from __future__ import annotations

from copy import deepcopy
from typing import List, Optional, TYPE_CHECKING

from .combo_board import _register_combo
from .combat_sim import project_board_face_after_spell
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _add_temp_hero_attack,
    _lethal_target_enemy_minions,
    _summon_friendly_fighter,
    hand_effect_active,
)
from .spell_p0_remove import _apply_optimal_destroy_any_minion

if TYPE_CHECKING:
    from .power_parser import Entity, GameState


def _score_board_face(
    taunts: List[dict],
    fighters: List[dict],
    enemy_shield: bool,
) -> int:
    return project_board_face_after_spell(taunts, fighters, enemy_shield) or 0


def _bounce_enemy_minion(target: dict, taunts: List[dict]) -> None:
    """移回手牌：从场面移除，不触发亡语。"""
    eid = target.get("entity_id")
    taunts[:] = [
        t for t in taunts
        if t.get("entity_id") != eid or t.get("health", 0) <= 0 or t.get("kind") == "hero"
    ]


def _apply_optimal_bounce_enemy(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """弹回最优敌方随从（有嘲讽时仅嘲讽）。"""
    living = _lethal_target_enemy_minions(taunts)
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            None,
        )
        if target is None or target.get("health", 0) <= 0:
            continue
        _bounce_enemy_minion(target, ts)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")

    if best_eid is None:
        return SpellApplyResult()
    for unit in taunts:
        if unit.get("entity_id") == best_eid and unit.get("health", 0) > 0:
            _bounce_enemy_minion(unit, taunts)
            break
    return SpellApplyResult()


def _summon_combo_body(
    fighters: List[dict],
    atk: int,
    hp: int,
    card_id: str,
    *,
    mult: int = 1,
) -> None:
    _summon_friendly_fighter(fighters, atk * mult, hp * mult, card_id=card_id)


def _combo_effect_active(
    card: Optional["Entity"],
    *,
    combo_active: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> bool:
    return hand_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    )


def _apply_vilespine_slayer(
    t, f, *, mult, card=None, enemy_shield=False,
    combo_active=False, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """邪脊吞噬者：亮边连击消灭一个随从。"""
    _summon_combo_body(f, 3, 4, "UNG_064", mult=mult)
    if _combo_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ):
        _apply_optimal_destroy_any_minion(t, f, enemy_shield=enemy_shield)
    return SpellApplyResult()


def _apply_bootstrap_sunkeneer(
    t, f, *, mult, card=None, enemy_shield=False,
    combo_active=False, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """镣铐水鬼：亮边连击将敌方随从移出场面（置入牌库底，v1 等同移除）。"""
    _summon_combo_body(f, 4, 4, "TSC_933", mult=mult)
    if _combo_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ):
        _apply_optimal_bounce_enemy(t, f, enemy_shield=enemy_shield)
    return SpellApplyResult()


def _apply_evil_miscreant(t, f, *, mult, **_kw) -> SpellApplyResult:
    """怪盗恶棍：亮边连击获取 2 张跟班（入手牌，当回合无场攻）。"""
    _summon_combo_body(f, 1, 5, "DAL_415", mult=mult)
    return SpellApplyResult()


def _apply_neferset_weaponsmith(
    t, f, *, mult, card=None, gs=None, player_id=None,
    combo_active=False, **_kw,
) -> SpellApplyResult:
    """奈法瑞特武器匠：战吼发现武器 v1 不模拟；亮边连击武器 +2 攻。"""
    _summon_combo_body(f, 5, 4, "TLC_516", mult=mult)
    if (
        _combo_effect_active(
            card, combo_active=combo_active, gs=gs, player_id=player_id,
        )
        and gs is not None
        and player_id is not None
    ):
        weapon = gs.get_weapon(player_id)
        if weapon and weapon.current_durability > 0:
            _add_temp_hero_attack(f, 2 * mult)
    return SpellApplyResult()


def _apply_eredar_skulker(
    t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """艾瑞达潜藏者：亮边连击 +2 攻（3/3，当回合不能攻击）。"""
    atk, hp = 1, 3
    if _combo_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ):
        atk += 2
    _summon_combo_body(f, atk, hp, "GDB_870", mult=mult)
    return SpellApplyResult()


def _register_p0_combo() -> None:
    specs = [
        (("UNG_064",), 5, "邪脊吞噬者", _apply_vilespine_slayer, False),
        (("TSC_933",), 5, "镣铐水鬼", _apply_bootstrap_sunkeneer, False),
        (("DAL_415",), 3, "怪盗恶棍", _apply_evil_miscreant, False),
        (("TLC_516",), 4, "奈法瑞特武器匠", _apply_neferset_weaponsmith, False),
        (("GDB_870",), 2, "艾瑞达潜藏者", _apply_eredar_skulker, False),
    ]
    for card_ids, cost, name, fn, uses_random in specs:
        _register_combo(
            BoardSpellDef(
                card_ids=card_ids,
                base_cost=cost,
                name=name,
                apply=fn,
                uses_random=uses_random,
            )
        )


_register_p0_combo()
