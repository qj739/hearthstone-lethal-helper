# weapon_board.py — 手牌武器接入场攻/斩杀模拟

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_cost
from .spell_board import BoardSpellDef

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_WEAPON: Dict[str, BoardSpellDef] = {}


def _register_weapon(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_WEAPON[cid] = defn


def get_weapon_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_WEAPON:
        return BOARD_WEAPON[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_WEAPON.get(card_id[5:])
    return BOARD_WEAPON.get("CORE_" + card_id)


def hand_weapons(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_weapon:
            continue
        defn = get_weapon_def(card.card_id or "")
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


from . import weapon_p0  # noqa: E402, F401
