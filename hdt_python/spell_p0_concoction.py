# spell_p0_concoction.py — 药剂大师普崔塞德（RLK_570）调配药剂（全形态）

from __future__ import annotations

import json
import random
from hdt_python.app_paths import resource_path
from typing import Callable, List, Optional, Tuple

from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_optimal_single_target_damage,
    _apply_random_destroy_enemy_minions,
    _register,
    scaled_spell_damage as _sd,
)

MC_DEFAULT_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _apply_concoction_3(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,
) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters,
        _sd(3, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )


def _apply_concoction_6(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,
) -> SpellApplyResult:
    total = SpellApplyResult()
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    for _ in range(2):
        part = _apply_optimal_single_target_damage(
            taunts, fighters, dmg, enemy_shield=enemy_shield,
        )
        total.direct_face_damage += part.direct_face_damage
        total.opponent_lifesteal_heal += part.opponent_lifesteal_heal
    return total


def _apply_concoction_destroy(
    taunts, fighters, *, count: int, rng=None, **_kw,
) -> SpellApplyResult:
    return _apply_random_destroy_enemy_minions(
        taunts, fighters, count=count, rng=_rng(rng),
    )


def _apply_concoction_3_destroy_1(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw,
) -> SpellApplyResult:
    total = _apply_concoction_3(
        taunts, fighters, mult=mult, enemy_shield=enemy_shield,
        spell_power=spell_power,
    )
    dest = _apply_concoction_destroy(taunts, fighters, count=1, rng=rng)
    total.direct_face_damage += dest.direct_face_damage
    total.opponent_lifesteal_heal += dest.opponent_lifesteal_heal
    return total


def _concoction_handler_from_text(
    text: str,
) -> Optional[Tuple[Callable, bool]]:
    """根据卡牌描述选择模拟 handler；返回 (apply_fn, uses_random)。"""
    t = (text or "").lower().replace("[x]", " ").replace("\n", " ")
    if not t.strip():
        return None
    if "deal $3 damage, twice" in t:
        return _apply_concoction_6, False
    deal3 = "deal $3 damage" in t
    des2 = "destroy two random" in t
    des1 = "destroy a random" in t or "destroy random enemy" in t
    if deal3 and des1:
        return _apply_concoction_3_destroy_1, False
    if deal3:
        return _apply_concoction_3, False
    if des2:
        return lambda *a, **k: _apply_concoction_destroy(*a, count=2, **k), True
    if des1:
        return lambda *a, **k: _apply_concoction_destroy(*a, count=1, **k), True
    return None


def _register_concoctions() -> None:
    path = resource_path("json", "cards.json")
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    seen: set[str] = set()
    for card in data:
        cid = card.get("id") or ""
        if not cid.startswith("RLK_570t") or card.get("type") != "SPELL":
            continue
        if cid in seen:
            continue
        row = _concoction_handler_from_text(card.get("text") or "")
        if row is None:
            continue
        apply_fn, uses_random = row
        cost = int(card.get("cost") or 3)
        name = card.get("name") or cid
        _register(BoardSpellDef(
            (cid,), cost, name, apply_fn, uses_random=uses_random,
        ))
        seen.add(cid)


_register_concoctions()
