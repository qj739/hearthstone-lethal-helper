# end_turn_hand_board.py — 手牌回合结束随从（打出后当回合触发 END_TURN）

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_attack, hand_minion_cost, hand_minion_health
from .end_turn_board import (
    END_TURN_BY_CARD,
    HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS,
    _end_turn_def_uses_random,
    _resolve_end_turn_def,
)
from .spell_board import BoardSpellDef, SpellApplyResult, _summon_friendly_fighter

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_END_TURN_HAND: Dict[str, BoardSpellDef] = {}

# 可从手牌打出并当回合结算回合结束效果
HAND_END_TURN_PLAY_IDS = frozenset({
    "EDR_453",   # 棘嗣幼龙（溢出随机）
    "RLK_720",   # 侏儒嚼嚼怪（打最低生命敌人）
})


def _register_hand_end_turn(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_END_TURN_HAND[cid] = defn


def sequence_has_random_end_turn_hand(sequence: List) -> bool:
    """手牌打出后当回合触发的随机回合结束效果（如棘嗣幼龙）。"""
    for step in sequence:
        defn = step[0]
        for cid in getattr(defn, "card_ids", ()):
            if cid not in HAND_END_TURN_PLAY_IDS and not (
                cid.startswith("CORE_") and cid[5:] in HAND_END_TURN_PLAY_IDS
            ):
                continue
            et = _resolve_end_turn_def(cid)
            if _end_turn_def_uses_random(et):
                return True
    return False


def get_hand_end_turn_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_END_TURN_HAND:
        return BOARD_END_TURN_HAND[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_END_TURN_HAND.get(card_id[5:])
    return BOARD_END_TURN_HAND.get("CORE_" + card_id)


def _apply_play_end_turn_minion(
    _t,
    fighters: List[dict],
    *,
    mult: int = 1,
    card: Optional["Entity"] = None,
    **_kw,
) -> SpellApplyResult:
    """打出回合结束随从：召唤失调，标记 sim_summon 供 end_turn 与 hold-attack 识别。"""
    if card is None:
        return SpellApplyResult()
    cid = card.card_id or ""
    atk = hand_minion_attack(card) * mult
    hp = hand_minion_health(card) * mult
    _summon_friendly_fighter(fighters, atk, hp, card_id=cid)
    fighters[-1]["sim_summon"] = True
    return SpellApplyResult()


def hand_end_turn_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_minion:
            continue
        cid = card.card_id or ""
        if cid not in HAND_END_TURN_PLAY_IDS and not (
            cid.startswith("CORE_") and cid[5:] in HAND_END_TURN_PLAY_IDS
        ):
            continue
        if cid not in END_TURN_BY_CARD and not (
            cid.startswith("CORE_") and cid[5:] in END_TURN_BY_CARD
        ):
            continue
        defn = get_hand_end_turn_def(cid)
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


def hand_hold_attack_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """手牌棘嗣幼龙等需保留敌方随从作溢出目标的回合结束随从。"""
    return [
        item for item in hand_end_turn_minions(gs, player_id, available_mana)
        if (item[0].card_id or "") in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS
        or (
            (item[0].card_id or "").startswith("CORE_")
            and (item[0].card_id or "")[5:] in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS
        )
    ]


_register_hand_end_turn(BoardSpellDef(
    ("EDR_453",),
    10,
    "棘嗣幼龙",
    _apply_play_end_turn_minion,
))
_register_hand_end_turn(BoardSpellDef(
    ("RLK_720", "CORE_RLK_720"),
    6,
    "侏儒嚼嚼怪",
    _apply_play_end_turn_minion,
))
