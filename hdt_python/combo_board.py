# combo_board.py — 手牌连击随从接入场攻/斩杀模拟

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_cost
from .spell_board import BoardSpellDef

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_COMBO: Dict[str, BoardSpellDef] = {}


def _register_combo(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_COMBO[cid] = defn


def get_combo_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_COMBO:
        return BOARD_COMBO[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_COMBO.get(card_id[5:])
    return BOARD_COMBO.get("CORE_" + card_id)


def hand_combo_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """可打出的手牌连击随从（已排除战吼/突袭已注册项）。"""
    from .battlecry_board import get_battlecry_def
    from .rush_board import get_rush_def

    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_minion:
            continue
        cid = card.card_id or ""
        if get_battlecry_def(cid) or get_rush_def(cid):
            continue
        defn = get_combo_def(cid)
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


# 注册全部竞技场连击随从
from . import combo_p0  # noqa: E402, F401
