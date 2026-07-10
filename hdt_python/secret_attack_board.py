"""奥秘/光环类攻击时加成（十字军光环等）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import GameState

# 十字军光环：随从攻击时 +2/+2（伤害在攻击结算前生效）
CRUSADER_AURA_CARD_IDS = frozenset({
    "LEG_TTN_908",
    "TTN_908",
})


def player_has_crusader_aura(gs: "GameState", player_id: int) -> bool:
    """己方 SECRET 区是否挂着十字军光环。"""
    for e in gs.get_player_entities(player_id, "SECRET"):
        cid = e.card_id or ""
        if cid in CRUSADER_AURA_CARD_IDS:
            return True
    return False


def stamp_crusader_aura_on_fighter(fighter: dict, gs: "GameState", player_id: int) -> None:
    """随从攻击时由十字军光环触发 +2 攻（至结算伤害）。"""
    if fighter.get("kind") != "minion":
        return
    if player_has_crusader_aura(gs, player_id):
        fighter["crusader_aura_on_attack"] = True


def crusader_strike_attack(fighter: dict) -> int:
    """本次攻击的有效攻击力（含十字军光环攻击前加成）。"""
    atk = int(fighter.get("atk", 0) or 0)
    if fighter.get("crusader_aura_on_attack"):
        atk += 2
    return atk


def apply_crusader_buff_after_strike(fighter: dict) -> None:
    """攻击后随从获得 +2/+2（影响同回合后续攻击）。"""
    if not fighter.get("crusader_aura_on_attack"):
        return
    fighter["atk"] = int(fighter.get("atk", 0) or 0) + 2
    fighter["health"] = int(fighter.get("health", 0) or 0) + 2


def minion_face_hits_with_crusader(
    base_atk: int,
    attacks: int,
    *,
    secret_active: bool,
) -> list[int]:
    """无嘲讽场面：随从每次打脸伤害列表（含十字军光环叠攻）。"""
    if attacks <= 0 or base_atk <= 0:
        return []
    hits: list[int] = []
    running = base_atk
    for _ in range(attacks):
        hit = running + (2 if secret_active else 0)
        hits.append(hit)
        if secret_active:
            running += 2
    return hits
