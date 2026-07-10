# location_p0.py — P0 地标效果

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from .board_damage import (
    attacks_per_turn,
    build_board_card,
    effective_attack_from_tags,
    is_silenced,
)
from .location_board import _register_location
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_random_split_damage,
    hand_effect_active,
)

if TYPE_CHECKING:
    from .power_parser import Entity, GameState


def _entity_windfury(entity: "Entity") -> bool:
    if is_silenced(entity):
        return False
    return attacks_per_turn(entity) > 1


def _entity_can_attack_this_turn(entity: "Entity", *, active_turn: bool = True) -> bool:
    view = build_board_card(entity, active_turn)
    return view.can_attack_minion or view.can_attack_hero


def pick_cathedral_buff_target(
    gs: "GameState",
    player_id: int,
    *,
    active_turn: bool = True,
) -> Optional["Entity"]:
    """
    赎罪教堂 +2/+1 目标：
    1. 本回合可攻击随从中，优先风怒，同档取攻击最低
    2. 无风怒则取可攻击中攻击最低
    """
    candidates: List[tuple] = []
    for m in gs.get_board(player_id):
        if not _entity_can_attack_this_turn(m, active_turn=active_turn):
            continue
        atk = effective_attack_from_tags(m.tags)
        if atk <= 0 and m.atk > 0:
            atk = m.atk
        wf = _entity_windfury(m)
        candidates.append((0 if wf else 1, atk, m.entity_id, m))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1], x[2]))
    return candidates[0][3]


def _buff_friendly_minion(
    fighters: List[dict],
    entity_id: int,
    *,
    bonus_atk: int,
    bonus_health: int,
) -> bool:
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        if f.get("entity_id") != entity_id:
            continue
        fighters[i] = dict(f)
        fighters[i]["atk"] = fighters[i].get("atk", 0) + bonus_atk
        fighters[i]["health"] = fighters[i].get("health", 0) + bonus_health
        return True
    return False


def _apply_cathedral_of_atonement(
    taunts,
    fighters,
    *,
    mult: int,
    enemy_shield,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    **_kw,
) -> SpellApplyResult:
    """赎罪教堂：+2/+1，优先风怒可攻随从，否则攻击最低的可攻随从。"""
    if gs is None or player_id is None:
        return SpellApplyResult()
    target = pick_cathedral_buff_target(gs, player_id)
    if target is None:
        return SpellApplyResult()
    bonus_atk = 2 * mult
    bonus_hp = 1 * mult
    eid = target.entity_id
    if not _buff_friendly_minion(
        fighters, eid, bonus_atk=bonus_atk, bonus_health=bonus_hp,
    ):
        atk = effective_attack_from_tags(target.tags)
        if atk <= 0 and target.atk > 0:
            atk = target.atk
        attacks = 0
        view = build_board_card(target, True)
        if view.can_attack_minion or view.can_attack_hero:
            used = int(target.tags.get("NUM_ATTACKS_THIS_TURN", 0) or 0)
            attacks = max(attacks_per_turn(target) - used, 0)
        fighters.append({
            "kind": "minion",
            "entity_id": eid,
            "card_id": target.card_id or "",
            "atk": atk + bonus_atk,
            "health": target.current_health + bonus_hp,
            "attacks_left": attacks,
            "can_face": view.can_attack_hero,
        })
    return SpellApplyResult()


def erupting_volcano_total_damage(
    *,
    card: Optional["Entity"] = None,
    fire_spell_played_this_turn: bool = False,
    mult: int = 1,
) -> int:
    """喷发火山：本回合已打火系法术 6 伤，否则 3 伤（随机 split 敌人）。"""
    powered = fire_spell_played_this_turn or hand_effect_active(card)
    return (6 if powered else 3) * mult


def _apply_erupting_volcano(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    rng=None,
    card=None,
    fire_spell_played_this_turn=False,
    **_kw,
) -> SpellApplyResult:
    total = erupting_volcano_total_damage(
        card=card,
        fire_spell_played_this_turn=fire_spell_played_this_turn,
        mult=mult,
    )
    roll = rng if rng is not None else __import__("random").Random(0)
    return _apply_random_split_damage(
        taunts, fighters, total, enemy_shield=enemy_shield,
        rng=roll, include_enemy_hero=True,
    )


def location_has_valid_target(
    defn: BoardSpellDef,
    gs: "GameState",
    player_id: int,
) -> bool:
    if "REV_290" in defn.card_ids or "CORE_REV_290" in defn.card_ids:
        return pick_cathedral_buff_target(gs, player_id) is not None
    return True


def _register_p0_locations() -> None:
    _register_location(BoardSpellDef(
        card_ids=("REV_290", "CORE_REV_290"),
        base_cost=0,
        name="赎罪教堂",
        apply=_apply_cathedral_of_atonement,
        uses_random=False,
    ))
    _register_location(BoardSpellDef(
        card_ids=("CATA_584",),
        base_cost=0,
        name="喷发火山",
        apply=_apply_erupting_volcano,
        uses_random=True,
    ))


_register_p0_locations()
