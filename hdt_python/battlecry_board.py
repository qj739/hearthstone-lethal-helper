# battlecry_board.py — 手牌战吼随从接入斩杀/场攻模拟（复用 BoardSpellDef）

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import entity_cardtype, hand_minion_cost
from .spell_board import BoardSpellDef, hand_board_spells

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_BATTLECRY: Dict[str, BoardSpellDef] = {}

from .interleave_board import (
    ATTACK_INTERLEAVE_BATTLECRY_IDS,
    ATTACK_INTERLEAVE_SPELL_IDS,
    BUNKER_SERGEANT_IDS,
    FACELESS_CORRUPTOR_IDS,
    HOSTILE_INVADER_IDS,
    PRE_PLAY_ATTACK_INTERLEAVE_IDS,
    sequence_is_faceless_only,
    sequence_needs_attack_interleave,
    sequence_needs_faceless_interleave,
    step_card_id as _play_step_card_id,
)

TYRANDE_IDS = frozenset({"EDR_464"})
# 战吼后附着英雄：EDR_464e2「Pull of the Moon」
TYRANDE_AURA_ENCHANT_IDS = frozenset({"EDR_464e2"})


def _tyrande_aura_attach_targets(
    game_state: "GameState",
    player_id: int,
) -> set:
    """泰兰德光环 ATTACHED 可能指向英雄实体或 Player 实体（日志常见 ATTACHED=Player EntityID）。"""
    targets: set = set()
    hero = game_state.get_hero(player_id)
    if hero is not None:
        targets.add(hero.entity_id)
    for eid, pid in game_state.player_ids.items():
        if pid == player_id:
            targets.add(eid)
    return targets


def tyrande_double_spells_remaining(
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> int:
    """英雄附着泰兰德光环 EDR_464e2 时，返回剩余可双倍施放的法术次数。"""
    if game_state is None or player_id is None:
        return 0
    attach_targets = _tyrande_aura_attach_targets(game_state, player_id)
    if not attach_targets:
        return 0
    for entity in list(game_state.entities.values()):
        if entity_cardtype(entity) != "ENCHANTMENT":
            continue
        cid = entity.card_id or ""
        if cid not in TYRANDE_AURA_ENCHANT_IDS:
            continue
        attached = int(entity.tags.get("ATTACHED", 0) or 0)
        if attached not in attach_targets:
            continue
        remaining = int(entity.tags.get("TAG_SCRIPT_DATA_NUM_1", 0) or 0)
        return remaining if remaining > 0 else 3
    return 0


def _register_bc(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_BATTLECRY[cid] = defn


def get_battlecry_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_BATTLECRY:
        return BOARD_BATTLECRY[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_BATTLECRY.get(card_id[5:])
    return BOARD_BATTLECRY.get("CORE_" + card_id)


def hand_battlecry_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_minion:
            continue
        defn = get_battlecry_def(card.card_id or "")
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


def hand_all_board_plays(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """手牌法术 + 武器 + 战吼随从 + 突袭随从 + 连击随从（统一枚举顺序）。"""
    from .combo_board import hand_combo_minions
    from .damaged_spell_power import hand_damaged_spellpower_minions
    from .end_turn_hand_board import hand_end_turn_minions
    from .location_board import board_location_plays
    from .rush_board import hand_rush_minions
    from .weapon_board import hand_weapons

    return (
        hand_board_spells(gs, player_id, available_mana)
        + hand_weapons(gs, player_id, available_mana)
        + hand_battlecry_minions(gs, player_id, available_mana)
        + hand_rush_minions(gs, player_id, available_mana)
        + hand_combo_minions(gs, player_id, available_mana)
        + hand_damaged_spellpower_minions(gs, player_id, available_mana)
        + hand_end_turn_minions(gs, player_id, available_mana)
        + board_location_plays(gs, player_id, available_mana)
    )


# 注册全部 P0 战吼
from . import battlecry_p0  # noqa: E402, F401
