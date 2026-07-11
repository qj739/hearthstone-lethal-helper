# combat_sim.py - 场面交换 / 清嘲模拟（供 spell_board 与 lethal_checker 共用）

from __future__ import annotations

import copy
from typing import Callable, List, Optional, Tuple

from .board_damage import apply_divine_shield_to_hits
from .deathrattle import on_minion_died, remove_dead_taunts, resolve_minion_death


def _normalize_fighter(f: dict) -> dict:
    """补全 combat_sim 所需字段（兼容缺少 attacks_left 的简化 dict / 测试脚本）。"""
    if "attacks_left" in f and "can_face" in f:
        return f
    out = dict(f)
    out.setdefault("attacks_left", 1)
    out.setdefault("can_face", True)
    out.setdefault("health", 0)
    out.setdefault("kind", "minion")
    return out


def _normalize_fighters(fighters: List[dict]) -> List[dict]:
    return [_normalize_fighter(f) for f in fighters]


def unit_is_dormant(unit: dict) -> bool:
    """休眠随从本回合不参与嘲讽阻挡与交换。"""
    return bool(unit.get("dormant"))


def unit_is_active_minion(unit: dict) -> bool:
    """场上仍参与交互的随从（休眠忽视）。"""
    return (
        unit.get("health", 0) > 0
        and unit.get("kind") != "hero"
        and not unit_is_dormant(unit)
    )


def _friendly_taunt_blocks_face(fighters: List[dict]) -> bool:
    """疯狂药水等当回合偷来的嘲讽不阻挡己方其余随从打脸。

    己方召唤的嘲讽（当回合不能攻击）也不应阻挡其余随从打脸（如光速抢购 token）。
    """
    return any(
        f.get("kind") == "minion"
        and f.get("health", 0) > 0
        and f.get("taunt")
        and not f.get("stolen_turn")
        and f.get("attacks_left", 0) > 0
        for f in fighters
    )


def fighters_face_hits(fighters: List[dict]) -> List[int]:
    if _friendly_taunt_blocks_face(fighters):
        return []
    hits: List[int] = []
    for f in fighters:
        if not f.get("can_face", True):
            continue
        if f["health"] <= 0 or f["attacks_left"] <= 0:
            continue
        if f["kind"] == "weapon":
            n = min(f["attacks_left"], f.get("durability", 0))
        else:
            n = f["attacks_left"]
        for _ in range(n):
            hits.append(f["atk"])
    return hits


def fighters_face_damage(fighters: List[dict], defender_shield: bool = False) -> int:
    hits = list(fighters_face_hits(fighters))
    for f in fighters:
        if f.get("kind") != "weapon" or f.get("health", 0) <= 0:
            continue
        if not f.get("can_face", True):
            continue
        aoe = int(f.get("hero_aoe_on_attack", 0) or 0)
        if aoe <= 0:
            continue
        n = min(f.get("attacks_left", 0), f.get("durability", 0))
        hits.extend([aoe] * n)
    return apply_divine_shield_to_hits(hits, defender_shield)


def taunt_is_dead(taunt: dict) -> bool:
    return taunt["health"] <= 0


def apply_single_attack(fighter: dict, taunt: dict) -> int:
    if fighter["attacks_left"] <= 0 or fighter["health"] <= 0:
        return 0

    if taunt["shield"]:
        taunt["shield"] = False
        damage_dealt = 0
    else:
        damage_dealt = min(fighter["atk"], max(taunt["health"], 0))
        taunt["health"] -= fighter["atk"]
        if damage_dealt > 0 and fighter.get("poisonous"):
            taunt["health"] = 0

    if damage_dealt > 0 and taunt.get("poisonous"):
        fighter["health"] = 0
    elif taunt.get("atk", 0) > 0 and damage_dealt > 0:
        if fighter.get("shield"):
            fighter["shield"] = False
        elif not fighter.get("hero_immune_on_attack"):
            fighter["health"] -= taunt["atk"]

    fighter["attacks_left"] -= 1
    if fighter["kind"] == "weapon":
        fighter["durability"] = max(0, fighter.get("durability", 0) - 1)

    return damage_dealt if taunt.get("lifesteal") else 0


def kill_taunt_outcomes(
    fighters: List[dict],
    taunt: dict,
    other_taunts: List[dict],
) -> List[Tuple[List[dict], int]]:
    outcomes: List[Tuple[List[dict], int]] = []

    def dfs(fs: List[dict], t: dict, heal: int) -> None:
        if taunt_is_dead(t):
            outcomes.append((fs, heal))
            return
        if not any(f["attacks_left"] > 0 and f["health"] > 0 for f in fs):
            return
        for i in range(len(fs)):
            if fs[i]["attacks_left"] <= 0 or fs[i]["health"] <= 0:
                continue
            fs2 = copy.deepcopy(fs)
            t2 = copy.deepcopy(t)
            other2 = copy.deepcopy(other_taunts)
            h = apply_single_attack(fs2[i], t2)
            if taunt_is_dead(t2):
                board2 = other2 + [t2]
                resolve_minion_death(t2, board2, fs2)
                remove_dead_taunts(board2)
                other2[:] = [m for m in board2 if m is not t2 and m.get("health", 0) > 0]
            dfs(fs2, t2, heal + h)

    dfs(copy.deepcopy(fighters), copy.deepcopy(taunt), 0)
    return outcomes


def find_best_taunt_clear_face(
    fighters: List[dict],
    taunts: List[dict],
    defender_shield: bool = False,
) -> Optional[int]:
    face, _, _, _ = find_best_taunt_clear_state(fighters, taunts, defender_shield)
    return face


def find_best_taunt_clear_state(
    fighters: List[dict],
    taunts: List[dict],
    defender_shield: bool = False,
) -> Tuple[Optional[int], int, Optional[List[dict]], List[dict]]:
    fighters = _normalize_fighters(fighters)
    if not taunts:
        fs = copy.deepcopy(fighters)
        return fighters_face_damage(fs, defender_shield), 0, fs, []

    if not any(f["attacks_left"] > 0 and f["health"] > 0 for f in fighters):
        return None, 0, None, taunts

    best_face: Optional[int] = None
    best_heal = 0
    best_fighters: Optional[List[dict]] = None

    for fs_after, heal_here in kill_taunt_outcomes(fighters, taunts[0], taunts[1:]):
        sub_face, sub_heal, sub_fighters, _sub_taunts = find_best_taunt_clear_state(
            fs_after, taunts[1:], defender_shield,
        )
        if sub_face is None:
            continue
        total_heal = heal_here + sub_heal
        if best_face is None or sub_face > best_face or (
            sub_face == best_face and total_heal < best_heal
        ):
            best_face = sub_face
            best_heal = total_heal
            best_fighters = sub_fighters

    if best_face is None:
        return None, 0, None, taunts
    return best_face, best_heal, best_fighters, []


def living_taunt_units(units: List[dict]) -> List[dict]:
    """存活且带嘲讽的敌方随从（休眠随从本回合忽视）。"""
    return [
        t for t in units
        if t.get("health", 0) > 0 and t.get("taunt") and not unit_is_dormant(t)
    ]


def rush_enable_face_if_no_enemy_minions(
    fighters: List[dict], enemy_board: List[dict],
) -> None:
    """对手场上无随从时，当回合突袭可打脸（亡者大军等）。"""
    has_enemy_minion = any(
        unit_is_active_minion(m) and m.get("kind") != "hero"
        for m in enemy_board
    )
    if has_enemy_minion:
        return
    for f in _normalize_fighters(fighters):
        if (
            f.get("rush")
            and f.get("attacks_left", 0) > 0
            and f.get("health", 0) > 0
            and f.get("kind") == "minion"
        ):
            f["can_face"] = True


def project_board_face_after_spell(
    taunts: List[dict],
    fighters: List[dict],
    defender_shield: bool,
) -> int:
    """法术已结算后的场面：清嘲则取最优剩余打脸，否则 0。"""
    fighters = _normalize_fighters(fighters)
    alive_taunts = living_taunt_units(taunts)
    if not alive_taunts:
        fs, board = exhaust_rush_on_enemy_minions(
            fighters, taunts, defender_shield,
        )
        rush_enable_face_if_no_enemy_minions(fs, board)
        return fighters_face_damage(fs, defender_shield)
    face = find_best_taunt_clear_face(fighters, alive_taunts, defender_shield)
    return face if face is not None else 0


def _rush_fighters(fighters: List[dict]) -> List[dict]:
    """仅本回合不能打脸的突袭（can_face=False）；上场已满一回合的突袭可直攻。"""
    return [
        f for f in _normalize_fighters(fighters)
        if f.get("rush")
        and not f.get("can_face", True)
        and f.get("attacks_left", 0) > 0
        and f.get("health", 0) > 0
        and f.get("kind") == "minion"
    ]


def rush_attack_targets(enemy_board: List[dict]) -> List[dict]:
    """突袭合法目标：有嘲讽必须先打嘲讽，否则任意存活敌方随从。"""
    taunts = living_taunt_units(enemy_board)
    if taunts:
        return taunts
    return [
        m for m in enemy_board
        if unit_is_active_minion(m) and m.get("kind") != "hero"
    ]


def _sync_minion_death_on_boards(
    fighter: dict,
    target: dict,
    fighters: List[dict],
    enemy_board: List[dict],
) -> None:
    if target.get("health", 0) <= 0:
        resolve_minion_death(target, enemy_board, fighters)
        remove_dead_taunts(enemy_board)
    if fighter.get("health", 0) <= 0:
        resolve_minion_death(fighter, enemy_board, fighters)
        remove_dead_taunts(enemy_board)


def exhaust_rush_on_enemy_minions(
    fighters: List[dict],
    enemy_board: List[dict],
    defender_shield: bool = False,
    *,
    score_after: Optional[Callable[[List[dict], List[dict]], int]] = None,
) -> Tuple[List[dict], List[dict]]:
    """
    让当回合突袭随从攻击敌方随从（不能打脸）。
    有 score_after 时贪心选得分最高的单次攻击；否则优先打剩余血量最高的随从。
    """
    fs = copy.deepcopy(_normalize_fighters(fighters))
    board = copy.deepcopy(enemy_board)

    while True:
        rushes = _rush_fighters(fs)
        targets = rush_attack_targets(board)
        if not rushes or not targets:
            break

        best_score = -1
        best_pair: Optional[Tuple[List[dict], List[dict]]] = None

        for rush in rushes:
            rid = rush.get("entity_id")
            for target in targets:
                fs2 = copy.deepcopy(fs)
                board2 = copy.deepcopy(board)
                r2 = next(
                    (f for f in fs2 if f.get("entity_id") == rid),
                    None,
                )
                tid = target.get("entity_id")
                t2 = next(
                    (m for m in board2 if m.get("entity_id") == tid),
                    None,
                )
                if r2 is None or t2 is None or t2.get("health", 0) <= 0:
                    continue
                apply_single_attack(r2, t2)
                _sync_minion_death_on_boards(r2, t2, fs2, board2)
                if score_after is not None:
                    score = score_after(fs2, board2)
                else:
                    score = fighters_face_damage(fs2, defender_shield)
                if score > best_score:
                    best_score = score
                    best_pair = (fs2, board2)

        if best_pair is None:
            break
        fs, board = best_pair
        if not _rush_fighters(fs):
            break

    return fs, board
