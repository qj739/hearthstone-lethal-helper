# arcane_flow.py — 奥术涌流（CATA_489）裂变 / 碎裂形态

from __future__ import annotations

from typing import List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import Entity, GameState
    from .spell_board import BoardSpellDef, SpellPlayStep

EULOGIZER_COMBINE_IDS = frozenset({"TTN_457"})

# 合体（完整裂变）形态
ARCANE_FLOW_COMBINED = "CATA_489"
# 碎裂后：单点 4 伤 / 全体敌人 2 伤
ARCANE_FLOW_SHATTERED_SINGLE = "CATA_489t"
ARCANE_FLOW_SHATTERED_AOE = "CATA_489t2"

ARCANE_FLOW_ALL_IDS = frozenset({
    ARCANE_FLOW_COMBINED,
    ARCANE_FLOW_SHATTERED_SINGLE,
    ARCANE_FLOW_SHATTERED_AOE,
})

# 打出时触发「其他裂变牌碎裂」的法术（Cata 扩展包 Shatter 关键字）
SHATTER_SPELL_IDS = frozenset({
    "CATA_134",
    "CATA_202",
    "CATA_306",
    "CATA_479",
    ARCANE_FLOW_COMBINED,
    "CATA_820",
})


def is_arcane_flow_combined(card_id: str) -> bool:
    return card_id == ARCANE_FLOW_COMBINED


def is_arcane_flow_shattered_form(card_id: str) -> bool:
    return card_id in (ARCANE_FLOW_SHATTERED_SINGLE, ARCANE_FLOW_SHATTERED_AOE)


def is_shatter_spell_card(card: Optional["Entity"]) -> bool:
    """是否为带 Shatter 的法术（打出后令手牌中其他奥术涌流碎裂）。"""
    if card is None:
        return False
    cid = card.card_id or ""
    if cid in SHATTER_SPELL_IDS:
        return True
    return card.tags.get("SHATTER") == 1


class ArcaneFlowVirtualCombined:
    """手牌碎裂 t+t2 合体虚拟牌（4 费，打出后消耗两张碎裂实体）。"""

    def __init__(self, single_card: "Entity", aoe_card: "Entity"):
        self.card_id = ARCANE_FLOW_COMBINED
        self.cost = 4
        self.tags: dict = {}
        self.single_entity_id = single_card.entity_id
        self.aoe_entity_id = aoe_card.entity_id
        self.entity_id = -(self.single_entity_id * 100000 + self.aoe_entity_id)
        self.arcane_flow_consumed_entity_ids = (
            self.single_entity_id,
            self.aoe_entity_id,
        )


def find_shattered_arcane_flow_pair(
    gs: Optional["GameState"],
    player_id: Optional[int],
) -> Optional[Tuple["Entity", "Entity"]]:
    """手牌中同时存在已碎裂的 CATA_489t 与 CATA_489t2 时返回 (t, t2)。"""
    if gs is None or player_id is None:
        return None
    single: Optional["Entity"] = None
    aoe: Optional["Entity"] = None
    for card in gs.get_hand(player_id):
        cid = card.card_id or ""
        if card.tags.get("SHATTERED") != 1:
            continue
        if cid == ARCANE_FLOW_SHATTERED_SINGLE:
            single = card
        elif cid == ARCANE_FLOW_SHATTERED_AOE:
            aoe = card
    if single is not None and aoe is not None:
        return (single, aoe)
    return None


def arcane_flow_hand_playable(card: Optional["Entity"]) -> bool:
    """
    手牌是否可参与场攻/斩杀枚举。
    - 合体 CATA_489：始终可打
    - 碎裂形态 CATA_489t / t2：须 SHATTERED=1（日志 tag）
    """
    if card is None:
        return False
    cid = card.card_id or ""
    if cid == ARCANE_FLOW_COMBINED:
        return True
    if is_arcane_flow_shattered_form(cid):
        return card.tags.get("SHATTERED") == 1
    return True


def _append_shattered_arcane_flow_pair(pending: List["SpellPlayStep"]) -> None:
    from .spell_board import BoardSpellDef, _SyntheticSpellCard, get_board_spell_def

    for sid in (ARCANE_FLOW_SHATTERED_SINGLE, ARCANE_FLOW_SHATTERED_AOE):
        defn = get_board_spell_def(sid)
        if not defn:
            continue
        cost = defn.base_cost
        pending.append((
            defn,
            cost,
            _SyntheticSpellCard(sid, cost),
        ))


def trigger_arcane_flow_shatter_on_play(
    played_card: Optional["Entity"],
    gs: Optional["GameState"],
    player_id: Optional[int],
    pending: List["SpellPlayStep"],
    shattered_entities: Set[int],
) -> None:
    """
    打出 Shatter 法术后：手牌中其余未碎裂的合体奥术涌流变为 t + t2 并入 pending。
    """
    if not is_shatter_spell_card(played_card):
        return
    if gs is None or player_id is None:
        return
    played_eid = getattr(played_card, "entity_id", None)
    for card in gs.get_hand(player_id):
        eid = getattr(card, "entity_id", None)
        if eid is None or eid == played_eid:
            continue
        if eid in shattered_entities:
            continue
        cid = card.card_id or ""
        if not is_arcane_flow_combined(cid):
            continue
        if card.tags.get("SHATTERED") == 1:
            continue
        shattered_entities.add(eid)
        _append_shattered_arcane_flow_pair(pending)


def trigger_arcane_flow_recombine_on_play(
    played_card: Optional["Entity"],
    gs: Optional["GameState"],
    player_id: Optional[int],
    pending: List["SpellPlayStep"],
    shattered_entities: Set[int],
) -> None:
    """
    打出悼词宣诵者等牌时：手牌碎裂 t+t2 合体为 CATA_489 并入 pending。
    """
    if played_card is None or gs is None or player_id is None:
        return
    cid = played_card.card_id or ""
    if cid not in EULOGIZER_COMBINE_IDS:
        return
    pair = find_shattered_arcane_flow_pair(gs, player_id)
    if pair is None:
        return
    single, aoe = pair
    for card in (single, aoe):
        eid = getattr(card, "entity_id", None)
        if eid is not None:
            shattered_entities.add(eid)
    from .spell_board import get_board_spell_def, _SyntheticSpellCard

    defn = get_board_spell_def(ARCANE_FLOW_COMBINED)
    if not defn:
        return
    pending.append((
        defn,
        defn.base_cost,
        _SyntheticSpellCard(ARCANE_FLOW_COMBINED, defn.base_cost),
    ))
