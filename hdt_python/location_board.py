# location_board.py — 场面地标接入场攻/斩杀模拟

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import entity_cardtype, entity_zone
from .spell_board import BoardSpellDef

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_LOCATION: Dict[str, BoardSpellDef] = {}


def _register_location(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_LOCATION[cid] = defn


def get_location_def(card_id: str) -> Optional[BoardSpellDef]:
    if not card_id:
        return None
    if card_id in BOARD_LOCATION:
        return BOARD_LOCATION[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_LOCATION.get(card_id[5:])
    return BOARD_LOCATION.get("CORE_" + card_id)


def is_location_entity(entity: "Entity") -> bool:
    if entity_cardtype(entity) == "LOCATION":
        return True
    cid = entity.card_id or ""
    return get_location_def(cid) is not None


def location_durability(entity: "Entity") -> int:
    hp = entity.health if entity.health > 0 else int(entity.tags.get("HEALTH", 0) or 0)
    dmg = entity.damage if entity.damage else int(entity.tags.get("DAMAGE", 0) or 0)
    return max(0, hp - dmg)


def location_is_ready(entity: "Entity") -> bool:
    """地标可激活：有耐久、未 EXHAUSTED、无 LOCATION_ACTION_COOLDOWN。"""
    if location_durability(entity) <= 0:
        return False
    if int(entity.tags.get("EXHAUSTED", 0) or 0) == 1:
        return False
    if int(entity.tags.get("LOCATION_ACTION_COOLDOWN", 0) or 0) == 1:
        return False
    return True


def get_board_locations(gs: "GameState", player_id: int) -> List["Entity"]:
    """我方场上地标（PLAY 区，有耐久）。"""
    out: List["Entity"] = []
    for entity in list(gs.entities.values()):
        if not gs.is_entity_controlled_by(entity, player_id):
            continue
        if entity_zone(entity) != "PLAY":
            continue
        if not is_location_entity(entity):
            continue
        if location_durability(entity) <= 0:
            continue
        out.append(entity)
    out.sort(key=lambda e: int(e.tags.get("ZONE_POSITION", 0) or 0))
    return out


def board_location_plays(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """可激活地标（0 费，消耗耐久）；无合法目标时不列入。"""
    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for loc in get_board_locations(gs, player_id):
        if not location_is_ready(loc):
            continue
        defn = get_location_def(loc.card_id or "")
        if not defn:
            continue
        from .location_p0 import location_has_valid_target

        if not location_has_valid_target(defn, gs, player_id):
            continue
        result.append((loc, defn, 0))
    return result


from . import location_p0  # noqa: E402, F401
