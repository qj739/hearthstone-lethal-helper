# rush_combat.py — 突袭随从攻击阶段特效（攻击触发 / 顺劈 / 食人魔随机目标）

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

from .spell_board import _add_temp_hero_attack

if TYPE_CHECKING:
    from .lethal_checker import LethalChecker

# 场面随从 card_id → 攻击特效（打出时另由 rush_p0 写入 infused cleave 等）
BOARD_ATTACK_EFFECTS = {
    "CS3_020": {"mirrors_hero_attack": True},
    "SW_431": {"hero_atk_on_attack": 3},
    "CATA_469": {"mana_restore_on_attack": True},
    "DINO_401": {"splash_other_minions": True},
    "BT_487": {"attack_again_on_kill": True},
    "WW_418": {"ogre_misdirect": True},
    "JAM_004": {"cleave": True},
}


def stamp_fighter_attack_effects(fighter: dict, card_id: str = "", *, infused_cleave: bool = False) -> None:
    """为模拟攻击者写入 card_id 与攻击特效标记。"""
    cid = card_id or fighter.get("card_id") or ""
    fighter["card_id"] = cid
    effects = BOARD_ATTACK_EFFECTS.get(cid, {})
    if effects.get("mirrors_hero_attack"):
        fighter["mirrors_hero_attack"] = True
    if effects.get("hero_atk_on_attack"):
        fighter["hero_atk_on_attack"] = effects["hero_atk_on_attack"]
    if effects.get("splash_other_minions"):
        fighter["splash_other_minions"] = True
    if effects.get("attack_again_on_kill"):
        fighter["attack_again_on_kill"] = True
    if effects.get("ogre_misdirect"):
        fighter["ogre_misdirect"] = True
    if effects.get("cleave") or infused_cleave:
        fighter["cleave"] = True
    if effects.get("mana_restore_on_attack"):
        fighter["mana_restore_on_attack"] = True


def fighters_need_random_attacks(fighters: List[dict]) -> bool:
    return any(f.get("ogre_misdirect") for f in fighters if f.get("health", 0) > 0)


def sequence_has_ogre(sequence) -> bool:
    from .battlecry_board import _play_step_card_id
    from .rush_board import get_rush_def

    for defn, _, card in sequence or []:
        cid = _play_step_card_id(defn, card) if hasattr(defn, "card_ids") else ""
        if not cid and card:
            cid = card.card_id or ""
        if cid == "WW_418" or (get_rush_def(cid or "") and cid == "WW_418"):
            return True
        if card and (card.card_id or "") == "WW_418":
            return True
    return False


def _adjacent_living(enemy_board: List[dict], target: dict) -> List[dict]:
    if not enemy_board or not target:
        return []
    living = [e for e in enemy_board if e.get("health", 0) > 0]
    t_pos = target.get("zone_pos") or 0
    t_eid = target.get("entity_id")
    if t_pos:
        return [
            e for e in living
            if e.get("entity_id") != t_eid
            and abs(int(e.get("zone_pos") or 0) - int(t_pos)) == 1
        ]
    # 无站位时按列表相邻
    idx = next((i for i, e in enumerate(living) if e.get("entity_id") == t_eid), -1)
    if idx < 0:
        return []
    out: List[dict] = []
    if idx > 0:
        out.append(living[idx - 1])
    if idx + 1 < len(living):
        out.append(living[idx + 1])
    return out


def _apply_damage_to_unit(
    checker: "LethalChecker",
    fighter: dict,
    unit: dict,
    enemy_board: List[dict],
    fighters: List[dict],
) -> int:
    """对单个敌方单位造成伤害（复用单次攻击核心逻辑）。"""
    from .deathrattle import resolve_minion_death, remove_dead_taunts

    if unit.get("health", 0) <= 0:
        return 0
    heal = checker._apply_single_attack_core(fighter, unit)
    if checker._taunt_is_dead(unit):
        resolve_minion_death(unit, enemy_board, fighters)
        remove_dead_taunts(enemy_board)
    return heal


def after_minion_attack(
    checker: "LethalChecker",
    fighter: dict,
    target: dict,
    *,
    enemy_board: List[dict],
    fighters: List[dict],
    was_alive_before: bool,
) -> int:
    """随从攻击随从后的触发（顺劈 / 德拉克雷斯 / 暴怒式加攻 / 杀怪再攻）。"""
    from .deathrattle import on_minion_died, remove_dead_taunts

    extra_heal = 0
    atk = fighter.get("atk", 0)

    if fighter.get("hero_atk_on_attack"):
        _add_temp_hero_attack(fighters, int(fighter["hero_atk_on_attack"]))

    if fighter.get("cleave") and atk > 0:
        from .spell_board import _apply_damage

        for adj in _adjacent_living(enemy_board, target):
            extra_heal += _apply_damage(
                adj, atk, taunts=enemy_board, fighters=fighters,
            )
        from .deathrattle import remove_dead_taunts
        remove_dead_taunts(enemy_board)

    if fighter.get("splash_other_minions") and was_alive_before and atk > 0:
        from .deathrattle import resolve_minion_death, remove_dead_taunts

        t_eid = target.get("entity_id")
        for other in list(enemy_board):
            if other.get("entity_id") == t_eid or other.get("health", 0) <= 0:
                continue
            if other.get("kind") == "hero":
                continue
            other["health"] = other.get("health", 0) - atk
            if other.get("health", 0) <= 0:
                resolve_minion_death(other, enemy_board, fighters)
        remove_dead_taunts(enemy_board)

    if (
        fighter.get("attack_again_on_kill")
        and checker._taunt_is_dead(target)
        and was_alive_before
    ):
        fighter["attacks_left"] = fighter.get("attacks_left", 0) + 1

    return extra_heal


def hero_face_swings(fighters: List[dict]) -> int:
    """英雄本回合可打脸次数（武器挥击 + 技能/法术临时英雄攻）。"""
    swings = 0
    for f in fighters:
        if f.get("health", 0) <= 0 or f.get("attacks_left", 0) <= 0:
            continue
        if not f.get("can_face", True):
            continue
        if f.get("kind") == "weapon":
            swings += min(
                f["attacks_left"], f.get("durability", f.get("attacks_left", 0)),
            )
        elif f.get("kind") == "hero":
            swings += f["attacks_left"]
    return swings


def inquisitor_face_mirror_hits(fighters: List[dict], base_hits: List[int]) -> List[int]:
    """英雄/武器打脸时，审判官跟刀追加伤害（独立触发，不消耗 attacks_left，不受突袭禁脸限制）。"""
    hits = list(base_hits)
    mirrors = [
        f for f in fighters
        if f.get("mirrors_hero_attack") and f.get("health", 0) > 0
    ]
    if not mirrors:
        return hits

    for _ in range(hero_face_swings(fighters)):
        hits.append(mirrors[0].get("atk", 0))
    return hits


def inquisitor_mirror_face_damage(
    fighters: List[dict], defender_shield: bool = False,
) -> int:
    """审判官跟刀打脸分量（用于分项时并入随从，避免与技能/武器重复）。"""
    from .board_damage import apply_divine_shield_to_hits

    mirror_hits = inquisitor_face_mirror_hits(fighters, [])
    return apply_divine_shield_to_hits(mirror_hits, defender_shield)


def after_hero_attack(
    checker: "LethalChecker",
    target: dict,
    *,
    enemy_board: List[dict],
    fighters: List[dict],
    defender_shield: bool,
    target_is_face: bool = False,
) -> int:
    """英雄攻击后：伊利达雷审判官跟刀（与随从自身 attacks_left / 突袭禁脸无关）。"""
    extra_heal = 0
    for f in fighters:
        if not f.get("mirrors_hero_attack") or f.get("health", 0) <= 0:
            continue
        if target_is_face:
            continue
        if target.get("health", 0) <= 0:
            continue
        was_alive = target.get("health", 0) > 0
        extra_heal += checker._apply_mirror_attack_core(f, target)
        extra_heal += after_minion_attack(
            checker, f, target,
            enemy_board=enemy_board, fighters=fighters,
            was_alive_before=was_alive,
        )
        if checker._taunt_is_dead(target):
            from .deathrattle import resolve_minion_death, remove_dead_taunts
            resolve_minion_death(target, enemy_board, fighters)
            remove_dead_taunts(enemy_board)
    return extra_heal


def ogre_pick_target(
    intended: dict,
    valid_targets: List[dict],
    rng: Optional[random.Random],
) -> dict:
    """食人魔 50% 攻击错误目标。"""
    if not valid_targets:
        return intended
    roll = rng if rng is not None else random.Random(0)
    if roll.random() < 0.5:
        return intended
    others = [t for t in valid_targets if t is not intended]
    if not others:
        return intended
    return roll.choice(others)
