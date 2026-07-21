# deathrattle.py - 随从死亡时亡语（用于交换/法术解场模拟）

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DrKind(str, Enum):
    """亡语效果类型（从防守方随从视角描述，模拟时映射到 attackers/fighters）。"""
    AOE_ALL_MINIONS = "aoe_all_minions"
    AOE_OTHER_MINIONS = "aoe_other_minions"
    AOE_ATTACKER_MINIONS = "aoe_attacker_minions"
    AOE_ATTACKER_MINIONS_ATK = "aoe_attacker_minions_atk"
    LOWEST_ATTACKER = "lowest_attacker"
    RANDOM_SPLIT_ATTACKERS = "random_split_attackers"
    ALL_ATTACKERS = "all_attackers"
    RANDOM_ATTACKER = "random_attacker"
    RANDOM_ATTACKER_SCRIPT = "random_attacker_script"
    SUMMON_ENEMY = "summon_enemy"
    SUMMON_ATTACK_ATTACKERS = "summon_attack_attackers"
    ENEMY_ARMOR = "enemy_armor"


@dataclass(frozen=True)
class DeathrattleDef:
    kind: DrKind
    amount: int = 0
    default_script: int = 0
    summon_atk: int = 0
    summon_health: int = 0
    summon_taunt: bool = False
    summon_charge: bool = False
    summon_card_id: str = ""
    summon_count: int = 1


@dataclass
class DeathrattleResult:
    face_damage: int = 0
    opponent_lifesteal_heal: int = 0
    armor_gain: int = 0
    uses_random: bool = False


DEATHRATTLE_BY_CARD: Dict[str, DeathrattleDef] = {
    # 已有
    "UNG_022": DeathrattleDef(DrKind.AOE_ALL_MINIONS, amount=1),
    "CORE_UNG_022": DeathrattleDef(DrKind.AOE_ALL_MINIONS, amount=1),
    # 1. 亡语直伤
    "TOY_642": DeathrattleDef(DrKind.LOWEST_ATTACKER, amount=3),
    "TLC_249": DeathrattleDef(DrKind.RANDOM_SPLIT_ATTACKERS, amount=2),
    "EDR_421": DeathrattleDef(DrKind.ALL_ATTACKERS, amount=1, default_script=1),
    "CATA_586": DeathrattleDef(DrKind.RANDOM_ATTACKER, amount=2),
    # 2. 亡语 AOE
    "GDB_226": DeathrattleDef(DrKind.AOE_OTHER_MINIONS, amount=2),
    "EDR_459": DeathrattleDef(DrKind.AOE_ATTACKER_MINIONS, amount=3),
    "AV_325": DeathrattleDef(DrKind.AOE_ATTACKER_MINIONS_ATK),
    "CORE_WC_701": DeathrattleDef(DrKind.AOE_ATTACKER_MINIONS, amount=1),
    # 3. 兆示亡语 token
    "CATA_580t": DeathrattleDef(DrKind.RANDOM_ATTACKER_SCRIPT, default_script=2),
    "CATA_150t": DeathrattleDef(DrKind.RANDOM_ATTACKER_SCRIPT, default_script=2),
    "CATA_150t1": DeathrattleDef(DrKind.RANDOM_ATTACKER_SCRIPT, default_script=2),
    # 4. 亡语召唤嘲讽
    "ETC_526": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=9, summon_health=9,
        summon_taunt=True, summon_charge=True, summon_card_id="ETC_526t",
    ),
    "FP1_012": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=1, summon_health=2,
        summon_taunt=True, summon_card_id="FP1_012t",
    ),
    "RLK_554": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=4, summon_health=4,
        summon_taunt=True, summon_card_id="RLK_554t",
    ),
    # 亡语召唤嘲讽（扩展）
    "AV_337": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=4,
        summon_taunt=True, summon_count=2, summon_card_id="AV_337t",
    ),
    "CORE_AV_337": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=4,
        summon_taunt=True, summon_count=2, summon_card_id="AV_337t",
    ),
    "TOY_914": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=4, summon_health=6,
        summon_taunt=True, summon_count=2, summon_card_id="TOY_914t",
    ),
    "BT_761": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=5, summon_health=9,
        summon_taunt=True, summon_card_id="BT_761t",
    ),
    # 亡语护甲
    "SW_068": DeathrattleDef(DrKind.ENEMY_ARMOR, amount=8),
    "CORE_SW_068": DeathrattleDef(DrKind.ENEMY_ARMOR, amount=8),
    # 甲龙：2 只 3/3 野兽各随机攻击一次（简化，不留场）
    "DINO_422": DeathrattleDef(
        DrKind.SUMMON_ATTACK_ATTACKERS,
        summon_atk=3, summon_health=3, summon_count=2,
    ),
}


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(0)


def _ensure_sim_meta(enemy_board: List[dict]) -> dict:
    if enemy_board and enemy_board[0].get("kind") == "sim_meta":
        return enemy_board[0]
    meta = {"kind": "sim_meta", "armor": 0}
    enemy_board.insert(0, meta)
    return meta


def sim_armor_gain(enemy_board: List[dict]) -> int:
    """模拟中敌方亡语获得的额外护甲（如莫尔葛熔魔）。"""
    if enemy_board and enemy_board[0].get("kind") == "sim_meta":
        return int(enemy_board[0].get("armor", 0) or 0)
    return 0


def _script_damage(dead: dict, default: int) -> int:
    for key in ("script_data_num_1", "TAG_SCRIPT_DATA_NUM_1"):
        val = dead.get(key)
        if val is not None and int(val) > 0:
            return int(val)
    tags = dead.get("tags") or {}
    val = tags.get("TAG_SCRIPT_DATA_NUM_1")
    if val is not None and int(val) > 0:
        return int(val)
    return default


def _living_enemy_minions(enemy_board: List[dict]) -> List[dict]:
    from .combat_sim import unit_is_dormant

    return [
        m for m in enemy_board
        if m.get("health", 0) > 0
        and m.get("kind") not in ("hero", "sim_meta")
        and not unit_is_dormant(m)
    ]


def _living_attacker_minions(fighters: List[dict]) -> List[dict]:
    return [
        f for f in fighters
        if f.get("kind") == "minion" and f.get("health", 0) > 0
    ]


def _effective_health(unit: dict) -> int:
    return max(int(unit.get("health", 0) or 0), 0)


def _pick_lowest(units: List[dict]) -> Optional[dict]:
    alive = [u for u in units if _effective_health(u) > 0]
    if not alive:
        return None
    return min(alive, key=_effective_health)


def _next_enemy_entity_id(enemy_board: List[dict], fighters: List[dict]) -> int:
    used = {
        m.get("entity_id")
        for m in enemy_board
        if m.get("entity_id") is not None
    }
    used.update(
        f.get("entity_id")
        for f in fighters
        if f.get("entity_id") is not None
    )
    eid = -1
    while eid in used:
        eid -= 1
    return eid


def _apply_damage(unit: dict, amount: int) -> int:
    """对单位造成伤害，返回实际血量伤害（用于吸血）。"""
    if amount <= 0 or unit.get("health", 0) <= 0:
        return 0
    if unit.get("shield"):
        unit["shield"] = False
        amount -= 1
        if amount <= 0:
            return 0
    dealt = min(amount, max(unit["health"], 0))
    unit["health"] -= amount
    return dealt


def _summon_enemy_minion(
    enemy_board: List[dict],
    fighters: List[dict],
    *,
    atk: int,
    health: int,
    taunt: bool = False,
    charge: bool = False,
    card_id: str = "",
) -> None:
    enemy_board.append({
        "entity_id": _next_enemy_entity_id(enemy_board, fighters),
        "kind": "minion",
        "card_id": card_id,
        "atk": max(atk, 0),
        "health": max(health, 0),
        "shield": False,
        "poisonous": False,
        "lifesteal": False,
        "spell_immune": False,
        "taunt": taunt,
        "charge": charge,
        "rush": False,
    })


def _summon_friendly_minion_dr(
    fighters: List[dict],
    *,
    atk: int,
    health: int,
    taunt: bool = False,
    charge: bool = False,
    card_id: str = "",
) -> None:
    """疯狂药水等：亡语按我方触发时在己方可攻击列表召唤（当回合失调）。"""
    attacks_left, can_face = (1, True) if charge else (0, False)
    fighters.append({
        "kind": "minion",
        "entity_id": _next_enemy_entity_id([], fighters),
        "card_id": card_id,
        "atk": max(atk, 0),
        "health": max(health, 0),
        "shield": False,
        "poisonous": False,
        "lifesteal": False,
        "taunt": taunt,
        "charge": charge,
        "rush": False,
        "attacks_left": attacks_left,
        "can_face": can_face,
    })


def _damage_and_maybe_dr(
    unit: dict,
    amount: int,
    *,
    dead: dict,
    enemy_board: List[dict],
    fighters: List[dict],
    enemy_shield: bool,
    rng: random.Random,
    result: DeathrattleResult,
) -> None:
    if unit is dead:
        return
    was_alive = unit.get("health", 0) > 0
    dealt = _apply_damage(unit, amount)
    if unit.get("lifesteal") and dealt > 0:
        result.opponent_lifesteal_heal += dealt
    if was_alive and unit.get("health", 0) <= 0 and unit.get("kind") != "hero":
        sub = resolve_minion_death(
            unit, enemy_board, fighters,
            enemy_shield=enemy_shield, rng=rng,
        )
        result.face_damage += sub.face_damage
        result.opponent_lifesteal_heal += sub.opponent_lifesteal_heal
        result.armor_gain += sub.armor_gain
        result.uses_random = result.uses_random or sub.uses_random


def resolve_minion_death(
    dead: dict,
    enemy_board: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool = False,
    rng: Optional[random.Random] = None,
) -> DeathrattleResult:
    """伤害致死：先尝试复生，再触发亡语。"""
    from .reborn import try_reborn_revive

    if try_reborn_revive(dead):
        return DeathrattleResult()
    return on_minion_died(
        dead, enemy_board, fighters,
        enemy_shield=enemy_shield, rng=rng,
    )


def on_minion_died(
    dead: dict,
    enemy_board: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool = False,
    enemy_hero_hp: int = 0,
    rng: Optional[random.Random] = None,
) -> DeathrattleResult:
    """
    随从死亡时触发亡语（交换或法术击杀均调用）。

    enemy_board: 敌方全场随从列表（含非嘲讽；召唤类亡语写入此列表）。
    fighters: 己方可攻击单位（随从/武器/英雄临时攻）。
    stolen_turn（疯狂药水）亡语按我方触发。
    """
    cid = dead.get("card_id") or ""
    effect = DEATHRATTLE_BY_CARD.get(cid)
    if not effect:
        return DeathrattleResult()

    r = _rng(rng)
    result = DeathrattleResult()
    kind = effect.kind
    friendly = bool(dead.get("stolen_turn"))

    if kind == DrKind.AOE_ALL_MINIONS:
        d = effect.amount
        if friendly:
            for m in _living_enemy_minions(enemy_board):
                _damage_and_maybe_dr(
                    m, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )
        else:
            for m in _living_enemy_minions(enemy_board):
                _damage_and_maybe_dr(
                    m, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )
            for f in _living_attacker_minions(fighters):
                _damage_and_maybe_dr(
                    f, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )

    elif kind == DrKind.AOE_OTHER_MINIONS:
        d = effect.amount
        if friendly:
            for m in _living_enemy_minions(enemy_board):
                if m is dead:
                    continue
                _damage_and_maybe_dr(
                    m, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )
        else:
            for m in _living_enemy_minions(enemy_board):
                if m is dead:
                    continue
                _damage_and_maybe_dr(
                    m, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )
            for f in _living_attacker_minions(fighters):
                _damage_and_maybe_dr(
                    f, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                    enemy_shield=enemy_shield, rng=r, result=result,
                )

    elif kind == DrKind.AOE_ATTACKER_MINIONS:
        d = effect.amount
        targets = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        for unit in targets:
            _damage_and_maybe_dr(
                unit, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.AOE_ATTACKER_MINIONS_ATK:
        d = max(int(dead.get("atk", 0)), 0)
        targets = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        for unit in targets:
            _damage_and_maybe_dr(
                unit, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.LOWEST_ATTACKER:
        pool = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        if friendly:
            if enemy_hero_hp > 0:
                pool = list(pool)
                pool.append({
                    "kind": "hero",
                    "health": enemy_hero_hp,
                    "shield": enemy_shield,
                })
        target = _pick_lowest(pool)
        if target is not None:
            if target.get("kind") == "hero":
                from .board_damage import apply_divine_shield_to_hits
                result.face_damage += apply_divine_shield_to_hits(
                    [effect.amount], enemy_shield,
                )
            else:
                _damage_and_maybe_dr(
                    target, effect.amount, dead=dead, enemy_board=enemy_board,
                    fighters=fighters, enemy_shield=enemy_shield, rng=r, result=result,
                )

    elif kind == DrKind.RANDOM_SPLIT_ATTACKERS:
        result.uses_random = True
        for _ in range(max(effect.amount, 0)):
            units = (
                _living_enemy_minions(enemy_board) if friendly
                else _living_attacker_minions(fighters)
            )
            if not units:
                break
            target = r.choice(units)
            _damage_and_maybe_dr(
                target, 1, dead=dead, enemy_board=enemy_board, fighters=fighters,
                enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.ALL_ATTACKERS:
        d = _script_damage(dead, effect.default_script or effect.amount)
        targets = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        for unit in targets:
            _damage_and_maybe_dr(
                unit, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.RANDOM_ATTACKER:
        result.uses_random = True
        units = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        if units:
            target = r.choice(units)
            _damage_and_maybe_dr(
                target, effect.amount, dead=dead, enemy_board=enemy_board,
                fighters=fighters, enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.RANDOM_ATTACKER_SCRIPT:
        result.uses_random = True
        d = _script_damage(dead, effect.default_script)
        units = (
            _living_enemy_minions(enemy_board) if friendly
            else _living_attacker_minions(fighters)
        )
        if units:
            target = r.choice(units)
            _damage_and_maybe_dr(
                target, d, dead=dead, enemy_board=enemy_board, fighters=fighters,
                enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.SUMMON_ENEMY:
        for _ in range(max(effect.summon_count, 1)):
            if friendly:
                _summon_friendly_minion_dr(
                    fighters,
                    atk=effect.summon_atk,
                    health=effect.summon_health,
                    taunt=effect.summon_taunt,
                    charge=effect.summon_charge,
                    card_id=effect.summon_card_id,
                )
            else:
                _summon_enemy_minion(
                    enemy_board, fighters,
                    atk=effect.summon_atk,
                    health=effect.summon_health,
                    taunt=effect.summon_taunt,
                    charge=effect.summon_charge,
                    card_id=effect.summon_card_id,
                )

    elif kind == DrKind.SUMMON_ATTACK_ATTACKERS:
        result.uses_random = True
        atk = effect.summon_atk
        for _ in range(max(effect.summon_count, 1)):
            units = (
                _living_enemy_minions(enemy_board) if friendly
                else _living_attacker_minions(fighters)
            )
            if not units:
                break
            target = r.choice(units)
            _damage_and_maybe_dr(
                target, atk, dead=dead, enemy_board=enemy_board,
                fighters=fighters, enemy_shield=enemy_shield, rng=r, result=result,
            )

    elif kind == DrKind.ENEMY_ARMOR and not friendly:
        gain = max(effect.amount, 0)
        meta = _ensure_sim_meta(enemy_board)
        meta["armor"] = int(meta.get("armor", 0) or 0) + gain
        result.armor_gain += gain

    return result


def remove_dead_taunts(taunts: List[dict]) -> None:
    taunts[:] = [
        t for t in taunts
        if t.get("kind") == "sim_meta" or t.get("health", 0) > 0
    ]


def remove_dead_fighters(fighters: List[dict]) -> None:
    fighters[:] = [
        f for f in fighters
        if f.get("health", 0) > 0 and (f.get("attacks_left", 0) > 0 or f.get("kind") == "weapon")
    ]
