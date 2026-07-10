# reborn.py — 复生：普通 1 血 / 黑暗之赐满血

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

# 黑暗之赐「回荡恐怖 / Persisting Horror」：复生满血并保留附魔
_DARK_GIFT_FULL_REBORN_GIFT_IDS = frozenset({"EDR_100t9"})
_DARK_GIFT_FULL_REBORN_ENCH_IDS = frozenset({"EDR_100t9e"})


def _is_full_reborn_gift_card(card_id: str) -> bool:
    if not card_id:
        return False
    if card_id in _DARK_GIFT_FULL_REBORN_GIFT_IDS:
        return True
    if card_id in _DARK_GIFT_FULL_REBORN_ENCH_IDS:
        return True
    return card_id.startswith("EDR_100t9")


def entity_has_reborn(entity: "Entity") -> bool:
    return int(entity.tags.get("REBORN", 0) or 0) == 1


def entity_reborn_already_used(entity: "Entity") -> bool:
    return int(entity.tags.get("HAS_BEEN_REBORN", 0) or 0) == 1


def entity_reborn_full_health(gs: "GameState", entity: "Entity") -> bool:
    """黑暗之赐复生：满血复活（非普通 1 血）。"""
    eid = entity.entity_id
    for e in list(gs.entities.values()):
        if e.cardtype != "ENCHANTMENT":
            continue
        if int(e.tags.get("ATTACHED", 0) or 0) != eid:
            continue
        if _is_full_reborn_gift_card(e.card_id or ""):
            return True
    gift_ref = entity.tags.get("HAS_DARK_GIFT")
    if gift_ref:
        gift = gs.get_entity(int(gift_ref))
        if gift and _is_full_reborn_gift_card(gift.card_id or ""):
            return True
    return False


def entity_reborn_flags(
    gs: "GameState", entity: "Entity",
) -> Tuple[bool, bool, int]:
    """
    从场面实体提取复生模拟字段。
    返回 (仍有复生次数, 是否满血复生, max_health)。
    """
    max_hp = max(int(entity.health or 0), entity.current_health, 1)
    if entity_reborn_already_used(entity):
        return False, False, max_hp
    if not entity_has_reborn(entity):
        return False, False, max_hp
    return True, entity_reborn_full_health(gs, entity), max_hp


def try_reborn_revive(unit: dict) -> bool:
    """
    随从因伤害死亡时尝试复生；成功则原地复活并返回 True。
    消灭类效果不应调用此函数。
    """
    if unit.get("health", 0) > 0:
        return False
    if unit.get("kind") == "hero":
        return False
    if not unit.get("reborn") or unit.get("reborn_used"):
        return False
    if unit.get("reborn_full_health"):
        unit["health"] = max(int(unit.get("max_health", 1) or 1), 1)
    else:
        unit["health"] = 1
    unit["reborn"] = False
    unit["reborn_used"] = True
    unit["shield"] = False
    return True
