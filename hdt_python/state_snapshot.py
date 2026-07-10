# state_snapshot.py - 将 Power.log 解析结果导出为可与 HDT 对比的快照

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .board_damage import board_active_turn_for_display, entity_has_taunt

if TYPE_CHECKING:
    from .lethal_checker import LethalChecker
    from .power_parser import GameState, Entity


def _hero_snapshot(hero: Optional["Entity"]) -> Dict[str, Any]:
    if not hero:
        return {"health": 30, "armor": 0, "total": 30}
    health = hero.current_health
    if health == 0 and hero.health == 0:
        health = 30
    armor = hero.tags.get("ARMOR", 0)
    return {"health": health, "armor": armor, "total": health + armor}


def _weapon_snapshot(weapon: Optional["Entity"]) -> Optional[Dict[str, Any]]:
    if not weapon:
        return None
    return {
        "cardId": weapon.card_id or "",
        "attack": weapon.atk,
        "durability": weapon.current_durability,
    }


def _minion_snapshot(entity: "Entity", *, active_turn: bool) -> Dict[str, Any]:
    view = entity.board_card_view(active_turn)
    return {
        "entityId": entity.entity_id,
        "cardId": entity.card_id or "",
        "attack": entity.atk,
        "health": entity.current_health,
        "zonePos": entity.tags.get("ZONE_POSITION", 0),
        "canAttack": view.can_attack_minion,
        "canAttackHero": view.can_attack_hero,
        "taunt": entity_has_taunt(entity),
        "exhausted": entity.tags.get("EXHAUSTED", 0) == 1,
    }


def _board_list(board: List["Entity"], *, active_turn: bool) -> List[Dict[str, Any]]:
    return [_minion_snapshot(m, active_turn=active_turn) for m in board]


def export_game_state(gs: "GameState", lethal_checker: Optional["LethalChecker"] = None) -> Dict[str, Any]:
    """导出当前解析状态（结构与 HDT 插件 JSON 对齐）。"""
    local = gs.local_player_id
    opp = gs.opponent_player_id
    in_game = gs.in_game and local is not None and opp is not None

    player_board: List[Dict[str, Any]] = []
    opponent_board: List[Dict[str, Any]] = []
    player_hero = _hero_snapshot(None)
    opponent_hero = _hero_snapshot(None)
    player_weapon = None
    mana = 0
    mana_used = 0
    hand_count = 0
    opp_hand_count = 0
    board_face = 0
    board_minion_atk = 0
    board_weapon_atk = 0
    is_my_turn = gs.is_local_turn() if local else False

    if local is not None:
        active = gs.is_local_turn()
        overlay_active = board_active_turn_for_display(gs, local)
        my_board = gs.get_board(local)
        my_hero = gs.get_hero(local)
        player_hero = _hero_snapshot(my_hero)
        player_weapon = _weapon_snapshot(gs.get_weapon(local))
        player_board = _board_list(my_board, active_turn=active)
        hand_count = len(gs.get_hand(local))
        if my_hero:
            mana = my_hero.tags.get("RESOURCES", 0)
            mana_used = my_hero.tags.get("RESOURCES_USED", 0)
        board_view = gs.get_player_board(local, active_turn=active)
        board_minion_atk = board_view.minion_damage
        board_weapon_atk = board_view.hero_damage
        board_face = board_minion_atk + board_weapon_atk
        overlay_face = board_face
        if lethal_checker:
            overlay_face = lethal_checker.overlay_board_face_damage()

    if opp is not None:
        opponent_board = _board_list(gs.get_board(opp), active_turn=False)
        opponent_hero = _hero_snapshot(gs.get_hero(opp))
        opp_hand_count = sum(
            1 for e in list(gs.entities.values())
            if gs.is_entity_controlled_by(e, opp) and (e.zone == "HAND" or e.tags.get("ZONE") == 2)
        )

    turn = None
    if gs.game_entity_id and gs.game_entity_id in gs.entities:
        turn = gs.entities[gs.game_entity_id].tags.get("TURN")

    return {
        "source": "power_log",
        "inGame": in_game,
        "isMyTurn": is_my_turn,
        "turn": turn,
        "player": {
            "playerId": local,
            "hero": player_hero,
            "mana": mana,
            "manaUsed": mana_used,
            "handCount": hand_count,
            "weapon": player_weapon,
            "board": player_board,
            "boardMinionAttack": board_minion_atk,
            "boardWeaponAttack": board_weapon_atk,
            "boardFaceDamage": board_face,
            "overlayFaceDamage": overlay_face,
        },
        "opponent": {
            "playerId": opp,
            "hero": opponent_hero,
            "handCount": opp_hand_count,
            "board": opponent_board,
        },
    }
