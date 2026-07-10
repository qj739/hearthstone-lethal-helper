# damaged_spell_power.py — 受伤时获得法术伤害（如 END_022 时光扭曲先知）

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

from .board_damage import hand_minion_attack, hand_minion_cost, hand_minion_health
from .spell_board import BoardSpellDef, SpellApplyResult, _summon_friendly_fighter

# card_id -> 受伤后法术伤害加成
DAMAGED_SPELL_POWER_BONUS: dict[str, int] = {
    "END_022": 2,
}

BOARD_DAMAGED_SPELL_POWER: Dict[str, BoardSpellDef] = {}

_FIREBLAST_COST = 2


def _base_card_id(card_id: str) -> str:
    if not card_id:
        return ""
    return card_id[5:] if card_id.startswith("CORE_") else card_id


def _register_damaged_spell_power(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_DAMAGED_SPELL_POWER[cid] = defn


def get_damaged_spell_power_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_DAMAGED_SPELL_POWER:
        return BOARD_DAMAGED_SPELL_POWER[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_DAMAGED_SPELL_POWER.get(card_id[5:])
    return BOARD_DAMAGED_SPELL_POWER.get("CORE_" + card_id)


def is_damaged_spellpower_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    from .spell_board import _step_card_id

    return _step_card_id(defn, card) in BOARD_DAMAGED_SPELL_POWER


def _apply_play_damaged_spellpower_minion(
    _t,
    fighters: List[dict],
    *,
    mult: int = 1,
    card: Optional["Entity"] = None,
    **_kw,
) -> SpellApplyResult:
    """打出受伤法强随从：当回合召唤（失调），供序列内火焰冲击点伤激活法强。"""
    if card is None:
        return SpellApplyResult()
    cid = card.card_id or ""
    atk = hand_minion_attack(card) * mult
    hp = hand_minion_health(card) * mult
    _summon_friendly_fighter(fighters, atk, hp, card_id=cid)
    if fighters:
        unit = fighters[-1]
        unit["sim_summon"] = True
        unit["damage"] = 0
        unit["spellpower"] = 0
        unit["max_health"] = int(unit.get("health", 0) or 0)
    return SpellApplyResult()


def hand_damaged_spellpower_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    """可打出的手牌受伤法强随从（非战吼/突袭，专用于组合技枚举）。"""
    from .battlecry_board import get_battlecry_def
    from .rush_board import get_rush_def

    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_minion:
            continue
        cid = card.card_id or ""
        if not is_damaged_spell_power_card(cid):
            continue
        if get_battlecry_def(cid) or get_rush_def(cid):
            continue
        defn = get_damaged_spell_power_def(cid)
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


def damaged_spell_power_bonus(card_id: str) -> int:
    cid = card_id or ""
    if cid in DAMAGED_SPELL_POWER_BONUS:
        return DAMAGED_SPELL_POWER_BONUS[cid]
    base = _base_card_id(cid)
    return DAMAGED_SPELL_POWER_BONUS.get(base, DAMAGED_SPELL_POWER_BONUS.get(f"CORE_{base}", 0))


def is_damaged_spell_power_card(card_id: str) -> bool:
    return damaged_spell_power_bonus(card_id) > 0


def fighter_spell_power_from_entity(entity: "Entity") -> int:
    sp = int(entity.tags.get("SPELLPOWER", 0) or 0)
    if sp > 0:
        return sp
    if int(entity.damage or 0) > 0:
        return damaged_spell_power_bonus(entity.card_id or "")
    return 0


def fighter_spell_power(unit: dict) -> int:
    if unit.get("kind") != "minion" or int(unit.get("health", 0) or 0) <= 0:
        return 0
    sp = int(unit.get("spellpower", 0) or 0)
    if sp > 0:
        return sp
    dmg = int(unit.get("damage", 0) or 0)
    if dmg <= 0 and int(unit.get("health", 0) or 0) < int(unit.get("max_health", 0) or 0):
        dmg = max(0, int(unit.get("max_health", 0) or 0) - int(unit.get("health", 0) or 0))
    if dmg > 0:
        return damaged_spell_power_bonus(unit.get("card_id", "") or "")
    return 0


def fighters_spell_power(fighters: List[dict]) -> int:
    return sum(fighter_spell_power(f) for f in fighters)


def sim_spell_power(
    gs: Optional["GameState"],
    player_id: Optional[int],
    fighters: Optional[List[dict]] = None,
) -> int:
    """场面实体法强 + 模拟 fighters 上受伤法强随从。"""
    from .spell_board import total_spell_power

    base = total_spell_power(gs, player_id)
    if not fighters:
        return base
    # gs 已含场面随从法强；fighters 里仅计 sim_summon / 当回合新增且不在 gs 的
    extra = 0
    board_eids: set = set()
    if gs is not None and player_id is not None:
        for ent in gs.get_board(player_id):
            if ent.current_health > 0:
                board_eids.add(ent.entity_id)
    for f in fighters:
        if f.get("kind") != "minion" or int(f.get("health", 0) or 0) <= 0:
            continue
        eid = f.get("entity_id")
        if eid is not None and eid in board_eids:
            continue
        extra += fighter_spell_power(f)
    return base + extra


def damage_friendly_fighter(fighter: dict, amount: int) -> int:
    """对己方模拟随从造成伤害并激活受伤法强。返回实际伤害量。"""
    if amount <= 0 or fighter.get("kind") != "minion":
        return 0
    hp = int(fighter.get("health", 0) or 0)
    if hp <= 0:
        return 0
    if fighter.get("max_health") is None:
        fighter["max_health"] = hp
    if fighter.get("shield"):
        fighter["shield"] = False
        amount -= 1
        if amount <= 0:
            return 0
    dealt = min(amount, hp)
    fighter["health"] = hp - dealt
    fighter["damage"] = int(fighter.get("damage", 0) or 0) + dealt
    bonus = damaged_spell_power_bonus(fighter.get("card_id", "") or "")
    if bonus and fighter["damage"] > 0 and fighter["health"] > 0:
        fighter["spellpower"] = bonus
    return dealt


def find_undamaged_spellpower_setup_target(fighters: List[dict]) -> Optional[dict]:
    """找可点伤以激活法强的己方随从（未受伤、仍存活）。"""
    best: Optional[dict] = None
    for f in fighters:
        if f.get("kind") != "minion":
            continue
        if int(f.get("health", 0) or 0) <= 0:
            continue
        cid = f.get("card_id", "") or ""
        if not is_damaged_spell_power_card(cid):
            continue
        if int(f.get("damage", 0) or 0) > 0:
            continue
        if fighter_spell_power(f) > 0:
            continue
        if best is None:
            best = f
    return best


def has_undamaged_spellpower_on_fighters(fighters: List[dict]) -> bool:
    return find_undamaged_spellpower_setup_target(fighters) is not None


def hand_has_damaged_spellpower_card(gs: Optional["GameState"], player_id: Optional[int]) -> bool:
    if gs is None or player_id is None:
        return False
    for card in gs.get_hand(player_id):
        if card.is_minion and is_damaged_spell_power_card(card.card_id or ""):
            return True
    return False


def _mage_fireblast_available(gs: Optional["GameState"], player_id: Optional[int]) -> bool:
    if gs is None or player_id is None:
        return False
    from .hero_power_board import usable_hero_power

    return usable_hero_power(gs, player_id, _FIREBLAST_COST) is not None


def apply_mage_fireblast_setup(
    fighters: List[dict],
    *,
    amount: int = 1,
) -> bool:
    """火焰冲击点己方受伤法强随从以激活法强。成功返回 True。"""
    target = find_undamaged_spellpower_setup_target(fighters)
    if target is None:
        return False
    damage_friendly_fighter(target, amount)
    return True


def try_inline_mage_fireblast_setup(
    fighters: List[dict],
    gs: Optional["GameState"],
    player_id: Optional[int],
    mana_left: Optional[int],
    *,
    already_used: bool = False,
) -> Optional[int]:
    """
    法术序列中：打出受伤法强随从后，用剩余法力点技能激活。
    返回更新后的剩余法力；无法激活时返回原值。
    """
    if already_used or mana_left is None or mana_left < _FIREBLAST_COST:
        return mana_left
    if not _mage_fireblast_available(gs, player_id):
        return mana_left
    if find_undamaged_spellpower_setup_target(fighters) is None:
        return mana_left
    if not apply_mage_fireblast_setup(fighters):
        return mana_left
    return mana_left - _FIREBLAST_COST


_register_damaged_spell_power(BoardSpellDef(
    ("END_022",),
    1,
    "时光扭曲先知",
    _apply_play_damaged_spellpower_minion,
))
