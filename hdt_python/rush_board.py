# rush_board.py — 手牌突袭随从接入场攻/斩杀模拟

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_cost, hand_minion_has_rush
from .spell_board import BoardSpellDef, hand_board_spells

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_RUSH: Dict[str, BoardSpellDef] = {}


def _register_rush(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_RUSH[cid] = defn


def get_rush_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_RUSH:
        return BOARD_RUSH[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_RUSH.get(card_id[5:])
    return BOARD_RUSH.get("CORE_" + card_id)


def hand_rush_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """可打出的手牌突袭随从（已排除 BOARD_BATTLECRY 已注册项）。"""
    from .battlecry_board import get_battlecry_def
    from .rush_combat import SHADEHOUND_CARD_IDS

    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        cid = card.card_id or ""
        # 注能影犬：牌面/高亮后应为突袭；日志偶发尚未写上 RUSH 时也认
        infused_shadehound = (
            cid in SHADEHOUND_CARD_IDS
            and (
                cid.endswith("t")
                or int(card.tags.get("INFUSED", 0) or 0) == 1
                or int(card.tags.get("RUSH", 0) or 0) == 1
            )
        )
        if not hand_minion_has_rush(card) and not infused_shadehound:
            continue
        if get_battlecry_def(cid):
            continue
        defn = get_rush_def(cid)
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


def hand_all_board_plays_with_rush(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """手牌法术 + 战吼随从 + 突袭随从。"""
    from .battlecry_board import hand_battlecry_minions

    return (
        hand_board_spells(gs, player_id, available_mana)
        + hand_battlecry_minions(gs, player_id, available_mana)
        + hand_rush_minions(gs, player_id, available_mana)
    )


# 注册全部竞技场突袭随从（rush_p0 覆盖特殊战吼）
from . import rush_p0  # noqa: E402, F401
