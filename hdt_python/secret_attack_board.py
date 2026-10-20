"""奥秘/光环类攻击时加成（十字军光环、军情七处杀手等）。"""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import GameState

# 十字军光环：随从攻击时 +2/+2（伤害在攻击结算前生效）
CRUSADER_AURA_CARD_IDS = frozenset({
    "LEG_TTN_908",
    "TTN_908",
})

# CAP_000 军情七处杀手：每当一个潜行的友方随从攻击，使其获得 +2/+2
SI7_SLAYER_CARD_IDS = frozenset({"CAP_000"})


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


def _si7_slayer_alive(unit: dict) -> bool:
    return (
        (unit.get("card_id") or "") in SI7_SLAYER_CARD_IDS
        and unit.get("kind") == "minion"
        and int(unit.get("health", 0) or 0) > 0
        and not unit.get("silenced")
        and not unit.get("dormant")
    )


def fighters_have_si7_slayer(fighters: Iterable[dict] | None) -> bool:
    return any(_si7_slayer_alive(f) for f in (fighters or ()))


def player_has_si7_slayer(gs: "GameState | None", player_id: int | None) -> bool:
    """场上是否有存活且未沉默的军情七处杀手。"""
    if gs is None or player_id is None:
        return False
    from .board_damage import is_dormant, is_silenced

    for m in gs.get_board(player_id):
        if (m.card_id or "") not in SI7_SLAYER_CARD_IDS:
            continue
        if int(getattr(m, "current_health", 0) or 0) <= 0:
            continue
        if is_silenced(m) or is_dormant(m, gs):
            continue
        return True
    return False


def stamp_si7_slayer_on_fighter(
    fighter: dict, gs: "GameState | None", player_id: int | None,
) -> None:
    """标记：攻击时若仍潜行，则由军情七处杀手触发 +2/+2。"""
    if fighter.get("kind") != "minion":
        return
    if player_has_si7_slayer(gs, player_id):
        fighter["si7_slayer_on_attack"] = True


def stamp_si7_slayer_aura_on_fighters(fighters: list[dict]) -> None:
    """手牌打出杀手后：按 fighters 列表重打光环标记。"""
    active = fighters_have_si7_slayer(fighters)
    for f in fighters:
        if f.get("kind") != "minion":
            continue
        if active and int(f.get("health", 0) or 0) > 0:
            f["si7_slayer_on_attack"] = True
        else:
            f.pop("si7_slayer_on_attack", None)


def _si7_slayer_triggers(fighter: dict) -> bool:
    return bool(fighter.get("si7_slayer_on_attack") and fighter.get("stealth"))


def crusader_strike_attack(fighter: dict) -> int:
    """本次攻击的有效攻击力（含十字军 / 军情七处杀手攻击前加成）。"""
    atk = int(fighter.get("atk", 0) or 0)
    if fighter.get("crusader_aura_on_attack"):
        atk += 2
    if _si7_slayer_triggers(fighter):
        atk += 2
    return atk


def apply_crusader_buff_after_strike(fighter: dict) -> None:
    """攻击后随从获得攻击时加成的 +2/+2（影响同回合后续攻击）。"""
    if fighter.get("crusader_aura_on_attack"):
        fighter["atk"] = int(fighter.get("atk", 0) or 0) + 2
        fighter["health"] = int(fighter.get("health", 0) or 0) + 2
    if _si7_slayer_triggers(fighter):
        fighter["atk"] = int(fighter.get("atk", 0) or 0) + 2
        fighter["health"] = int(fighter.get("health", 0) or 0) + 2
        fighter["stealth"] = False


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
