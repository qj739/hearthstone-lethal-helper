# interleave_board.py — 攻击穿插注册表（战吼随从 + 法术）

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import Entity
    from .spell_board import BoardSpellDef


class InterleaveKind(str, Enum):
    """穿插模拟分支。"""

    FACELESS_RUSH = "faceless_rush"
    PRE_PLAY_AOE = "pre_play_aoe"
    SPELL_GENERIC = "spell_generic"


# --- 战吼随从 ---
FACELESS_CORRUPTOR_IDS: Set[str] = frozenset({"DRG_076"})
HOSTILE_INVADER_IDS: Set[str] = frozenset({"GDB_226"})
BUNKER_SERGEANT_IDS: Set[str] = frozenset({"AV_126"})
PRE_PLAY_ATTACK_INTERLEAVE_IDS: Set[str] = (
    HOSTILE_INVADER_IDS | BUNKER_SERGEANT_IDS
)
ATTACK_INTERLEAVE_BATTLECRY_IDS: Set[str] = (
    FACELESS_CORRUPTOR_IDS | PRE_PLAY_ATTACK_INTERLEAVE_IDS
)

# --- 法术（用户整理清单）---
ATTACK_INTERLEAVE_LOCATION_IDS: Set[str] = frozenset({
    "REV_290",       # 赎罪教堂 +2/+1（先攻再 buff 再攻）
    "CORE_REV_290",
})

ATTACK_INTERLEAVE_SPELL_IDS: Set[str] = frozenset({
    "WW_405",       # 迅疾连射
    "CFM_603",      # 疯狂药水
    "SW_040",       # 邪能弹幕
    "ICC_041",      # 亵渎
    "CATA_526",     # 布洛克斯加的奋战
    "SW_107",       # 火热促销
    "VAC_953",      # 浪潮涌起
    "CFM_662",      # 龙息药水
    "BT_117",       # 剑刃风暴
    "CATA_581",     # 屠灭
    "TTN_932",      # 混乱吞噬
    "DMF_117",      # 连环灾难
    "DMF_117t",
    "DMF_117t2",
    "REV_239",      # 窒息暗影
    "DREAM_02",     # 伊瑟拉苏醒
})

INTERLEAVE_SPELL_NAMES: Dict[str, str] = {
    "WW_405": "迅疾连射",
    "CFM_603": "疯狂药水",
    "SW_040": "邪能弹幕",
    "ICC_041": "亵渎",
    "CATA_526": "布洛克斯加的奋战",
    "SW_107": "火热促销",
    "VAC_953": "浪潮涌起",
    "CFM_662": "龙息药水",
    "BT_117": "剑刃风暴",
    "CATA_581": "屠灭",
    "TTN_932": "混乱吞噬",
    "DMF_117": "连环灾难",
    "DMF_117t": "连环灾难",
    "DMF_117t2": "连环灾难",
    "REV_239": "窒息暗影",
    "DREAM_02": "伊瑟拉苏醒",
}


def step_card_id(defn: "BoardSpellDef", card: Optional["Entity"]) -> str:
    if card and card.card_id:
        return card.card_id
    return defn.card_ids[0] if defn.card_ids else ""


def card_in_interleave_spell_set(card_id: str) -> bool:
    return card_id in ATTACK_INTERLEAVE_SPELL_IDS


def interleave_kind_for_card_id(card_id: str) -> Optional[InterleaveKind]:
    if card_id in FACELESS_CORRUPTOR_IDS:
        return InterleaveKind.FACELESS_RUSH
    if card_id in PRE_PLAY_ATTACK_INTERLEAVE_IDS:
        return InterleaveKind.PRE_PLAY_AOE
    if card_id in ATTACK_INTERLEAVE_SPELL_IDS:
        return InterleaveKind.SPELL_GENERIC
    return None


def sequence_is_faceless_only(sequence) -> bool:
    if len(sequence) != 1:
        return False
    defn, _, card = sequence[0]
    return step_card_id(defn, card) in FACELESS_CORRUPTOR_IDS


def sequence_needs_faceless_interleave(sequence) -> bool:
    return sequence_is_faceless_only(sequence)


def _sequence_card_ids(defn, card) -> Set[str]:
    ids = set(defn.card_ids or ())
    cid = step_card_id(defn, card)
    if cid:
        ids.add(cid)
    return ids


def sequence_has_interleave_spell(sequence) -> bool:
    for defn, _, card in sequence:
        if _sequence_card_ids(defn, card) & ATTACK_INTERLEAVE_SPELL_IDS:
            return True
    return False


def sequence_has_interleave_location(sequence) -> bool:
    for defn, _, card in sequence:
        if _sequence_card_ids(defn, card) & ATTACK_INTERLEAVE_LOCATION_IDS:
            return True
    return False


def sequence_has_pre_play_battlecry(sequence) -> bool:
    for defn, _, card in sequence:
        cid = step_card_id(defn, card)
        if cid in PRE_PLAY_ATTACK_INTERLEAVE_IDS:
            return True
    return False


def sequence_has_conflicting_battlecry(sequence) -> bool:
    """序列含非穿插战吼随从时，不走通用法术穿插。"""
    from .battlecry_board import get_battlecry_def

    for defn, _, card in sequence:
        cid = step_card_id(defn, card)
        if get_battlecry_def(cid) is None:
            continue
        base = cid[5:] if cid.startswith("CORE_") else cid
        if (
            cid in ATTACK_INTERLEAVE_BATTLECRY_IDS
            or base in ATTACK_INTERLEAVE_BATTLECRY_IDS
        ):
            continue
        return True
    return False


def sequence_needs_attack_interleave(sequence) -> bool:
    """
    启用 attack_interleaved：
    - 无面：仅单卡无面
    - 入侵者/碉堡：含该战吼且不含其他战吼（可含法术）
    - 穿插法术：含注册法术且不含冲突战吼
    """
    if not sequence:
        return False
    if sequence_is_faceless_only(sequence):
        return True
    from .battlecry_board import get_battlecry_def

    has_pre_play = False
    for defn, _, card in sequence:
        cid = step_card_id(defn, card)
        if cid in PRE_PLAY_ATTACK_INTERLEAVE_IDS:
            has_pre_play = True
        elif get_battlecry_def(cid) is not None:
            return False
    if has_pre_play:
        return True
    if sequence_has_interleave_location(sequence):
        return True
    if sequence_has_interleave_spell(sequence):
        if sequence_has_conflicting_battlecry(sequence):
            return False
        return True
    return False


def interleave_note_suffix(sequence, order: str) -> str:
    """overlay 备注后缀。"""
    if order == "faceless_interleaved":
        return " 无面穿插"
    if order != "attack_interleaved":
        return ""
    if sequence_is_faceless_only(sequence):
        return " 无面穿插"
    if sequence_has_interleave_location(sequence):
        return " 地标穿插"
    if sequence_has_interleave_spell(sequence) and not sequence_has_pre_play_battlecry(sequence):
        return " 法术穿插"
    return " 战吼穿插"
