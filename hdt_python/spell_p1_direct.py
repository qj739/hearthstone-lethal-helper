# spell_p1_direct.py — P1 直伤法术

from __future__ import annotations

import json
from functools import lru_cache
from hdt_python.app_paths import resource_path
from typing import List, Optional, TYPE_CHECKING

from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_optimal_single_target_damage,
    _register,
)

if TYPE_CHECKING:
    from .power_parser import GameState

_ELEMENTAL_RACE = frozenset({"ELEMENTAL", 18})


@lru_cache(maxsize=1)
def _elemental_card_ids() -> frozenset[str]:
    path = resource_path("json", "cards.json")
    if not path.exists():
        return frozenset()
    data = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(
        c["id"] for c in data
        if c.get("type") == "MINION" and c.get("race") == "ELEMENTAL"
    )


def _entity_is_elemental(entity) -> bool:
    tags = getattr(entity, "tags", None) or {}
    race = tags.get("CARDRACE", tags.get("RACE", tags.get("516")))
    if race in _ELEMENTAL_RACE:
        return True
    return bool(tags.get("ELEMENTAL"))


def _fighter_is_elemental(
    fighter: dict,
    *,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> bool:
    if fighter.get("kind") != "minion":
        return False
    cid = fighter.get("card_id") or ""
    if cid and cid in _elemental_card_ids():
        return True
    eid = fighter.get("entity_id")
    if gs is not None and player_id is not None and eid is not None:
        for ent in gs.get_board(player_id):
            if ent.entity_id == eid:
                return _entity_is_elemental(ent)
    return False


def _buff_friendly_elementals(
    fighters: List[dict],
    *,
    bonus_atk: int,
    bonus_health: int,
    mult: int = 1,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> None:
    ba, bh = bonus_atk * mult, bonus_health * mult
    for i, f in enumerate(fighters):
        if f.get("health", 0) <= 0:
            continue
        if not _fighter_is_elemental(f, gs=gs, player_id=player_id):
            continue
        fighters[i] = dict(f)
        fighters[i]["atk"] = fighters[i].get("atk", 0) + ba
        fighters[i]["health"] = fighters[i].get("health", 0) + bh


def _stored_spell_damage(card, default: int) -> int:
    if card is None:
        return default
    stored = getattr(card, "stored_damage", None)
    if stored is not None and int(stored) > 0:
        return int(stored)
    tags = getattr(card, "tags", None) or {}
    for key in ("TAG_SCRIPT_DATA_NUM_1", "STORED_DAMAGE"):
        tag = tags.get(key)
        if tag is not None and int(tag) > 0:
            return int(tag)
    bonus = int(tags.get("CURRENT_SPELLPOWER_BASE", 0) or 0)
    return default + bonus


def _apply_dragonbane_shot(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_fire_breath(taunts, fighters, *, mult, enemy_shield, gs=None, player_id=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """喷吐火焰：4 伤单目标 + 己方元素 +1/+1。"""
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    _buff_friendly_elementals(
        fighters, bonus_atk=1, bonus_health=1, mult=mult,
        gs=gs, player_id=player_id,
    )
    return res


def _apply_moonfire(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    dmg = _sd(_stored_spell_damage(card, 1), mult=mult, spell_power=spell_power)
    return _apply_optimal_single_target_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )


def _apply_starfire(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    dmg = _sd(_stored_spell_damage(card, 5), mult=mult, spell_power=spell_power)
    return _apply_optimal_single_target_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )


def _register_p1_direct() -> None:
    specs = [
        (("ONY_010",), 2, "灭龙射击", _apply_dragonbane_shot, False),
        (("DINO_406",), 3, "喷吐火焰", _apply_fire_breath, False),
        (("CS2_008",), 0, "月火术", _apply_moonfire, False),
        (("EX1_173", "VAN_EX1_173"), 6, "星火术", _apply_starfire, False),
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


_register_p1_direct()
