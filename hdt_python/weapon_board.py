# weapon_board.py — 手牌武器接入场攻/斩杀模拟

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_cost
from .spell_board import BoardSpellDef, SpellApplyResult

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


def _default_weapon_apply(cid: str, default_atk: int = 1, default_dur: int = 1):
    """未单独实现的武器：按手牌当前攻/耐久装备并计入挥击。"""

    def _apply(t, f, *, mult=1, card=None, **_kw):
        from .weapon_p0 import _card_has_windfury, _equip, _weapon_stats_from_card

        wa, wd = _weapon_stats_from_card(card, default_atk, default_dur)
        _equip(
            f, wa, wd, cid, mult=mult,
            windfury=_card_has_windfury(card), **_kw,
        )
        return SpellApplyResult()

    return _apply


def ensure_weapon_def(card: "Entity") -> Optional[BoardSpellDef]:
    """已注册则复用；否则按实体攻/耐久合成默认装备定义（经典/生成武器）。"""
    cid = card.card_id or ""
    if not cid:
        return None
    existing = get_weapon_def(cid)
    if existing is not None:
        return existing
    atk = max(1, int(card.atk or card.tags.get("ATK", 0) or card.tags.get("479", 0) or 1))
    dur = int(getattr(card, "current_durability", 0) or 0)
    if dur <= 0:
        dur = max(1, int(card.health or card.tags.get("HEALTH", 0) or 1))
    cost = hand_minion_cost(card)
    name = cid
    defn = BoardSpellDef((cid,), cost, name, _default_weapon_apply(cid, atk, dur))
    _register_weapon(defn)
    return defn


def hand_weapons(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    for card in gs.get_hand(player_id):
        if not card.is_weapon:
            continue
        defn = ensure_weapon_def(card)
        if not defn:
            continue
        cost = hand_minion_cost(card)
        if cost <= available_mana:
            result.append((card, defn, cost))
    return result


from . import weapon_p0  # noqa: E402, F401
