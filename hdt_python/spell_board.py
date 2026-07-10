# spell_board.py - 手牌法术解场 / 直伤，参与场攻与清嘲讽模拟

from __future__ import annotations

import json
import random
from copy import deepcopy
from dataclasses import dataclass, field
from enum import IntEnum
from functools import lru_cache
from pathlib import Path

from hdt_python.app_paths import resource_path
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import apply_divine_shield_to_hits
from .combat_sim import project_board_face_after_spell
from .deathrattle import on_minion_died, remove_dead_taunts, resolve_minion_death

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

MC_TRIALS = 2000
# 法术 combo 搜索上限；None = 全枚举（子集+排列+空序列，仍受 mana_budget 剪枝）
MAX_SPELL_SEQUENCES: Optional[int] = None
# 单条 combo 最多几张法术；None = 不限制
MAX_SPELL_COMBO_LEN: Optional[int] = 7


def _rng_or_default(rng: Optional[random.Random] = None) -> random.Random:
    """分层推断等无显式 RNG 时用固定种子，保证结果稳定。"""
    return rng if rng is not None else random.Random(0)


# 圣杖埃提耶识：法术伤害与治疗翻倍
ATIESH_WEAPON_IDS = frozenset({
    "TIME_890t",   # 圣杖埃提耶识（Medivh the Hallowed 衍生）
    "TIME_890t1",
})


@dataclass
class SpellApplyResult:
    """法术模拟结果。"""
    opponent_lifesteal_heal: int = 0
    direct_face_damage: int = 0  # 对敌方英雄的直接伤害（如月亮井）
    battlecry_face_damage: int = 0  # 战吼随从造成的打脸（与法术分项分开）
    self_hero_damage: int = 0  # 对我方英雄的自伤（如夜影花茶）
    self_hero_heal: int = 0  # 法术吸血等为我方英雄回复
    drinks_after: int = 0  # 打出后剩余杯数；0 表示不回手
    add_hand_spell_id: Optional[str] = None  # 置入手的衍生法术 card_id
    add_hand_spell_damage: int = 0  # 衍生法术的动态伤害（如影叶瓶子）
    add_hand_pending: List[Tuple[str, int, int]] = field(default_factory=list)
    # (card_id, cost, override_damage)；override_damage>0 时覆盖默认伤害
    mana_crystal_gain: int = 0  # 野性成长等：增加剩余可用法力
    consume_hand_entity_ids: Tuple[int, ...] = ()


@dataclass(frozen=True)
class BoardSpellDef:
    card_ids: Tuple[str, ...]
    base_cost: int
    name: str
    apply: Callable[..., SpellApplyResult]
    cost_fn: Optional[Callable[["GameState", int], int]] = None
    uses_random: bool = False


# 会对己方随从造成伤害的法术（先打会清掉场面场攻）
SPELLS_DAMAGE_ALL_MINIONS = frozenset({
    "CATA_581",   # 屠灭
    "CS2_062",    # 地狱烈焰
    "CORE_CS2_062",
    "LOOT_417",   # 大灾变
    "GDB_301",    # 超级新星
})


def has_atiesh_weapon(gs: "GameState", player_id: int) -> bool:
    weapon = gs.get_weapon(player_id)
    if not weapon or weapon.current_durability <= 0:
        return False
    cid = weapon.card_id or ""
    return cid in ATIESH_WEAPON_IDS


def total_spell_power(gs: Optional["GameState"], player_id: Optional[int]) -> int:
    """场面法强 + 英雄 CURRENT_SPELLPOWER_BASE（如艾杰斯亚导师 +2）。"""
    if gs is None or player_id is None:
        return 0
    total = 0
    for entity in gs.get_board(player_id):
        if entity.current_health > 0:
            total += int(entity.tags.get("SPELLPOWER", 0) or 0)
    hero = gs.get_hero(player_id)
    if hero:
        total += int(hero.tags.get("CURRENT_SPELLPOWER_BASE", 0) or 0)
    return total


def scaled_spell_damage(base: int, *, mult: int = 1, spell_power: int = 0) -> int:
    """炉石法术伤害：(基础 + 法强) × 埃提耶识翻倍。"""
    return (max(base, 0) + spell_power) * mult


def spell_effect_multiplier(gs: "GameState", player_id: int) -> int:
    """埃提耶识翻倍；场面/英雄法强见 total_spell_power + scaled_spell_damage。"""
    return 2 if has_atiesh_weapon(gs, player_id) else 1


def _dragon_race_value(tags: dict) -> object:
    return (
        tags.get("CARDRACE")
        or tags.get("RACE")
        or tags.get("516")
    )


def entity_is_dragon(entity) -> bool:
    """随从实体是否为龙（CARDRACE / DRAGON 标签）。"""
    if entity is None:
        return False
    tags = getattr(entity, "tags", {}) or {}
    if tags.get("DRAGON"):
        return True
    return _dragon_race_value(tags) in ("DRAGON", 24)


def unit_is_dragon(unit: dict) -> bool:
    """模拟场面 dict 是否为龙。"""
    if unit.get("dragon"):
        return True
    tags = unit.get("tags") or {}
    if tags.get("DRAGON"):
        return True
    race = unit.get("cardrace") or _dragon_race_value(tags)
    return race in ("DRAGON", 24)


def _apply_damage(
    unit: dict,
    amount: int,
    *,
    taunts: Optional[List[dict]] = None,
    fighters: Optional[List[dict]] = None,
) -> int:
    """对模拟单位造成伤害，返回对手因吸血获得的回复量。击杀时触发亡语。"""
    if amount <= 0 or unit.get("health", 0) <= 0:
        return 0
    heal = 0
    was_alive = unit.get("health", 0) > 0
    if unit.get("shield"):
        unit["shield"] = False
        amount -= 1
        if amount <= 0:
            return 0
    dealt = min(amount, max(unit["health"], 0))
    unit["health"] -= amount
    if was_alive and unit.get("health", 0) <= 0 and taunts is not None and fighters is not None:
        resolve_minion_death(unit, taunts, fighters)
    if unit.get("lifesteal") and dealt > 0:
        heal += dealt
    return heal


def _heal_unit(unit: dict, amount: int) -> None:
    if amount <= 0 or unit.get("health", 0) <= 0:
        return
    unit["health"] += amount


def _remove_dead_taunts(taunts: List[dict]) -> None:
    remove_dead_taunts(taunts)


def _is_unit_frozen(unit: dict) -> bool:
    return bool(unit.get("frozen", False))


def _steal_enemy_minion_to_fighter(
    unit: dict,
    taunts: List[dict],
    fighters: List[dict],
) -> bool:
    """
    疯狂药水：移出敌方场面，加入己方可攻击列表（不触发亡语）。
    未冰冻则可当回合攻击打脸。
    """
    if unit.get("health", 0) <= 0 or unit.get("kind") == "hero":
        return False
    if int(unit.get("atk", 0) or 0) > 2:
        return False
    if unit.get("spell_immune"):
        return False
    frozen = _is_unit_frozen(unit)
    fighters.append({
        "kind": "minion",
        "entity_id": unit.get("entity_id"),
        "card_id": unit.get("card_id", ""),
        "atk": int(unit.get("atk", 0) or 0),
        "health": int(unit.get("health", 0) or 0),
        "shield": bool(unit.get("shield")),
        "poisonous": bool(unit.get("poisonous")),
        "lifesteal": bool(unit.get("lifesteal")),
        "taunt": bool(unit.get("taunt")),
        "stolen_turn": True,
        "frozen": frozen,
        "attacks_left": 0 if frozen else 1,
        "can_face": not frozen,
        "rush": False,
        "charge": False,
    })
    unit["health"] = 0
    _remove_dead_taunts(taunts)
    return True


def _living_enemy_board_minions(taunts: List[dict]) -> List[dict]:
    """模拟中的敌方场面随从（休眠随从本回合忽视）。"""
    from .combat_sim import unit_is_active_minion

    return [t for t in taunts if unit_is_active_minion(t)]


def _living_enemy_taunts(taunts: List[dict]) -> List[dict]:
    """存活且带嘲讽的敌方随从（休眠忽视）。

    斩杀模拟默认：单体法术点敌方随从时仅用此列表（卡牌另有说明的除外）。
    """
    from .combat_sim import unit_is_dormant

    return [
        t for t in _living_enemy_board_minions(taunts)
        if t.get("taunt") and not unit_is_dormant(t)
    ]


def _spell_blocking_taunts(taunts: List[dict]) -> List[dict]:
    """阻挡法术打脸的嘲讽（魔法免疫/Elusive 嘲不阻挡法术选脸）。"""
    return [t for t in _living_enemy_taunts(taunts) if not t.get("spell_immune")]


def _can_spell_hit_enemy_face(taunts: List[dict]) -> bool:
    """无（非魔免）嘲讽阻挡时，单体法术方可对敌方英雄造成直伤。"""
    return not _spell_blocking_taunts(taunts)


# 表一「清场指向性法术」：无嘲讽时可遍历敌方随从（见 CLEAR_TARGETED_SPELL_TABLE.md）
CLEAR_TARGETED_POINTED_SPELL_IDS = frozenset({
    "CATA_303", "CATA_978", "CFM_662", "CORE_EX1_309", "CORE_EX1_391",
    "CORE_RLK_087", "CORE_SW_108", "DAL_716", "DED_517", "DMF_117",
    "DMF_117t", "DMF_117t2", "DREAM_01", "EDR_262", "EDR_460", "ETC_394",
    "FIR_954", "GDB_460", "GDB_902", "JAM_002", "MIS_903", "NX2_020",
    "REV_239", "REV_249", "REV_939", "RLK_018", "SCH_512", "SW_090",
    "SW_108", "SW_108t", "TIME_216", "TIME_433", "TIME_712", "TLC_901",
    "ULD_714", "UNG_955", "VAC_404", "VAC_404t1", "VAC_404t2", "VAC_951",
    "VAC_951t", "VAC_951t2", "WC_021", "WORK_014", "WW_393",
})


# 须指定敌方随从方可打出（无随从时不可对英雄单独使用）
SPELL_REQUIRES_ENEMY_MINION = frozenset({
    "TTN_853",  # 审判恶徒
})

# 须指定友方随从方可打出
SPELL_REQUIRES_FRIENDLY_MINION = frozenset({
    "WW_027",  # 可靠陪伴
    "MAW_021",  # 问心无愧
    "CORE_MAW_021",
    "JAIL_913",  # 拦住他们！
    "ETC_201", "ETC_201t", "ETC_201t2",  # 一串香蕉
})


def enemy_board_has_targetable_minion(
    gs: "GameState",
    player_id: int,
) -> bool:
    """对手场面是否存在可被法术指定的随从（非魔免）。"""
    board = _sim_enemy_board_for_apply(gs, player_id)
    return bool([
        t for t in _living_enemy_board_minions(board)
        if not t.get("spell_immune")
    ])


def friendly_board_has_spell_target_minion(
    gs: "GameState",
    player_id: int,
) -> bool:
    """己方场面是否存在可被法术指定的随从（非魔免）。"""
    from .lethal_checker import LethalChecker

    lc = LethalChecker(gs)
    board_view = gs.get_overlay_board(player_id)
    fighters = lc._build_fighters(board_view, player_id)
    return bool(_friendly_spell_target_minions(fighters, gs, player_id))


def pick_judge_unworthy_target(taunts: List[dict]) -> Optional[dict]:
    """审判恶徒点选：优先最高生命，其次最高攻击的敌方随从。"""
    living = [
        t for t in _living_enemy_board_minions(taunts)
        if not t.get("spell_immune")
    ]
    if not living:
        return None
    return max(
        living,
        key=lambda t: (int(t.get("health", 0) or 0), int(t.get("atk", 0) or 0)),
    )


def clear_targeted_pointed_allows_no_taunt_minion(
    *,
    card: Optional["Entity"] = None,
    card_id: Optional[str] = None,
    defn: Optional[BoardSpellDef] = None,
) -> bool:
    """清场指向性法术：无嘲讽时允许点敌方随从。"""
    cid = card_id or (getattr(card, "card_id", None) if card else None)
    if cid and cid in CLEAR_TARGETED_POINTED_SPELL_IDS:
        return True
    if defn is not None:
        return any(c in CLEAR_TARGETED_POINTED_SPELL_IDS for c in defn.card_ids)
    return False


def _resolve_allow_no_taunt_minion_targets(
    *,
    allow_no_taunt_minion_targets: bool = False,
    card: Optional["Entity"] = None,
) -> bool:
    return allow_no_taunt_minion_targets or clear_targeted_pointed_allows_no_taunt_minion(
        card=card,
    )


def _iter_spell_minion_target_indices(
    taunts: List[dict],
    *,
    allow_all_without_taunt: bool = False,
    card: Optional["Entity"] = None,
) -> List[int]:
    """
    斩杀模拟：单体法术点随从时，场上仍有嘲讽则只试嘲讽随从；
    无嘲讽时默认不用法术点随从；清场指向性法术可遍历存活敌方随从。
    """
    allow_all_without_taunt = _resolve_allow_no_taunt_minion_targets(
        allow_no_taunt_minion_targets=allow_all_without_taunt,
        card=card,
    )
    if _living_enemy_taunts(taunts):
        out: List[int] = []
        for i, t in enumerate(taunts):
            if t.get("health", 0) <= 0 or t.get("kind") == "hero":
                continue
            if not t.get("taunt") or t.get("spell_immune"):
                continue
            out.append(i)
        return out
    if not allow_all_without_taunt:
        return []
    out: List[int] = []
    for i, t in enumerate(taunts):
        if t.get("health", 0) <= 0 or t.get("kind") == "hero":
            continue
        if t.get("spell_immune"):
            continue
        out.append(i)
    return out


def _lethal_target_enemy_minions(
    taunts: List[dict],
    *,
    allow_all_without_taunt: bool = False,
    card: Optional["Entity"] = None,
) -> List[dict]:
    """消灭/沉默等点选随从：有嘲讽只选嘲讽；清场指向性无嘲讽时可点任意敌方随从。"""
    allow_all_without_taunt = _resolve_allow_no_taunt_minion_targets(
        allow_no_taunt_minion_targets=allow_all_without_taunt,
        card=card,
    )
    if not _living_enemy_taunts(taunts):
        if not allow_all_without_taunt:
            return []
        return [
            t for t in _living_enemy_board_minions(taunts)
            if not t.get("spell_immune")
        ]
    return [
        t for t in _living_enemy_board_minions(taunts)
        if t.get("taunt") and not t.get("spell_immune")
    ]


def _strip_enemy_minion_keywords(unit: dict) -> None:
    """衰变简化：去关键词与亡语标识，保留攻血/圣盾等身材。"""
    if unit.get("kind") == "hero" or unit.get("health", 0) <= 0:
        return
    unit["taunt"] = False
    unit["lifesteal"] = False
    unit["poisonous"] = False
    unit["spell_immune"] = False
    unit["charge"] = False
    unit["rush"] = False
    unit["card_id"] = ""


def _destroy_enemy_minion(
    unit: dict,
    taunts: List[dict],
    fighters: List[dict],
) -> None:
    """消灭敌方随从（非伤害），触发亡语。"""
    if unit.get("kind") == "hero" or unit.get("health", 0) <= 0:
        return
    unit["health"] = 0
    on_minion_died(unit, taunts, fighters)
    _remove_dead_taunts(taunts)


def _apply_random_destroy_enemy_minions(
    taunts: List[dict],
    fighters: List[dict],
    *,
    count: int,
    rng: Optional[random.Random] = None,
) -> SpellApplyResult:
    """随机消灭 count 个敌方随从（可重复随机直到不足）。"""
    roll = _rng_or_default(rng)
    for _ in range(max(count, 0)):
        living = _living_enemy_board_minions(taunts)
        if not living:
            break
        target = roll.choice(living)
        _destroy_enemy_minion(target, taunts, fighters)
    return SpellApplyResult()


def _hero_unit(enemy_shield: bool, *, hero_hp: Optional[int] = None) -> dict:
    """hero_hp 未知时用极大值，避免无场面上下文时误判「最低血=英雄」。"""
    hp = hero_hp if hero_hp is not None else 10**9
    return {
        "kind": "hero",
        "health": hp,
        "shield": enemy_shield,
        "lifesteal": False,
        "atk": 0,
        "poisonous": False,
    }


def _resolve_opponent_hero_hp(
    gs: Optional["GameState"],
    player_id: Optional[int],
) -> Optional[int]:
    """对手英雄有效生命（血+甲），用于「最低血量敌人」比较。"""
    if gs is None or player_id is None:
        return None
    opp = gs.opponent_player_id
    if opp is None or player_id != gs.local_player_id:
        if gs.local_player_id is not None and player_id == gs.opponent_player_id:
            opp = gs.local_player_id
        else:
            return None
    hero = gs.get_hero(opp)
    if hero is None:
        return None
    hp = hero.current_health + int(hero.tags.get("ARMOR", 0) or 0)
    if hp <= 0 and hero.health == 0:
        hp = 30
    return max(hp, 0)


def _sim_enemy_board_for_apply(
    gs: Optional["GameState"],
    player_id: Optional[int],
) -> List[dict]:
    """从 GameState 构建敌方随从模拟列表（与 LethalChecker._build_enemy_minion_states 一致）。"""
    if gs is None or player_id is None:
        return []
    from .lethal_checker import LethalChecker

    return LethalChecker(gs)._build_enemy_minion_states(player_id)


def _target_key(unit: dict):
    if unit.get("kind") == "hero":
        return ("hero",)
    eid = unit.get("entity_id")
    if eid is not None:
        return ("minion", eid)
    return ("minion", id(unit))


def _apply_direct_face(damage: int, enemy_shield: bool) -> SpellApplyResult:
    face = apply_divine_shield_to_hits([max(damage, 0)], enemy_shield)
    return SpellApplyResult(direct_face_damage=face)


def _apply_optimal_single_target_damage(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool,
    return_primary_key: bool = False,
    **_kw,
):
    """
    可选目标「造成 N 点伤害」：斩杀模拟仅考虑「打脸（无嘲讽时）」或「点嘲讽随从」。
    在嘲讽与各嘲讽随从之间选「法术直伤 + 解嘲后随从打脸」最大的目标。
    return_primary_key=True 时返回 (SpellApplyResult, primary_target_key)。
    """
    amount = max(damage, 0)
    if amount <= 0:
        empty = SpellApplyResult()
        return (empty, ("hero",)) if return_primary_key else empty

    best_score = -1
    best_face_hit = False
    best_minion_idx: Optional[int] = None

    def _score(hit_face: bool, minion_idx: Optional[int]) -> int:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        direct = 0
        if hit_face:
            direct = apply_divine_shield_to_hits([amount], enemy_shield)
        else:
            assert minion_idx is not None
            target = ts[minion_idx]
            _, direct, _ = _apply_damage_to_unit(
                target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
            )
            _remove_dead_taunts(ts)
        return direct + project_board_face_after_spell(ts, fs, enemy_shield)

    if _can_spell_hit_enemy_face(taunts):
        face_score = _score(True, None)
        best_score = face_score
        best_face_hit = True

    for i in _iter_spell_minion_target_indices(taunts):
        s = _score(False, i)
        if s > best_score:
            best_score = s
            best_face_hit = False
            best_minion_idx = i

    if best_score < 0:
        empty = SpellApplyResult()
        return (empty, ("hero",)) if return_primary_key else empty

    if best_face_hit:
        res = _apply_direct_face(amount, enemy_shield)
        return (res, ("hero",)) if return_primary_key else res

    assert best_minion_idx is not None
    res = SpellApplyResult()
    target = taunts[best_minion_idx]
    heal, face, _ = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    res.direct_face_damage = face
    _remove_dead_taunts(taunts)
    if return_primary_key:
        return res, _target_key(target)
    return res


def _effective_health(unit: dict) -> int:
    return max(int(unit.get("health", 0) or 0), 0)


def _pick_lowest_unit(units: List[dict]) -> Optional[dict]:
    alive = [
        u for u in units
        if u.get("kind") == "hero" or _effective_health(u) > 0
    ]
    if not alive:
        return None
    return min(alive, key=lambda u: _effective_health(u))


def _living_enemy_units(
    taunts: List[dict],
    enemy_shield: bool,
    *,
    spell_targetable_only: bool = False,
    hero_hp: Optional[int] = None,
) -> List[dict]:
    units: List[dict] = []
    for t in taunts:
        if t.get("health", 0) <= 0:
            continue
        if spell_targetable_only and t.get("spell_immune"):
            continue
        units.append(t)
    units.append(_hero_unit(enemy_shield, hero_hp=hero_hp))
    return units


def _damage_dealt_preview(unit: dict, amount: int) -> int:
    """预估对随从造成的伤害量（含破圣盾的 1 点），用于法术吸血。"""
    if amount <= 0 or unit.get("health", 0) <= 0:
        return 0
    amt = amount
    dealt = 0
    if unit.get("shield"):
        dealt += 1
        amt -= 1
        if amt <= 0:
            return dealt
    dealt += min(amt, max(unit.get("health", 0), 0))
    return dealt


def _apply_damage_to_unit(
    unit: dict,
    amount: int,
    *,
    taunts: List[dict],
    fighters: List[dict],
    enemy_shield: bool,
) -> Tuple[int, int, int]:
    """返回 (对手随从吸血回复, 对英雄直伤, 实际伤害量)。"""
    if amount <= 0:
        return 0, 0, 0
    if unit.get("kind") == "hero":
        face = apply_divine_shield_to_hits([amount], enemy_shield)
        unit["shield"] = False
        return 0, face, 0
    dealt = _damage_dealt_preview(unit, amount)
    heal = _apply_damage(unit, amount, taunts=taunts, fighters=fighters)
    return heal, 0, dealt


def _apply_lowest_enemy_hits(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    hits: int,
    enemy_shield: bool,
    self_lifesteal: bool = False,
    **kw,
) -> SpellApplyResult:
    gs = kw.get("gs")
    player_id = kw.get("player_id")
    opp_hp_kw = kw.get("opponent_hero_hp")
    hero_hp = (
        opp_hp_kw if opp_hp_kw is not None
        else _resolve_opponent_hero_hp(gs, player_id)
    )
    shield = enemy_shield
    res = SpellApplyResult()
    for _ in range(hits):
        units = _living_enemy_units(
            taunts, shield, spell_targetable_only=True, hero_hp=hero_hp,
        )
        target = _pick_lowest_unit(units)
        if target is None:
            break
        heal, face, dealt = _apply_damage_to_unit(
            target, damage, taunts=taunts, fighters=fighters, enemy_shield=shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
        if self_lifesteal and target.get("kind") != "hero":
            res.self_hero_heal += dealt
        if target.get("kind") == "hero":
            if shield and face == 0 and damage > 0:
                shield = False
            elif face > 0 and hero_hp is not None:
                hero_hp = max(0, hero_hp - face)
    _remove_dead_taunts(taunts)
    return res


def _apply_split_to_lowest(
    taunts: List[dict],
    fighters: List[dict],
    total_damage: int,
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    res = SpellApplyResult()
    remaining = total_damage
    while remaining > 0:
        units = _living_enemy_units(taunts, enemy_shield, spell_targetable_only=True)
        target = _pick_lowest_unit(units)
        if target is None:
            break
        heal, face, _ = _apply_damage_to_unit(
            target, 1, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
        remaining -= 1
    _remove_dead_taunts(taunts)
    return res


def _apply_random_enemy_hits(
    taunts: List[dict],
    fighters: List[dict],
    *,
    hits: int,
    damage: int,
    enemy_shield: bool,
    rng: Optional[random.Random] = None,
    exclude_hero: bool = False,
    distinct_targets: bool = False,
    exclude_keys: Optional[set] = None,
) -> SpellApplyResult:
    """distinct_targets=True 时各次伤害不能重复命中同一单位；exclude_keys 预先排除（如奥术弹幕主目标）。"""
    res = SpellApplyResult()
    roll = _rng_or_default(rng)
    used: set = set(exclude_keys or ())
    hero = None if exclude_hero else _hero_unit(enemy_shield)
    for _ in range(hits):
        units = [t for t in taunts if t.get("health", 0) > 0]
        if hero is not None:
            units.append(hero)
        units = [u for u in units if _target_key(u) not in used]
        if not units:
            break
        target = roll.choice(units)
        if distinct_targets:
            used.add(_target_key(target))
        heal, face, _ = _apply_damage_to_unit(
            target, damage, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
    _remove_dead_taunts(taunts)
    return res


def _apply_random_minion_hits(
    taunts: List[dict],
    fighters: List[dict],
    *,
    hits: int,
    damage: int,
    enemy_shield: bool,
    rng: Optional[random.Random] = None,
) -> SpellApplyResult:
    return _apply_random_enemy_hits(
        taunts, fighters, hits=hits, damage=damage,
        enemy_shield=enemy_shield, rng=rng, exclude_hero=True,
    )


def _next_summon_entity_id(fighters: List[dict]) -> int:
    used = {
        f.get("entity_id")
        for f in fighters
        if f.get("kind") == "minion" and f.get("entity_id") is not None
    }
    eid = -1
    while eid in used:
        eid -= 1
    return eid


def _summon_friendly_fighter(
    fighters: List[dict],
    atk: int,
    health: int,
    *,
    charge: bool = False,
    rush: bool = False,
    poisonous: bool = False,
    taunt: bool = False,
    divine_shield: bool = False,
    lifesteal: bool = False,
    windfury: bool = False,
    card_id: str = "",
    from_hero_power: bool = False,
) -> None:
    """
    法术当回合召唤随从。
    冲锋：可打脸；突袭：仅可解场；否则召唤失调（本回合不能攻击）。
    """
    if charge:
        attacks_left, can_face = (2 if windfury else 1), True
    elif rush:
        attacks_left, can_face = (2 if windfury else 1), False
    else:
        attacks_left, can_face = 0, False
    fighters.append({
        "kind": "minion",
        "entity_id": _next_summon_entity_id(fighters),
        "card_id": card_id,
        "atk": max(atk, 0),
        "health": max(health, 0),
        "shield": divine_shield,
        "poisonous": poisonous,
        "taunt": taunt,
        "lifesteal": lifesteal,
        "attacks_left": attacks_left,
        "can_face": can_face,
        "rush": rush and not charge,
        "charge": charge,
        "windfury": windfury,
        "from_hero_power": from_hero_power,
    })


def _add_temp_hero_attack(
    fighters: List[dict],
    attack: int,
    *,
    from_hero_power: bool = False,
    can_face: bool = True,
) -> None:
    """法术/技能当回合给英雄临时攻击力（可打脸、可参与解嘲）。"""
    atk = max(0, int(attack))
    if atk <= 0:
        return
    fighters.append({
        "kind": "hero",
        "atk": atk,
        "health": 10**9,
        "attacks_left": 1,
        "can_face": can_face,
        "from_hero_power": from_hero_power,
    })


def _friendly_minion_count(
    fighters: List[dict],
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """
    友方存活随从总数（用于森林赠礼等按随从数计量的 buff）。
    fighters 仅含本回合可攻击者；须合并 gs 场面上的疲劳/刚召唤随从。
    """
    seen: set = set()
    count = 0
    for f in fighters:
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        eid = f.get("entity_id")
        if eid is not None:
            seen.add(eid)
        count += 1
    if gs is not None and player_id is not None:
        for m in gs.get_board(player_id):
            if m.entity_id in seen or m.current_health <= 0:
                continue
            count += 1
    return count


def _friendly_spell_target_minions(
    fighters: List[dict],
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> List[Tuple[str, object, dict]]:
    """
    可被我方法术指定的友方随从。
    返回 (来源, 键, 单位状态)：
      - ("fighter", 下标, unit) 已在 fighters 中
      - ("board", entity_id, unit) 场面有但本回合暂未进 fighters（如刚召唤）
    跳过 spell_immune / 魔免。
    """
    from .board_damage import entity_spell_immune, effective_attack_from_tags

    out: List[Tuple[str, object, dict]] = []
    seen: set = set()
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        if f.get("spell_immune"):
            continue
        eid = f.get("entity_id")
        if eid is not None:
            seen.add(eid)
        out.append(("fighter", i, f))
    if gs is not None and player_id is not None:
        for m in gs.get_board(player_id):
            eid = m.entity_id
            if eid in seen or m.current_health <= 0:
                continue
            if entity_spell_immune(m):
                continue
            atk = effective_attack_from_tags(m.tags)
            if atk <= 0 and m.atk > 0:
                atk = m.atk
            out.append(("board", eid, {
                "kind": "minion",
                "entity_id": eid,
                "card_id": m.card_id or "",
                "atk": atk,
                "health": m.current_health,
                "shield": m.tags.get("DIVINE_SHIELD", 0) == 1,
                "spell_immune": False,
                "attacks_left": 1,
                "can_face": True,
            }))
    return out


def _pick_best_spell_target_fighter(
    fighters: List[dict],
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> Optional[Tuple[str, object, dict]]:
    """可被我方法术指定的友方随从中，选场面价值最高者（跳过魔法免疫）。"""
    candidates = _friendly_spell_target_minions(fighters, gs, player_id)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            int(item[2].get("atk", 0) or 0)
            * max(int(item[2].get("attacks_left", 0) or 0), 1),
            int(item[2].get("atk", 0) or 0),
        ),
    )


def _apply_buff_to_spell_target(
    fighters: List[dict],
    picked: Tuple[str, object, dict],
    *,
    bonus_atk: int,
    bonus_health: int,
) -> None:
    """对单个可指定友方随从施加攻/血增益。"""
    src, key, unit = picked
    if src == "fighter":
        i = int(key)
        fighters[i] = dict(fighters[i])
        fighters[i]["atk"] = fighters[i].get("atk", 0) + bonus_atk
        fighters[i]["health"] = fighters[i].get("health", 0) + bonus_health
        return
    eid = key
    for i, f in enumerate(fighters):
        if f.get("entity_id") == eid:
            fighters[i] = dict(f)
            fighters[i]["atk"] = fighters[i].get("atk", 0) + bonus_atk
            fighters[i]["health"] = fighters[i].get("health", 0) + bonus_health
            return
    buffed = dict(unit)
    buffed["atk"] = buffed.get("atk", 0) + bonus_atk
    buffed["health"] = buffed.get("health", 0) + bonus_health
    fighters.append(buffed)


def _minion_max_health(unit: dict) -> int:
    return max(0, int(unit.get("health", 0)) + int(unit.get("damage", 0) or 0))


def _summon_minion_copy(fighters: List[dict], source: dict) -> None:
    """通窍等：召唤被击杀随从的复制（满血、保留攻/剧毒/冲锋/突袭）。"""
    _summon_friendly_fighter(
        fighters,
        int(source.get("atk", 0)),
        _minion_max_health(source),
        charge=bool(source.get("charge")),
        rush=bool(source.get("rush")),
        poisonous=bool(source.get("poisonous")),
    )


def _apply_targeted_minion(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool,
    heal_enemy_on_kill: int = 0,
    summon_on_kill: Optional[Tuple[int, int, bool]] = None,
    summon_copy_on_kill: bool = False,
    **kw,
) -> SpellApplyResult:
    """对最优敌方随从（优先嘲讽）造成伤害，可选击杀后对手回血。跳过魔法免疫。"""
    return _apply_best_minion_damage(
        taunts, fighters, damage,
        enemy_shield=enemy_shield,
        heal_enemy_on_kill=heal_enemy_on_kill,
        summon_on_kill=summon_on_kill,
        summon_copy_on_kill=summon_copy_on_kill,
        **kw,
    )


def _apply_best_minion_damage(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool,
    heal_enemy_on_kill: int = 0,
    filter_fn: Optional[Callable[[dict], bool]] = None,
    summon_on_kill: Optional[Tuple[int, int, bool]] = None,
    summon_copy_on_kill: bool = False,
    self_lifesteal: bool = False,
    allow_no_taunt_minion_targets: bool = False,
    **kw,
) -> SpellApplyResult:
    """对随从 N 伤：有嘲讽时只点嘲讽；清场指向性无嘲讽时可遍历随从择优。"""
    card = kw.get("card")
    allow_no_taunt = _resolve_allow_no_taunt_minion_targets(
        allow_no_taunt_minion_targets=allow_no_taunt_minion_targets,
        card=card,
    )
    amount = max(damage, 0)
    if amount <= 0:
        return SpellApplyResult()

    def _maybe_on_kill(fs: List[dict], target: dict, was_alive: bool) -> None:
        if not was_alive or target.get("health", 0) > 0:
            return
        if summon_on_kill:
            atk, hp, rush = summon_on_kill
            _summon_friendly_fighter(fs, atk, hp, rush=rush)
        elif summon_copy_on_kill:
            _summon_minion_copy(fs, target)

    best_score = -1
    best_idx: Optional[int] = None

    for i in _iter_spell_minion_target_indices(
        taunts, allow_all_without_taunt=allow_no_taunt, card=card,
    ):
        t = taunts[i]
        if filter_fn and not filter_fn(t):
            continue
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            ts[i],
        )
        was_alive = target.get("health", 0) > 0
        _apply_damage_to_unit(
            target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        _maybe_on_kill(fs, target, was_alive)
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return SpellApplyResult()

    res = SpellApplyResult()
    target = taunts[best_idx]
    was_alive = target.get("health", 0) > 0
    heal, _, dealt = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    if self_lifesteal:
        res.self_hero_heal = dealt
    if heal_enemy_on_kill and was_alive and target.get("health", 0) <= 0:
        res.opponent_lifesteal_heal += heal_enemy_on_kill
    _maybe_on_kill(fighters, target, was_alive)
    _remove_dead_taunts(taunts)
    return res


def _apply_enemy_minions_aoe(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """对所有敌方随从造成固定伤害（不含英雄）。"""
    res = SpellApplyResult()
    for t in list(taunts):
        res.opponent_lifesteal_heal += _apply_damage(
            t, damage, taunts=taunts, fighters=fighters,
        )
    _remove_dead_taunts(taunts)
    return res


def player_corpses(gs: "GameState", player_id: int) -> int:
    """读取己方残骸数（CORPSES tag，log 写在英雄或玩家名上）。"""
    hero = gs.get_hero(player_id)
    if hero:
        v = hero.tags.get("CORPSES")
        if v is not None:
            return max(0, int(v))
    name = gs.player_names.get(player_id)
    if name:
        ent = gs.entities.get(name) if hasattr(gs, "entities") else None
        if ent is None and hasattr(gs, "get_entity"):
            ent = gs.get_entity(name) if isinstance(name, int) else None
        if ent and ent.tags.get("CORPSES") is not None:
            return max(0, int(ent.tags["CORPSES"]))
    return 0


def _apply_hellfire(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    dmg = 3 * mult
    res = SpellApplyResult()
    for t in list(taunts):
        res.opponent_lifesteal_heal += _apply_damage(t, dmg, taunts=taunts, fighters=fighters)
    _remove_dead_taunts(taunts)
    for f in fighters:
        if f.get("kind") == "minion":
            _apply_damage(f, dmg, taunts=taunts, fighters=fighters)
    res.direct_face_damage = apply_divine_shield_to_hits([dmg], enemy_shield)
    res.self_hero_damage = dmg
    return res


def _apply_all_enemies_damage(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """对所有敌人造成伤害（随从 + 英雄直伤）。"""
    res = _apply_enemy_minions_aoe(
        taunts, fighters, damage, enemy_shield=enemy_shield,
    )
    res.direct_face_damage += apply_divine_shield_to_hits([damage], enemy_shield)
    return res


def _apply_all_minions_aoe_spell(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
) -> SpellApplyResult:
    heal = _apply_aoe_all_minions(taunts, fighters, damage)
    return SpellApplyResult(opponent_lifesteal_heal=heal)


def _minion_died_in_wave(
    units: List[dict],
    before: dict,
) -> bool:
    for u in units:
        key = _target_key(u)
        if before.get(key, 0) > 0 and u.get("health", 0) <= 0:
            return True
    return False


def _snapshot_health(units: List[dict]) -> dict:
    return {_target_key(u): u.get("health", 0) for u in units if u.get("health", 0) > 0}


def _any_death_since(before: dict, taunts: List[dict], fighters: List[dict]) -> bool:
    """对比波次前后：生命值归零或已从场面移除均视为死亡。"""
    still_present: set = set()
    for t in taunts:
        key = _target_key(t)
        still_present.add(key)
        if before.get(key, 0) > 0 and t.get("health", 0) <= 0:
            return True
    for f in fighters:
        if f.get("kind") != "minion":
            continue
        key = _target_key(f)
        still_present.add(key)
        if before.get(key, 0) > 0 and f.get("health", 0) <= 0:
            return True
    for key, hp in before.items():
        if hp > 0 and key not in still_present:
            return True
    return False


def _friendly_minions(fighters: List[dict]) -> List[dict]:
    return [
        f for f in fighters
        if f.get("kind") == "minion" and f.get("health", 0) > 0
    ]


def _apply_damage_wave_all_minions(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
) -> SpellApplyResult:
    """一轮：对所有随从造成固定伤害。"""
    res = SpellApplyResult()
    for t in list(taunts):
        res.opponent_lifesteal_heal += _apply_damage(
            t, damage, taunts=taunts, fighters=fighters,
        )
    _remove_dead_taunts(taunts)
    for f in fighters:
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            _apply_damage(f, damage, taunts=taunts, fighters=fighters)
    return res


def _apply_defile(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """亵渎：全场 1 伤循环，有随从死亡则再施放。"""
    dmg = max(1, mult)
    total = SpellApplyResult()
    while True:
        units = _living_enemy_board_minions(taunts) + _friendly_minions(fighters)
        if not units:
            break
        before = _snapshot_health(units)
        wave = _apply_damage_wave_all_minions(taunts, fighters, dmg)
        _merge_spell_result(total, wave)
        if not _any_death_since(before, taunts, fighters):
            break
    return total


def _apply_bladestorm(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """剑刃风暴：全场 1 伤循环，直到某轮有随从死亡。"""
    dmg = max(1, mult)
    total = SpellApplyResult()
    while True:
        units = _living_enemy_board_minions(taunts) + _friendly_minions(fighters)
        if not units:
            break
        before = _snapshot_health(units)
        wave = _apply_damage_wave_all_minions(taunts, fighters, dmg)
        _merge_spell_result(total, wave)
        if _any_death_since(before, taunts, fighters):
            break
    return total


def _apply_random_split_damage(
    taunts: List[dict],
    fighters: List[dict],
    total_damage: int,
    *,
    enemy_shield: bool,
    rng: Optional[random.Random] = None,
    include_friendly_minions: bool = False,
    include_enemy_hero: bool = False,
    effect_lifesteal: bool = False,
) -> SpellApplyResult:
    """
    将 total_damage 逐点随机分配到目标。
    默认：仅敌方随从。
    include_friendly_minions：所有随从（苏打火山，不含英雄）。
    include_enemy_hero：额外含敌方英雄（夕阳漫射等「所有敌人」）。
    effect_lifesteal：效果自带吸血，伤害量回复我方英雄（德纳修斯大帝战吼）。
    """
    res = SpellApplyResult()
    roll = _rng_or_default(rng)
    for _ in range(max(total_damage, 0)):
        units: List[dict] = [t for t in taunts if t.get("health", 0) > 0]
        if include_friendly_minions:
            units.extend(
                f for f in fighters
                if f.get("kind") == "minion" and f.get("health", 0) > 0
            )
        if include_enemy_hero:
            units.append(_hero_unit(enemy_shield))
        if not units:
            break
        target = roll.choice(units)
        heal, face, dealt = _apply_damage_to_unit(
            target, 1, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
        if effect_lifesteal:
            res.self_hero_heal += dealt + face
        _remove_dead_taunts(taunts)
    return res

SpellPlayStep = Tuple[BoardSpellDef, int, Optional["Entity"]]


# 腐蚀法术：打出更高费牌后升级（base -> 已腐蚀 card_id）
CORRUPT_SPELL_NEXT: Dict[str, str] = {
    "DMF_701": "DMF_701t",
}
CORRUPTED_SPELL_IDS = frozenset({"DMF_701t"})


def _resolve_corrupt_spell_id(card_id: str) -> Optional[str]:
    if not card_id:
        return None
    if card_id in CORRUPT_SPELL_NEXT:
        return CORRUPT_SPELL_NEXT[card_id]
    if card_id.startswith("CORE_"):
        base = card_id[5:]
        nxt = CORRUPT_SPELL_NEXT.get(base)
        if nxt:
            return "CORE_" + nxt
    core = CORRUPT_SPELL_NEXT.get("CORE_" + card_id)
    return core


def corrupt_active(card: Optional["Entity"]) -> bool:
    """手牌已腐蚀（CORRUPTED_CARD / 已升级 card_id / 腐蚀亮边）。"""
    if card is None:
        return False
    cid = card.card_id or ""
    if cid in CORRUPTED_SPELL_IDS:
        return True
    if cid.startswith("CORE_") and cid[5:] in CORRUPTED_SPELL_IDS:
        return True
    if int(card.tags.get("CORRUPTED_CARD", 0) or 0) > 0:
        return True
    if card.tags.get("POWERED_UP") == 1 and _resolve_corrupt_spell_id(cid):
        return True
    return False


def _corruptible_spell_cost(card: Optional["Entity"], defn: Optional[BoardSpellDef]) -> int:
    if card is not None:
        from .board_damage import hand_minion_cost

        c = hand_minion_cost(card)
        if c > 0:
            return c
    if defn is not None:
        return int(defn.base_cost or 0)
    return 0


def _apply_corrupt_to_card(card: "Entity") -> None:
    cid = card.card_id or ""
    next_cid = _resolve_corrupt_spell_id(cid)
    if next_cid:
        card.card_id = next_cid
    card.tags["CORRUPTED_CARD"] = 1


def trigger_corrupt_on_sequence_play(
    played_cost: int,
    seq: List[SpellPlayStep],
    next_idx: int,
    pending: List[SpellPlayStep],
    *,
    skip_entity_id: Optional[int] = None,
) -> None:
    """模拟本回合先打高费牌：序列内尚未打出的腐蚀牌升级。"""
    if played_cost <= 0:
        return
    pool: List[SpellPlayStep] = list(pending)
    pool.extend(seq[next_idx:])
    for defn, _cost, card in pool:
        if card is None:
            continue
        eid = getattr(card, "entity_id", None)
        if skip_entity_id is not None and eid == skip_entity_id:
            continue
        if corrupt_active(card):
            continue
        if _resolve_corrupt_spell_id(card.card_id or "") is None:
            continue
        if played_cost > _corruptible_spell_cost(card, defn):
            _apply_corrupt_to_card(card)


BONEBLADE_FLURRY_IDS = frozenset({"JAIL_445"})


def friendly_minion_died_this_turn(
    gs: Optional["GameState"],
    player_id: Optional[int],
) -> bool:
    """本回合是否已有友方随从死亡（骨刃乱舞等亮边条件）。"""
    if gs is None or player_id is None:
        return False
    for eid, pid in gs.player_ids.items():
        if pid != player_id:
            continue
        player = gs.get_entity(eid)
        if player is None:
            continue
        if int(player.tags.get("NUM_FRIENDLY_MINIONS_THAT_DIED_THIS_TURN", 0) or 0) > 0:
            return True
    return False


def hand_effect_active(
    card: Optional["Entity"],
    *,
    combo_active: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    next_turn_preview: bool = False,
    hero_damaged_this_turn: bool = False,
    friendly_minion_died_this_turn: bool = False,
) -> bool:
    """手牌亮边（POWERED_UP）或连击已触发（本回合已出牌 / 模拟序列内先出牌）。"""
    if card is None:
        return False
    if card.tags.get("POWERED_UP") == 1:
        return True
    cid = card.card_id or ""
    if friendly_minion_died_this_turn and cid in BONEBLADE_FLURRY_IDS:
        return True
    if hero_damaged_this_turn and cid in ("VAC_414", "CORE_VAC_414"):
        return True
    has_combo = bool(card.tags.get("COMBO"))
    if not has_combo:
        from .combo_board import get_combo_def

        has_combo = get_combo_def(card.card_id or "") is not None
    if not has_combo:
        return False
    if combo_active:
        return True
    if next_turn_preview:
        return False
    return player_combo_active(gs, player_id)


def player_combo_active(
    gs: Optional["GameState"],
    player_id: Optional[int],
    *,
    next_turn_preview: bool = False,
) -> bool:
    """本回合是否已打出过牌（盗贼连击等）。"""
    if next_turn_preview:
        return False
    if gs is None or player_id is None:
        return False
    for eid, pid in gs.player_ids.items():
        if pid != player_id:
            continue
        player = gs.get_entity(eid)
        if player is None:
            continue
        if int(player.tags.get("NUM_OPTIONS_PLAYED_THIS_TURN", 0) or 0) > 0:
            return True
        if int(player.tags.get("COMBO_ACTIVE", 0) or 0) > 0:
            return True
    return False


def quickdraw_active(card: Optional["Entity"]) -> bool:
    """快枪：本回合抽到可触发（与连击等同用 POWERED_UP 亮边）。"""
    return hand_effect_active(card)


def _face_estimate_script_damage(card: Optional["Entity"], default: int = 0) -> int:
    """直伤预估用脚本伤害；亮边时 TAG_SCRIPT_DATA_NUM_1 仍为基底值，须走 apply。"""
    if hand_effect_active(card):
        return 0
    return spell_script_damage(card, default=default)


@lru_cache(maxsize=1)
def _fire_spell_card_ids() -> frozenset[str]:
    path = resource_path("json", "cards.json")
    if not path.exists():
        return frozenset()
    data = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(
        c["id"] for c in data
        if c.get("type") == "SPELL" and c.get("spellSchool") == "FIRE"
    )


def _card_id_is_fire_spell(card_id: str) -> bool:
    if not card_id:
        return False
    ids = _fire_spell_card_ids()
    if card_id in ids:
        return True
    if card_id.startswith("CORE_"):
        return card_id[5:] in ids
    return ("CORE_" + card_id) in ids


def is_fire_spell(
    card: Optional["Entity"],
    defn: Optional[BoardSpellDef] = None,
) -> bool:
    """火系法术：实体 SPELL_SCHOOL=2 或 cards.json spellSchool=FIRE。"""
    if card is not None:
        tags = getattr(card, "tags", None) or {}
        if int(tags.get("SPELL_SCHOOL", 0) or 0) == 2:
            return True
        cid = getattr(card, "card_id", None) or ""
        if _card_id_is_fire_spell(cid):
            return True
    if defn is not None:
        for cid in defn.card_ids:
            if _card_id_is_fire_spell(cid):
                return True
    return False


def _step_counts_as_fire_spell_played(
    defn: BoardSpellDef,
    card: Optional["Entity"],
) -> bool:
    """本回合「打出火系法术」：仅手牌法术步，不含地标/战吼/随从。"""
    if get_board_spell_def(_step_card_id(defn, card)) is None:
        return False
    return is_fire_spell(card, defn)


# TAG_SCRIPT_DATA_NUM_1 对该 token 不是法术伤害（日志里常为其他脚本数据）
_SPELL_FIXED_SCRIPT_FACE: Dict[str, int] = {
    "TLC_630t": 2,  # 格里什毒刺虫
}


def _fixed_spell_script_face(card_id: str) -> Optional[int]:
    if not card_id:
        return None
    if card_id in _SPELL_FIXED_SCRIPT_FACE:
        return _SPELL_FIXED_SCRIPT_FACE[card_id]
    if card_id.startswith("CORE_"):
        return _SPELL_FIXED_SCRIPT_FACE.get(card_id[5:])
    return _SPELL_FIXED_SCRIPT_FACE.get("CORE_" + card_id)


def spell_script_damage(
    card: Optional["Entity"],
    default: int = 0,
    *,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """读取手牌脚本伤害 + 卡牌自带法伤（如星体平衡 CURRENT_SPELLPOWER_BASE）。"""
    if card is None:
        return default
    cid = card.card_id or ""
    mt = manathirst_spell_face_damage(cid, gs, player_id, card=card)
    if mt is not None:
        bonus = int(card.tags.get("CURRENT_SPELLPOWER_BASE", 0) or 0)
        return mt + bonus
    fixed = _fixed_spell_script_face(cid)
    if fixed is not None:
        bonus = int(card.tags.get("CURRENT_SPELLPOWER_BASE", 0) or 0)
        return fixed + bonus
    stored = getattr(card, "stored_damage", None)
    if stored is not None and int(stored) > 0:
        return int(stored)
    tags = getattr(card, "tags", None) or {}
    for key in ("TAG_SCRIPT_DATA_NUM_1", "STORED_DAMAGE"):
        tag = tags.get(key)
        if tag is not None and int(tag) > 0:
            return int(tag)
    bonus = int(tags.get("CURRENT_SPELLPOWER_BASE", 0) or 0)
    return default + bonus


def spell_estimate_trim_damage(
    card: Optional["Entity"],
    defn: BoardSpellDef,
    *,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """
    手牌法术裁剪时的预估直伤（无场面上下文）。
    优先脚本伤害；否则模拟一次 apply 的 direct_face_damage。
    """
    spell_power = total_spell_power(gs, player_id)
    dmg = _face_estimate_script_damage(card, default=0)
    if dmg > 0:
        return scaled_spell_damage(dmg, spell_power=spell_power)
    if defn.uses_random:
        return scaled_spell_damage(4, spell_power=spell_power)
    try:
        taunts = _sim_enemy_board_for_apply(gs, player_id)
        res = defn.apply(
            taunts, [], mult=1, enemy_shield=False,
            card=card, gs=gs, player_id=player_id,
            spell_power=spell_power,
        )
        return max(0, int(res.direct_face_damage))
    except Exception:
        return 0


def sequence_uses_random(sequence: List[SpellPlayStep]) -> bool:
    return any(defn.uses_random for defn, _, _ in sequence)


class SpellSimTier(IntEnum):
    """法术 combo 模拟出牌优先级（数值越小越先打）。"""
    CLEAR_BOARD = 0       # 清场：主要伤害落在随从，不含英雄
    CLEAR_AND_FACE = 1    # 清场+打脸：AOE/随机「所有敌人」等可同时打到脸
    DIRECT_FACE = 2       # 直伤：灵活单点（有怪打怪、空场打脸）或纯打脸
    UTILITY = 3           # 功能：buff/过牌/沉默等，不以直伤为主


SPELL_SIM_TIER_LABELS: Dict[SpellSimTier, str] = {
    SpellSimTier.CLEAR_BOARD: "清场",
    SpellSimTier.CLEAR_AND_FACE: "清场+打脸",
    SpellSimTier.DIRECT_FACE: "直伤",
    SpellSimTier.UTILITY: "功能",
}

# 启发式分类的显式覆盖（card_id -> tier）
_SPELL_SIM_TIER_OVERRIDES: Dict[str, SpellSimTier] = {
    # 用户指定：AOE 含英雄伤害仍按清场优先（combo 中先于直伤）
    "VAC_464t24": SpellSimTier.CLEAR_BOARD,   # 亡者之书
    "ONY_005tc2": SpellSimTier.CLEAR_BOARD,   # 亡者之书（奥特兰克宝藏）
    "PVPDR_SCH_Active54": SpellSimTier.CLEAR_BOARD,  # 亡者之书（对决）
    "ONY_005ta4": SpellSimTier.DIRECT_FACE,   # 极寒之击（奥特兰克宝藏）
    "DREAM_02": SpellSimTier.CLEAR_BOARD,     # 伊瑟拉苏醒
    "RLK_063": SpellSimTier.CLEAR_BOARD,      # 冰霜巨龙之怒
    "RLK_709": SpellSimTier.CLEAR_BOARD,      # 冷酷严冬
    "CORE_CS2_062": SpellSimTier.CLEAR_BOARD, # 地狱烈焰
    "LOOT_417": SpellSimTier.CLEAR_BOARD,     # 大灾变
    "CORE_CS2_093": SpellSimTier.CLEAR_BOARD, # 奉献
    "TTN_853": SpellSimTier.CLEAR_BOARD,      # 审判恶徒
    "EDR_476": SpellSimTier.CLEAR_BOARD,      # 月亮井
    "CORE_EDR_476": SpellSimTier.CLEAR_BOARD,
    "VAC_414": SpellSimTier.CLEAR_BOARD,      # 炽热火炭
    "TIME_619t2": SpellSimTier.CLEAR_BOARD,   # 赞达拉惨象
    "GDB_305": SpellSimTier.CLEAR_BOARD,      # 阳炎耀斑
    "CATA_489": SpellSimTier.CLEAR_AND_FACE,  # 奥术涌流（合体）
    "CATA_489t": SpellSimTier.DIRECT_FACE,    # 奥术涌流·碎裂单点
    "CATA_489t2": SpellSimTier.CLEAR_AND_FACE,  # 奥术涌流·碎裂AOE
    "EDR_461": SpellSimTier.UTILITY,            # 新月仪式
    "EDR_461t": SpellSimTier.UTILITY,           # 满月仪式
    "WW_027": SpellSimTier.UTILITY,             # 可靠陪伴 +2/+3
    "ETC_210": SpellSimTier.DIRECT_FACE,        # 通灵最强音（脚本伤害）
    "VAC_427": SpellSimTier.DIRECT_FACE,        # 甜筒殡淇淋 3 直伤
    "ETC_717": SpellSimTier.UTILITY,             # 悦耳嘻哈：直伤+武器加攻，须 combo 模拟
    "ETC_717t": SpellSimTier.UTILITY,            # 刺耳嘻哈：直伤+武器加攻，须 combo 模拟
    "TOY_642": SpellSimTier.CLEAR_BOARD,        # 球霸野猪人：最低血敌人，非纯打脸
    "SW_040": SpellSimTier.CLEAR_BOARD,         # 邪能弹幕：最低血敌人，可先打脸再弹幕
    "REV_290": SpellSimTier.UTILITY,            # 赎罪教堂 +2/+1
    "CORE_REV_290": SpellSimTier.UTILITY,
    "JAIL_445": SpellSimTier.DIRECT_FACE,       # 骨刃乱舞 3(+3) 随机敌人
    "END_014": SpellSimTier.UTILITY,            # 协作火花 3 伤 + 击杀 buff +3/+3
    "ETC_201": SpellSimTier.UTILITY,            # 一串香蕉 +1/+1 ×3
    "ETC_201t": SpellSimTier.UTILITY,
    "ETC_201t2": SpellSimTier.UTILITY,
    "ETC_082": SpellSimTier.UTILITY,            # 绝望哀歌：灵活解场+召唤，非纯打脸前缀
    "EDR_874": SpellSimTier.UTILITY,            # 星体平衡：生成月火+星火链，须完整 combo
}


def _infer_spell_sim_tier(defn: BoardSpellDef) -> SpellSimTier:
    """用 5×2/2 与空场各模拟一次，推断法术模拟分层。"""
    taunts = [
        {
            "health": 2, "shield": False, "lifesteal": False, "atk": 2,
            "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": i,
        }
        for i in range(1, 6)
    ]
    fighters: List[dict] = []
    board_t, board_f = deepcopy(taunts), deepcopy(fighters)
    tier_rng = random.Random(0)
    res_board = defn.apply(
        board_t, board_f, mult=1, enemy_shield=False, rng=tier_rng,
    )
    alive = sum(1 for t in board_t if t.get("health", 0) > 0)
    minion_hit = alive < len(taunts)
    face_board = int(res_board.direct_face_damage or 0)
    res_empty = defn.apply([], [], mult=1, enemy_shield=False, rng=tier_rng)
    face_empty = int(res_empty.direct_face_damage or 0)

    if not minion_hit and face_board == 0 and face_empty == 0:
        return SpellSimTier.UTILITY
    if face_board > 0 and minion_hit:
        return SpellSimTier.CLEAR_AND_FACE
    if minion_hit and face_board == 0 and face_empty > 0:
        return SpellSimTier.DIRECT_FACE
    if minion_hit and face_board == 0 and face_empty == 0:
        return SpellSimTier.CLEAR_BOARD
    if not minion_hit and (face_board > 0 or face_empty > 0):
        return SpellSimTier.DIRECT_FACE
    return SpellSimTier.DIRECT_FACE


@lru_cache(maxsize=512)
def spell_sim_tier_for_card(card_id: str) -> SpellSimTier:
    for cid, override in _SPELL_SIM_TIER_OVERRIDES.items():
        if cid == card_id:
            return override
    from .end_turn_hand_board import get_hand_end_turn_def

    if get_hand_end_turn_def(card_id) is not None:
        # 回合结束随从：打脸来自 end_turn 模拟，不走无嘲讽直伤前缀
        return SpellSimTier.UTILITY
    from .rush_board import get_rush_def

    rush_def = get_rush_def(card_id)
    if rush_def is not None:
        return _infer_spell_sim_tier(rush_def)
    from .location_board import get_location_def

    if get_location_def(card_id) is not None:
        return SpellSimTier.UTILITY
    from .weapon_board import get_weapon_def

    if get_weapon_def(card_id) is not None:
        # 武器打脸来自装备后的英雄攻击，不走无嘲讽直伤前缀
        return SpellSimTier.UTILITY
    from .combo_board import get_combo_def

    if get_combo_def(card_id) is not None:
        # 连击随从：常与 UTILITY 层法术（混乱打击等）同桶，以枚举先触发连击的顺序
        return SpellSimTier.UTILITY
    defn = BOARD_CLEAR_SPELLS.get(card_id)
    if defn is None:
        return SpellSimTier.DIRECT_FACE
    for cid in defn.card_ids:
        if cid in _SPELL_SIM_TIER_OVERRIDES:
            return _SPELL_SIM_TIER_OVERRIDES[cid]
    return _infer_spell_sim_tier(defn)


def spell_sim_tier(defn: BoardSpellDef) -> SpellSimTier:
    return spell_sim_tier_for_card(defn.card_ids[0])


def estimate_no_taunt_direct_face_damage(
    defn: BoardSpellDef,
    card: Optional["Entity"],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """无嘲讽时直伤法术按当前场面模拟的最大打脸（不参与 combo 枚举）。"""
    spell_power = total_spell_power(gs, player_id)
    dmg = _face_estimate_script_damage(card, default=0)
    if dmg > 0:
        return scaled_spell_damage(dmg, mult=spell_mult, spell_power=spell_power)
    try:
        taunts = _sim_enemy_board_for_apply(gs, player_id)
        res = defn.apply(
            taunts, [], mult=spell_mult, enemy_shield=enemy_shield,
            card=card, gs=gs, player_id=player_id,
            spell_power=spell_power,
        )
        return max(0, int(res.direct_face_damage or 0))
    except Exception:
        return 0


def partition_hand_spells_by_tier(
    hand_spells: List[Tuple["Entity", BoardSpellDef, int]],
) -> Tuple[List[Tuple["Entity", BoardSpellDef, int]], List[Tuple["Entity", BoardSpellDef, int]]]:
    """拆成 (combo 候选, 无嘲讽直伤固定打脸)。"""
    combo: List[Tuple["Entity", BoardSpellDef, int]] = []
    direct: List[Tuple["Entity", BoardSpellDef, int]] = []
    for item in hand_spells:
        card, defn, _cost = item
        if _is_battlecry_step(defn, card):
            combo.append(item)
            continue
        from .weapon_board import get_weapon_def

        if get_weapon_def(card.card_id or ""):
            combo.append(item)
            continue
        from .combo_board import get_combo_def

        if get_combo_def(card.card_id or ""):
            combo.append(item)
            continue
        if spell_sim_tier(defn) == SpellSimTier.DIRECT_FACE:
            direct.append(item)
        else:
            combo.append(item)
    return combo, direct


def pack_no_taunt_direct_face_spells(
    direct_spells: List[Tuple["Entity", BoardSpellDef, int]],
    available_mana: int,
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> Tuple[List[SpellPlayStep], int, int]:
    """
    无嘲讽：在法力内纳入直伤法术，按打脸伤害/费用贪心选取。
    返回 (固定前缀步骤, 累计打脸, 已耗法力)。
    """
    entries: List[Tuple[float, int, int, "Entity", BoardSpellDef]] = []
    for card, defn, cost in direct_spells:
        if cost > available_mana:
            continue
        dmg = estimate_no_taunt_direct_face_damage(
            defn, card, spell_mult=spell_mult, enemy_shield=enemy_shield,
            gs=gs, player_id=player_id,
        )
        if dmg <= 0:
            continue
        entries.append((dmg / max(cost, 1), dmg, cost, card, defn))
    entries.sort(key=lambda x: (-x[0], -x[1], x[2], x[3].entity_id if x[3] else 0))

    steps: List[SpellPlayStep] = []
    face = 0
    mana_used = 0
    for _, dmg, cost, card, defn in entries:
        if mana_used + cost > available_mana:
            continue
        steps.append((defn, cost, card))
        face += dmg
        mana_used += cost
    return steps, face, mana_used


def split_sequence_by_sim_tier(
    sequence: List[SpellPlayStep],
) -> Tuple[List[SpellPlayStep], List[SpellPlayStep], List[SpellPlayStep], List[SpellPlayStep]]:
    """按模拟优先级分桶：清场 / 清场+打脸 / 直伤 / 功能。"""
    buckets: List[List[SpellPlayStep]] = [[], [], [], []]
    for step in sequence:
        tier = int(spell_sim_tier(step[0]))
        buckets[tier].append(step)
    return buckets[0], buckets[1], buckets[2], buckets[3]


def sequence_random_spells_all_last(sequence: List[SpellPlayStep]) -> bool:
    """随机法术是否全部排在确定性法术之后（旧 MC 分批前提）。"""
    seen_random = False
    for defn, _, _ in sequence:
        if defn.uses_random:
            seen_random = True
        elif seen_random:
            return False
    return True


def split_deterministic_random_sequence(
    sequence: List[SpellPlayStep],
) -> Tuple[List[SpellPlayStep], List[SpellPlayStep]]:
    """拆成「确定性前缀 + 随机后缀」（随机法术固定放最后）。"""
    det: List[SpellPlayStep] = []
    rand: List[SpellPlayStep] = []
    for step in sequence:
        if step[0].uses_random:
            rand.append(step)
        else:
            det.append(step)
    return det, rand


def merge_spell_apply_results(*parts: SpellApplyResult) -> SpellApplyResult:
    total = SpellApplyResult()
    for part in parts:
        total.opponent_lifesteal_heal += part.opponent_lifesteal_heal
        total.direct_face_damage += part.direct_face_damage
        total.battlecry_face_damage += part.battlecry_face_damage
        total.self_hero_damage += part.self_hero_damage
        total.self_hero_heal += part.self_hero_heal
        total.drinks_after += part.drinks_after
        if part.add_hand_spell_id:
            total.add_hand_spell_id = part.add_hand_spell_id
            total.add_hand_spell_damage = part.add_hand_spell_damage
        total.add_hand_pending.extend(part.add_hand_pending)
    return total


def _permute_spell_steps(items: List[SpellPlayStep]) -> List[List[SpellPlayStep]]:
    if not items:
        return [[]]
    out: List[List[SpellPlayStep]] = []

    def permute(rest: List[SpellPlayStep], cur: List[SpellPlayStep]) -> None:
        if not rest:
            out.append(cur)
            return
        for i, item in enumerate(rest):
            permute(rest[:i] + rest[i + 1:], cur + [item])

    permute(items, [])
    return out


def _perm_entity_key(perm: List[SpellPlayStep]) -> tuple:
    return tuple(card.entity_id if card else 0 for _, _, card in perm)


def _unique_bucket_perms_by_outcome(
    bucket: List[SpellPlayStep],
    taunts: List[dict],
    fighters: List[dict],
    *,
    spell_mult: int,
    enemy_shield: bool,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    next_turn_preview: bool = False,
) -> List[List[SpellPlayStep]]:
    """
    同一优先级层内：若多种排列打出后场面终态相同，只保留一条代表序列。
    例：苏打清场后，火球/熔岩涌流/灼烧之风等直伤顺序可合并为 1 条。
    """
    if len(bucket) <= 1:
        return [bucket] if bucket else [[]]

    reps: Dict[tuple, List[SpellPlayStep]] = {}
    for perm in _permute_spell_steps(bucket):
        t2 = deepcopy(taunts)
        f2 = deepcopy(fighters)
        res = apply_spell_sequence(
            t2, f2, perm, spell_mult=spell_mult, enemy_shield=enemy_shield,
            gs=gs, player_id=player_id,
            next_turn_preview=next_turn_preview,
        )
        fp = spell_sequence_transposition_key(
            t2, f2, res, hero_hp=None, mana_left=None,
        )
        prev = reps.get(fp)
        if prev is None or _perm_entity_key(perm) < _perm_entity_key(prev):
            reps[fp] = perm
    return list(reps.values())


def enumerate_pruned_tiered_spell_orders(
    items: List[SpellPlayStep],
    taunts: List[dict],
    fighters: List[dict],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    next_turn_preview: bool = False,
) -> List[List[SpellPlayStep]]:
    """
    分层枚举 + 场面置换剪枝：每层内合并终态等价的排列；
    层与层之间按 清场 -> 清场+打脸 -> 直伤 -> 功能 顺序连接。
    """
    return _enumerate_pruned_tiered_dfs(
        items, taunts, fighters,
        spell_mult=spell_mult, enemy_shield=enemy_shield,
        gs=gs, player_id=player_id,
        next_turn_preview=next_turn_preview,
    )


def _enumerate_pruned_tiered_dfs(
    items: List[SpellPlayStep],
    taunts: List[dict],
    fighters: List[dict],
    *,
    spell_mult: int,
    enemy_shield: bool,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    next_turn_preview: bool = False,
) -> List[List[SpellPlayStep]]:
    buckets = list(split_sequence_by_sim_tier(items))
    out: List[List[SpellPlayStep]] = []
    seen_seq: set = set()

    def dfs(prefix: List[SpellPlayStep], bucket_idx: int, t: List[dict], f: List[dict]) -> None:
        if bucket_idx >= len(buckets):
            key = tuple((d, c, card.entity_id if card else None) for d, c, card in prefix)
            if key not in seen_seq:
                seen_seq.add(key)
                out.append(prefix)
            return
        bucket = buckets[bucket_idx]
        if not bucket:
            dfs(prefix, bucket_idx + 1, t, f)
            return
        for perm in _unique_bucket_perms_by_outcome(
            bucket, t, f,
            spell_mult=spell_mult, enemy_shield=enemy_shield,
            gs=gs, player_id=player_id,
            next_turn_preview=next_turn_preview,
        ):
            t2 = deepcopy(t)
            f2 = deepcopy(f)
            apply_spell_sequence(
                t2, f2, perm, spell_mult=spell_mult, enemy_shield=enemy_shield,
                gs=gs, player_id=player_id,
                next_turn_preview=next_turn_preview,
            )
            dfs(prefix + perm, bucket_idx + 1, t2, f2)

    dfs([], 0, taunts, fighters)
    return out


def enumerate_tiered_spell_orders(
    items: List[SpellPlayStep],
) -> List[List[SpellPlayStep]]:
    """
    按模拟优先级分层全排列：清场 -> 清场+打脸 -> 直伤 -> 功能。
    无场面上下文时不做置换剪枝（层内全排列）。
    """
    clear_b, clear_face, direct, utility = split_sequence_by_sim_tier(items)
    orders: List[List[SpellPlayStep]] = [[]]
    for bucket in (clear_b, clear_face, direct, utility):
        if not bucket:
            continue
        next_orders: List[List[SpellPlayStep]] = []
        for base in orders:
            for perm in _permute_spell_steps(bucket):
                next_orders.append(base + perm)
        orders = next_orders
    return orders


def enumerate_random_last_spell_orders(
    items: List[SpellPlayStep],
) -> List[List[SpellPlayStep]]:
    """兼容旧名：已改为按清场/直伤分层枚举。"""
    return enumerate_tiered_spell_orders(items)


def _apply_aoe_all_minions(taunts: List[dict], fighters: List[dict], damage: int) -> int:
    """对所有随从造成固定伤害（含己方），如麦迪文的胜利。"""
    heal = 0
    for t in list(taunts):
        heal += _apply_damage(t, damage, taunts=taunts, fighters=fighters)
    _remove_dead_taunts(taunts)
    for f in fighters:
        if f.get("kind") == "minion":
            heal += _apply_damage(f, damage, taunts=taunts, fighters=fighters)
    return heal


def _apply_moonwell(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """
    月亮井：对全体敌人造成 4 点（含英雄），全体友方恢复 4 点。
    仅模拟 taunts + fighters；直伤走 direct_face_damage。
    """
    dmg = 4 * mult
    heal = 4 * mult
    opp_heal = 0
    for t in list(taunts):
        opp_heal += _apply_damage(t, dmg, taunts=taunts, fighters=fighters)
    _remove_dead_taunts(taunts)
    for f in fighters:
        _heal_unit(f, heal)
    face_hits = apply_divine_shield_to_hits([dmg], enemy_shield)
    return SpellApplyResult(opponent_lifesteal_heal=opp_heal, direct_face_damage=face_hits)


def _apply_medivh_triumph(taunts: List[dict], fighters: List[dict], *, mult: int, **_kw) -> SpellApplyResult:
    heal = _apply_aoe_all_minions(taunts, fighters, 4 * mult)
    return SpellApplyResult(opponent_lifesteal_heal=heal)


def _cata_308_cost(gs: "GameState", player_id: int) -> int:
    for m in gs.get_board(player_id):
        rarity = m.tags.get("RARITY")
        if rarity in ("LEGENDARY", 5):
            return 1
    return 5


BOARD_CLEAR_SPELLS: Dict[str, BoardSpellDef] = {}


def _register(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_CLEAR_SPELLS[cid] = defn


_register(BoardSpellDef(
    card_ids=("EDR_476", "CORE_EDR_476"),
    base_cost=6,
    name="月亮井",
    apply=_apply_moonwell,
))

_register(BoardSpellDef(
    card_ids=("CATA_308",),
    base_cost=5,
    name="麦迪文的胜利",
    apply=_apply_medivh_triumph,
    cost_fn=_cata_308_cost,
))

# P0 直伤法术（21 张）
from . import spell_p0_direct  # noqa: E402, F401
# P0 解场伤法术（33 张）
from . import spell_p0_minion  # noqa: E402, F401
# P0 移除法术（消灭等）
from . import spell_p0_remove  # noqa: E402, F401
# P0 复杂 AOE（33 张）
from . import spell_p0_aoe  # noqa: E402, F401
# 伊瑟拉梦境池法术（梦境 / 伊瑟拉苏醒 / 梦魇）
from . import spell_p0_dream  # noqa: E402, F401
# P0 加攻 / 武器（6 张）
from . import spell_p0_buff  # noqa: E402, F401
# P0 其他法术（14 张）
from . import spell_p0_other  # noqa: E402, F401
from . import spell_p0_concoction  # noqa: E402, F401
# P1 法术
from . import spell_p1_direct  # noqa: E402, F401
from . import spell_p1_minion  # noqa: E402, F401
from . import spell_p1_aoe  # noqa: E402, F401
from . import spell_p1_buff  # noqa: E402, F401
from . import spell_p1_other  # noqa: E402, F401
# P2 法术
from . import spell_p2_direct  # noqa: E402, F401
# 尤朵拉神奇战利品（场攻子集）
from . import eudora_loot  # noqa: E402, F401


def get_board_spell_def(card_id: str) -> Optional[BoardSpellDef]:
    if card_id in BOARD_CLEAR_SPELLS:
        return BOARD_CLEAR_SPELLS[card_id]
    if card_id.startswith("CORE_"):
        return BOARD_CLEAR_SPELLS.get(card_id[5:])
    return BOARD_CLEAR_SPELLS.get("CORE_" + card_id)


WICKED_STAB_IDS = frozenset({
    "BAR_319", "BAR_319t", "BAR_319t2", "BAR_920", "BAR_921",
})
CONDEMN_IDS = frozenset({"BAR_314", "BAR_915", "BAR_916"})

# 饮品法术（夜影花茶 / “健康”饮品等）：card_id -> 打出前剩余杯数
DRINKS_LEFT = {
    "VAC_404": 3,
    "VAC_404t1": 2,
    "VAC_404t2": 1,
    "VAC_951": 3,
    "VAC_951t": 2,
    "VAC_951t2": 1,
    "VAC_323": 3,
    "VAC_323t": 2,
    "VAC_323t1": 2,
    "VAC_323t2": 1,
    "ETC_201": 3,
    "ETC_201t": 2,
    "ETC_201t2": 1,
}
DRINK_NEXT = {
    "VAC_404": "VAC_404t1",
    "VAC_404t1": "VAC_404t2",
    "VAC_951": "VAC_951t",
    "VAC_951t": "VAC_951t2",
    "VAC_323": "VAC_323t",
    "VAC_323t": "VAC_323t2",
    "VAC_323t1": "VAC_323t2",
    "ETC_201": "ETC_201t",
    "ETC_201t": "ETC_201t2",
}
# 饮品各杯实际费用（首杯/回手衍生牌可能不同；未列出的沿用当步 cost）
DRINK_SPELL_COST: Dict[str, int] = {
    "VAC_323": 1,
    "VAC_323t": 2,
    "VAC_323t1": 2,
    "VAC_323t2": 2,
}
DRINK_SPELL_IDS = frozenset(DRINKS_LEFT)

# 兼容旧名
NIGHTSHADE_DRINKS = DRINKS_LEFT
NIGHTSHADE_NEXT = DRINK_NEXT


def drink_play_cost(card_id: str, fallback: int = 0) -> int:
    """饮品法术单杯费用（连喝时每杯独立计费）。"""
    if card_id in DRINK_SPELL_COST:
        return DRINK_SPELL_COST[card_id]
    defn = get_board_spell_def(card_id)
    if defn is not None:
        return int(defn.base_cost or fallback)
    return fallback


def _mana_for_drink_step(card_id: str, cost: int, mana_left: Optional[int]) -> Tuple[int, Optional[int]]:
    """单张法术步骤消耗（含饮品连喝），返回 (本步花费, 剩余法力)。"""
    play_cost = drink_play_cost(card_id, cost)
    if mana_left is not None and play_cost > mana_left:
        return 0, mana_left
    spent = play_cost
    if mana_left is not None:
        mana_left -= play_cost
    cid = card_id or ""
    while DRINKS_LEFT.get(cid, 0) > 0:
        if DRINKS_LEFT.get(cid, 0) - 1 <= 0:
            break
        next_cid = DRINK_NEXT.get(cid)
        if not next_cid:
            break
        next_cost = drink_play_cost(next_cid, cost)
        if mana_left is not None and next_cost > mana_left:
            break
        spent += next_cost
        if mana_left is not None:
            mana_left -= next_cost
        cid = next_cid
    return spent, mana_left


def spell_sequence_mana_left(
    sequence: List["SpellPlayStep"],
    mana_budget: Optional[int],
) -> Optional[int]:
    """估算法术序列实际消耗后的剩余法力（饮品连喝每杯另付费用）。"""
    if mana_budget is None:
        return None
    mana_left = mana_budget
    for defn, cost, card in sequence:
        cid = _spell_card_id(card) or (defn.card_ids[0] if defn.card_ids else "")
        step_spent, mana_left = _mana_for_drink_step(cid, cost, mana_left)
        if step_spent <= 0 and cost > 0:
            continue
    return mana_left

# 初始之火 → 传承之火（HJSON：衍生牌 id 为 SW_108t，Core/原版均共用）
FLAME_CHAIN_NEXT = {
    "CORE_SW_108": "SW_108t",
    "SW_108": "SW_108t",
}
FLAME_CHAIN_IDS = frozenset(FLAME_CHAIN_NEXT) | frozenset(FLAME_CHAIN_NEXT.values())


class _SyntheticSpellCard:
    """模拟衍生/回手法术，仅用于读取 card_id / cost / 动态伤害。"""

    def __init__(self, card_id: str, cost: int = 1, stored_damage: int = 0):
        self.card_id = card_id
        self.cost = cost
        self.stored_damage = stored_damage
        self.tags: dict = {}


def _spell_card_id(card) -> str:
    if card is None:
        return ""
    return card.card_id or ""


def _step_card_id(defn: BoardSpellDef, card: Optional["Entity"]) -> str:
    cid = _spell_card_id(card)
    if cid:
        return cid
    return defn.card_ids[0] if defn.card_ids else ""


def sequence_damages_friendly_minions(sequence) -> bool:
    """序列中是否含全场 AOE（含己方随从）。"""
    for defn, _, card in sequence or []:
        if _step_card_id(defn, card) in SPELLS_DAMAGE_ALL_MINIONS:
            return True
    return False


def _is_battlecry_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    from .battlecry_board import BOARD_BATTLECRY

    return _step_card_id(defn, card) in BOARD_BATTLECRY


def _is_hostile_invader_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    from .battlecry_board import HOSTILE_INVADER_IDS

    return _step_card_id(defn, card) in HOSTILE_INVADER_IDS


MANASABER_IDS = frozenset({"GDB_322"})
DEVOURER_IDS = frozenset({"GDB_855"})
TYRANDE_IDS = frozenset({"EDR_464"})


def _entity_spellburst_ready(entity: "Entity") -> bool:
    return (
        entity.is_minion
        and entity.current_health > 0
        and int(entity.tags.get("SPELLBURST", 0) or 0) == 1
    )


def _board_spellburst_pending_counts(
    gs: Optional["GameState"],
    player_id: Optional[int],
) -> tuple[int, int, int]:
    """场上未触发的法术迸发：入侵者 / 魔刃豹 / 吞星兽。"""
    if gs is None or player_id is None:
        return 0, 0, 0
    from .battlecry_board import HOSTILE_INVADER_IDS

    hostile = manasaber = devourer = 0
    for entity in gs.get_board(player_id):
        if not _entity_spellburst_ready(entity):
            continue
        cid = entity.card_id or ""
        if cid in HOSTILE_INVADER_IDS:
            hostile += 1
        elif cid in MANASABER_IDS:
            manasaber += 1
        elif cid in DEVOURER_IDS:
            devourer += 1
    return hostile, manasaber, devourer


def _is_rush_minion_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    from .rush_board import BOARD_RUSH

    return _step_card_id(defn, card) in BOARD_RUSH


def _is_manasaber_rush_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    return _step_card_id(defn, card) in MANASABER_IDS


def _is_devourer_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    return _step_card_id(defn, card) in DEVOURER_IDS


def _is_tyrande_step(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    return _step_card_id(defn, card) in TYRANDE_IDS


def _is_tyrande_double_eligible_spell(defn: BoardSpellDef, card: Optional["Entity"]) -> bool:
    """泰兰德光环：仅手牌法术（非战吼/突袭/武器等）触发双倍施放。"""
    if _is_battlecry_step(defn, card):
        return False
    if _is_rush_minion_step(defn, card):
        return False
    return get_board_spell_def(_step_card_id(defn, card)) is not None


def _apply_devourer_spellburst(fighters: List[dict], *, mult: int = 1) -> SpellApplyResult:
    """吞星兽法术迸发：英雄 +8 攻（+8 甲 v1 不计）。"""
    _add_temp_hero_attack(fighters, 8 * mult)
    return SpellApplyResult()


def _apply_manasaber_spellburst(fighters: List[dict]) -> SpellApplyResult:
    """光注魔刃豹法术迸发：场上魔刃豹获得圣盾。"""
    for f in reversed(fighters):
        if f.get("card_id") == "GDB_322" and f.get("health", 0) > 0:
            f["shield"] = True
            break
    return SpellApplyResult()


def _apply_hostile_invader_spellburst(
    taunts: List[dict],
    fighters: List[dict],
    *,
    spell_mult: int,
) -> SpellApplyResult:
    """凶恶的入侵者法术迸发：再对所有其他随从造成 2 点伤害。"""
    return _apply_all_minions_aoe_spell(taunts, fighters, 2 * spell_mult)


def _merge_spell_result(total: SpellApplyResult, res: SpellApplyResult) -> None:
    res = _coerce_spell_apply_result(res)
    total.opponent_lifesteal_heal += res.opponent_lifesteal_heal
    total.direct_face_damage += res.direct_face_damage
    total.battlecry_face_damage += res.battlecry_face_damage
    total.self_hero_damage += res.self_hero_damage
    total.self_hero_heal += res.self_hero_heal
    # drinks_after / add_hand_spell_id 由 apply_spell_sequence 消费，不累计到 total


def _coerce_spell_apply_result(res: object) -> SpellApplyResult:
    """部分 destroy 辅助函数返回被消灭随从 dict；统一转为 SpellApplyResult。"""
    if isinstance(res, SpellApplyResult):
        return res
    if res is None:
        return SpellApplyResult()
    return SpellApplyResult()


def _merge_step_result(
    total: SpellApplyResult,
    res: SpellApplyResult,
    defn: BoardSpellDef,
    card: Optional["Entity"],
) -> None:
    """合并单步打出结果；战吼打脸计入 battlecry_face_damage，其余计入 direct_face_damage。"""
    res = _coerce_spell_apply_result(res)
    total.opponent_lifesteal_heal += res.opponent_lifesteal_heal
    total.self_hero_damage += res.self_hero_damage
    total.self_hero_heal += res.self_hero_heal
    face = res.direct_face_damage
    if _is_battlecry_step(defn, card):
        total.battlecry_face_damage += face
    else:
        total.direct_face_damage += face


def wicked_stab_card_id_for_max_mana(max_mana: int) -> str:
    """Ranked spell：5 水晶→4伤，10 水晶→6伤（均为 2 费）。"""
    if max_mana >= 10:
        return "BAR_921"
    if max_mana >= 5:
        return "BAR_920"
    return "BAR_319"


def condemn_card_id_for_max_mana(max_mana: int) -> str:
    """罪罚：5 水晶→2 伤，10 水晶→3 伤。"""
    if max_mana >= 10:
        return "BAR_916"
    if max_mana >= 5:
        return "BAR_915"
    return "BAR_314"


def _estimate_max_mana_from_turn(gs: "GameState", player_id: int) -> int:
    game = gs.entities.get(gs.game_entity_id) if gs.game_entity_id else None
    if not game:
        return 0
    turn = game.tags.get("TURN", 0)
    if turn <= 0:
        return 0
    first = gs.first_player_id
    if first is None:
        return min(10, (turn + 1) // 2)
    if player_id == first:
        return min(10, (turn + 1) // 2)
    return min(10, turn // 2)


def max_mana_crystals_for_spells(gs: "GameState", player_id: int) -> int:
    """
    邪恶挥刺等按「法力水晶上限」升级。对方回合时取下一回合水晶数（与 Overlay 一致）。
    """
    from .board_damage import is_players_turn

    hero = gs.get_hero(player_id)
    cur = 0
    if hero:
        cur = int(hero.tags.get("MAXRESOURCES", 0) or hero.tags.get("RESOURCES", 0))
    if cur <= 0:
        cur = _estimate_max_mana_from_turn(gs, player_id)
    cur = min(10, cur)
    if not is_players_turn(gs, player_id):
        return min(10, cur + 1)
    return cur


# 法力渴求直伤法术：(阈值水晶数, 基础伤, 升级伤)
MANATHIRST_SPELL_DAMAGE: Dict[str, Tuple[int, int, int]] = {
    "RLK_843": (8, 2, 3),  # 奥术箭
}


def manathirst_spell_upgraded(
    card_id: str,
    gs: Optional["GameState"],
    player_id: Optional[int],
    *,
    card: Optional["Entity"] = None,
) -> bool:
    """法力渴求是否已满足（优先读手牌亮边，否则按当前/下回合水晶上限）。"""
    spec = MANATHIRST_SPELL_DAMAGE.get(card_id or "")
    if spec is None:
        return False
    threshold, _, _ = spec
    if card is not None and card.tags.get("POWERED_UP") == 1:
        if not card.tags.get("COMBO"):
            from .combo_board import get_combo_def
            if get_combo_def(card.card_id or "") is None:
                return True
    if gs is None or player_id is None:
        return False
    return max_mana_crystals_for_spells(gs, player_id) >= threshold


def manathirst_spell_face_damage(
    card_id: str,
    gs: Optional["GameState"],
    player_id: Optional[int],
    *,
    card: Optional["Entity"] = None,
) -> Optional[int]:
    """法力渴求法术的脚本打脸伤害；非登记卡返回 None。"""
    spec = MANATHIRST_SPELL_DAMAGE.get(card_id or "")
    if spec is None:
        return None
    _, base, upgraded = spec
    return upgraded if manathirst_spell_upgraded(
        card_id, gs, player_id, card=card,
    ) else base


def resolve_board_spell_def(
    card: "Entity", gs: "GameState", player_id: int,
) -> Optional[BoardSpellDef]:
    cid = card.card_id or ""
    if cid in DRINK_SPELL_IDS or cid in FLAME_CHAIN_IDS:
        defn = get_board_spell_def(cid)
        if defn:
            return defn
    if cid in CONDEMN_IDS:
        if cid in ("BAR_915", "BAR_916"):
            return get_board_spell_def(cid)
        max_m = max_mana_crystals_for_spells(gs, player_id)
        return get_board_spell_def(condemn_card_id_for_max_mana(max_m))
    if cid not in WICKED_STAB_IDS:
        return get_board_spell_def(cid)
    if cid in ("BAR_920", "BAR_921", "BAR_319t", "BAR_319t2"):
        return get_board_spell_def(cid)
    max_m = max_mana_crystals_for_spells(gs, player_id)
    return get_board_spell_def(wicked_stab_card_id_for_max_mana(max_m))


VENDETTA_IDS = frozenset({"DAL_716"})


def _board_spell_base_cost(defn: BoardSpellDef, gs: "GameState", player_id: int) -> int:
    if defn.cost_fn:
        return defn.cost_fn(gs, player_id)
    return defn.base_cost


def _prepared_hand_cost(card: "Entity", base_cost: int) -> Optional[int]:
    """预备（Prepare）：PREPARED 为已投入的预备法力，实际打出费 = base - PREPARED。"""
    raw = card.tags.get("PREPARED")
    if raw is None:
        return None
    try:
        prepared = int(raw)
    except (TypeError, ValueError):
        return None
    if prepared <= 0:
        return None
    return max(0, base_cost - prepared)


def spell_effective_cost(card: "Entity", gs: "GameState", player_id: int) -> int:
    defn = resolve_board_spell_def(card, gs, player_id)
    if not defn:
        return 999
    base_cost = _board_spell_base_cost(defn, gs, player_id)
    # 手牌减费以 tags[COST] 为准（预备后日志会写 COST=0/1/3 等；偶发未同步时用 PREPARED 回退）
    tag_cost: Optional[int] = None
    raw_tag = card.tags.get("COST")
    if raw_tag is not None:
        try:
            tc = int(raw_tag)
            if tc >= 0:
                tag_cost = tc
        except (TypeError, ValueError):
            pass
    prep_cost = _prepared_hand_cost(card, base_cost)
    if prep_cost is not None:
        if tag_cost is None:
            return prep_cost
        if tag_cost >= base_cost and prep_cost < base_cost:
            return prep_cost
        return tag_cost
    if tag_cost is not None:
        return tag_cost
    cid = card.card_id or ""
    if cid in VENDETTA_IDS and hand_effect_active(card):
        return 0
    if card.cost is not None and card.cost > 0:
        return int(card.cost)
    return base_cost


def hand_board_spells(
    gs: "GameState", player_id: int, available_mana: int
) -> List[Tuple["Entity", BoardSpellDef, int]]:
    from .arcane_flow import (
        ArcaneFlowVirtualCombined,
        arcane_flow_hand_playable,
        find_shattered_arcane_flow_pair,
    )

    result: List[Tuple[Entity, BoardSpellDef, int]] = []
    pair = find_shattered_arcane_flow_pair(gs, player_id)
    paired_eids: Set[int] = set()
    if pair is not None:
        paired_eids = {pair[0].entity_id, pair[1].entity_id}

    for card in gs.get_hand(player_id):
        eid = getattr(card, "entity_id", None)
        if eid is not None and eid in paired_eids:
            continue
        if not arcane_flow_hand_playable(card):
            continue
        defn = resolve_board_spell_def(card, gs, player_id)
        if not defn:
            continue
        cost = spell_effective_cost(card, gs, player_id)
        if cost <= available_mana:
            if any(c in SPELL_REQUIRES_ENEMY_MINION for c in defn.card_ids):
                if not enemy_board_has_targetable_minion(gs, player_id):
                    continue
            if any(c in SPELL_REQUIRES_FRIENDLY_MINION for c in defn.card_ids):
                if not friendly_board_has_spell_target_minion(gs, player_id):
                    continue
            result.append((card, defn, cost))

    if pair is not None:
        defn = get_board_spell_def("CATA_489")
        if defn and defn.base_cost <= available_mana:
            virtual = ArcaneFlowVirtualCombined(pair[0], pair[1])
            result.append((virtual, defn, defn.base_cost))

    return result


def _living_minion_key(m: dict) -> Optional[tuple]:
    if m.get("health", 0) <= 0:
        return None
    return (
        m.get("entity_id"),
        m.get("health", 0),
        m.get("atk", 0),
        m.get("shield", False),
        m.get("taunt", False),
        m.get("poisonous", False),
        m.get("spell_immune", False),
        m.get("zone_pos", 0),
    )


def _living_fighter_key(f: dict) -> Optional[tuple]:
    if f.get("health", 0) <= 0:
        return None
    return (
        f.get("kind"),
        f.get("entity_id"),
        f.get("atk", 0),
        f.get("health", 0),
        f.get("shield", False),
        f.get("attacks_left", 0),
        f.get("durability", 0),
        f.get("can_face", True),
        f.get("poisonous", False),
    )


def spell_sequence_transposition_key(
    enemy: List[dict],
    fighters: List[dict],
    spell_acc: SpellApplyResult,
    *,
    hero_hp: Optional[int],
    mana_left: Optional[int],
) -> tuple:
    """法术阶段终态指纹：场面 + 累计直伤/吸血/自伤 + 剩余法力。"""
    em = tuple(sorted(
        (k for m in enemy if (k := _living_minion_key(m)) is not None),
        key=lambda x: (x[0] or 0, x[7]),
    ))
    ff = tuple(sorted(
        (k for f in fighters if (k := _living_fighter_key(f)) is not None),
        key=lambda x: (x[0], x[1] or 0),
    ))
    return (
        em,
        ff,
        spell_acc.direct_face_damage,
        spell_acc.opponent_lifesteal_heal,
        spell_acc.self_hero_heal,
        spell_acc.self_hero_damage,
        hero_hp,
        mana_left,
    )


def enumerate_spell_sequences(
    spells: List[Tuple["Entity", BoardSpellDef, int]],
    *,
    max_combo_len: Optional[int] = MAX_SPELL_COMBO_LEN,
    mana_budget: Optional[int] = None,
    max_sequences: Optional[int] = MAX_SPELL_SEQUENCES,
    enemy_minions: Optional[List[dict]] = None,
    fighters: Optional[List[dict]] = None,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    next_turn_preview: bool = False,
) -> List[List[SpellPlayStep]]:
    """
    枚举手牌解场法术的可行打出顺序（含子集：可只打其中几张，如两张月亮井）。
    每张手牌实体最多使用一次；保留 Entity 以读取 POWERED_UP 亮边。
    max_combo_len：单条 combo 最多几张（默认 MAX_SPELL_COMBO_LEN=6；None=不限制）。
    mana_budget 剪枝总费用；max_sequences 为 None 时不提前截断。
    提供 enemy_minions/fighters 时：按分层 + 场面终态置换剪枝（同终态只留一条序列）。
    """
    if not spells:
        return [[]]

    n = len(spells)
    sequences: List[List[SpellPlayStep]] = [[]]
    seen: set = set()
    limit = None if max_sequences is None else max(1, max_sequences)
    use_board_prune = enemy_minions is not None and fighters is not None

    def add_seq(seq: List[SpellPlayStep]) -> bool:
        key = tuple((d, c, card.entity_id if card else None) for d, c, card in seq)
        if key in seen:
            return limit is None or len(sequences) < limit
        seen.add(key)
        sequences.append(seq)
        return limit is None or len(sequences) < limit

    for mask in range(1, 1 << n):
        if max_combo_len is not None and bin(mask).count("1") > max_combo_len:
            continue
        items = [
            (spells[i][1], spells[i][2], spells[i][0])
            for i in range(n) if mask & (1 << i)
        ]
        if not items:
            continue
        if mana_budget is not None and sum(c for _, c, _ in items) > mana_budget:
            continue

        if use_board_prune:
            order_list = enumerate_pruned_tiered_spell_orders(
                items, deepcopy(enemy_minions), deepcopy(fighters),
                spell_mult=spell_mult, enemy_shield=enemy_shield,
                gs=gs, player_id=player_id,
                next_turn_preview=next_turn_preview,
            )
        else:
            order_list = enumerate_tiered_spell_orders(items)

        for order in order_list:
            if mana_budget is not None and sum(c for _, c, _ in order) > mana_budget:
                continue
            if not add_seq(order):
                break

    return sequences


def apply_spell_sequence(
    taunts: List[dict],
    fighters: List[dict],
    sequence: List[SpellPlayStep],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    rng: Optional[random.Random] = None,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    hero_hp: Optional[int] = None,
    opponent_hero_hp: Optional[int] = None,
    mana_budget: Optional[int] = None,
    next_turn_preview: bool = False,
) -> SpellApplyResult:
    """
    按顺序施放法术序列；支持夜影花茶回手连喝、初始之火链式衍生。
    hero_hp：我方有效生命（血+甲）；吸血先回血再扣自伤，自伤后须 >0 才能继续。
    opponent_hero_hp：模拟中对手英雄已压低后的有效生命（先攻后法等）。
    mana_budget：本回合可用法力；None 时不限制。
    """
    total, _, _ = _apply_spell_sequence_impl(
        taunts, fighters, sequence,
        spell_mult=spell_mult, enemy_shield=enemy_shield, rng=rng,
        gs=gs, player_id=player_id, hero_hp=hero_hp,
        opponent_hero_hp=opponent_hero_hp,
        mana_budget=mana_budget,
        next_turn_preview=next_turn_preview,
    )
    return total


def apply_spell_sequence_with_meta(
    taunts: List[dict],
    fighters: List[dict],
    sequence: List[SpellPlayStep],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    rng: Optional[random.Random] = None,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    hero_hp: Optional[int] = None,
    opponent_hero_hp: Optional[int] = None,
    mana_budget: Optional[int] = None,
    next_turn_preview: bool = False,
    inline_hero_power_used: bool = False,
) -> Tuple[SpellApplyResult, Optional[int], Optional[int]]:
    """apply_spell_sequence 并返回 (结果, 我方剩余有效生命, 剩余法力)。"""
    return _apply_spell_sequence_impl(
        taunts, fighters, sequence,
        spell_mult=spell_mult, enemy_shield=enemy_shield, rng=rng,
        gs=gs, player_id=player_id, hero_hp=hero_hp,
        opponent_hero_hp=opponent_hero_hp,
        mana_budget=mana_budget,
        next_turn_preview=next_turn_preview,
        inline_hero_power_used=inline_hero_power_used,
    )


def _apply_spell_sequence_impl(
    taunts: List[dict],
    fighters: List[dict],
    sequence: List[SpellPlayStep],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    rng: Optional[random.Random] = None,
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    hero_hp: Optional[int] = None,
    opponent_hero_hp: Optional[int] = None,
    mana_budget: Optional[int] = None,
    next_turn_preview: bool = False,
    inline_hero_power_used: bool = False,
) -> Tuple[SpellApplyResult, Optional[int], Optional[int]]:
    total = SpellApplyResult()
    roll = rng if rng is not None else random.Random(0)
    hp = hero_hp
    mana_left = mana_budget
    pending: List[SpellPlayStep] = []
    idx = 0
    seq = list(sequence)
    (
        hostile_spellburst_pending,
        manasaber_spellburst_pending,
        devourer_spellburst_pending,
    ) = _board_spellburst_pending_counts(gs, player_id)
    from .battlecry_board import tyrande_double_spells_remaining
    from .arcane_flow import (
        trigger_arcane_flow_recombine_on_play,
        trigger_arcane_flow_shatter_on_play,
    )
    tyrande_double_remaining = tyrande_double_spells_remaining(gs, player_id)
    shattered_arcane_flow_entities: set = set()
    fire_spell_played_this_turn = False
    from .damaged_spell_power import sim_spell_power, try_inline_mage_fireblast_setup
    spell_power = sim_spell_power(gs, player_id, fighters)
    hp_used_inline = inline_hero_power_used
    combo_active = (
        False if next_turn_preview
        else player_combo_active(gs, player_id)
    )
    hero_damaged_this_turn = False
    friendly_minion_died = friendly_minion_died_this_turn(gs, player_id)
    if gs is not None and player_id is not None:
        for hc in gs.get_hand(player_id):
            if (hc.card_id or "") in ("VAC_414", "CORE_VAC_414") and hc.tags.get("POWERED_UP") == 1:
                hero_damaged_this_turn = True
                break

    while idx < len(seq) or pending:
        if pending:
            defn, cost, card = pending.pop(0)
        else:
            defn, cost, card = seq[idx]
            idx += 1

        played_eid = getattr(card, "entity_id", None) if card else None
        if played_eid is not None and played_eid in shattered_arcane_flow_entities:
            continue

        if mana_left is not None and cost > mana_left:
            continue

        is_last_in_sequence = not pending and idx == len(seq)
        finale_active = (
            mana_left is not None
            and cost == mana_left
            and is_last_in_sequence
        )

        tyrande_eligible = (
            tyrande_double_remaining > 0
            and _is_tyrande_double_eligible_spell(defn, card)
        )
        spell_cast_copies = 2 if tyrande_eligible else 1
        if tyrande_eligible:
            tyrande_double_remaining -= 1

        mana_paid = False
        friendly_before = _snapshot_health(_friendly_minions(fighters))
        for _tyrande_copy in range(spell_cast_copies):
            current_card = card
            while True:
                spell_power = sim_spell_power(gs, player_id, fighters)
                if hostile_spellburst_pending > 0 and not _is_battlecry_step(defn, card):
                    for _ in range(hostile_spellburst_pending):
                        sb = _apply_hostile_invader_spellburst(
                            taunts, fighters, spell_mult=spell_mult,
                        )
                        _merge_spell_result(total, sb)
                    hostile_spellburst_pending = 0

                if (
                    manasaber_spellburst_pending > 0
                    and not _is_battlecry_step(defn, card)
                    and not _is_rush_minion_step(defn, card)
                ):
                    for _ in range(manasaber_spellburst_pending):
                        sb = _apply_manasaber_spellburst(fighters)
                        _merge_spell_result(total, sb)
                    manasaber_spellburst_pending = 0

                if devourer_spellburst_pending > 0 and get_board_spell_def(
                    _step_card_id(defn, card)
                ):
                    for _ in range(devourer_spellburst_pending):
                        sb = _apply_devourer_spellburst(fighters, mult=spell_mult)
                        _merge_spell_result(total, sb)
                    devourer_spellburst_pending = 0

                res = defn.apply(
                    taunts, fighters, mult=spell_mult, enemy_shield=enemy_shield, rng=roll,
                    gs=gs, player_id=player_id, card=current_card,
                    opponent_hero_hp=opponent_hero_hp,
                    fire_spell_played_this_turn=fire_spell_played_this_turn,
                    spell_power=spell_power,
                    combo_active=combo_active,
                    next_turn_preview=next_turn_preview,
                    finale_active=finale_active,
                    hero_damaged_this_turn=hero_damaged_this_turn,
                    friendly_minion_died_this_turn=friendly_minion_died,
                )
                res = _coerce_spell_apply_result(res)
                _merge_step_result(total, res, defn, current_card)
                if not friendly_minion_died and _minion_died_in_wave(
                    _friendly_minions(fighters), friendly_before,
                ):
                    friendly_minion_died = True

                if _step_counts_as_fire_spell_played(defn, card):
                    fire_spell_played_this_turn = True
                combo_active = True

                consumed = getattr(card, "arcane_flow_consumed_entity_ids", None)
                if consumed:
                    for eid in consumed:
                        shattered_arcane_flow_entities.add(eid)
                for eid in res.consume_hand_entity_ids:
                    shattered_arcane_flow_entities.add(eid)

                if mana_left is not None and not mana_paid:
                    mana_left -= cost
                if mana_left is not None and res.mana_crystal_gain > 0:
                    mana_left += res.mana_crystal_gain
                if not mana_paid:
                    mana_paid = True
                    trigger_corrupt_on_sequence_play(
                        cost, seq, idx, pending, skip_entity_id=played_eid,
                    )

                trigger_arcane_flow_shatter_on_play(
                    current_card, gs, player_id, pending, shattered_arcane_flow_entities,
                )
                trigger_arcane_flow_recombine_on_play(
                    current_card, gs, player_id, pending, shattered_arcane_flow_entities,
                )

                if _is_hostile_invader_step(defn, current_card):
                    hostile_spellburst_pending += 1

                if _is_manasaber_rush_step(defn, current_card):
                    manasaber_spellburst_pending += 1

                if _is_devourer_step(defn, current_card):
                    devourer_spellburst_pending += 1

                if _is_tyrande_step(defn, current_card):
                    tyrande_double_remaining = 3

                played_cid = _step_card_id(defn, current_card)
                from .damaged_spell_power import is_damaged_spellpower_step
                if not hp_used_inline and is_damaged_spellpower_step(defn, current_card):
                    new_mana = try_inline_mage_fireblast_setup(
                        fighters, gs, player_id, mana_left, already_used=False,
                    )
                    if new_mana is not None and mana_left is not None and new_mana < mana_left:
                        mana_left = new_mana
                        hp_used_inline = True

                if res.self_hero_damage > 0:
                    hero_damaged_this_turn = True
                if hp is not None:
                    if res.self_hero_heal > 0:
                        hp += res.self_hero_heal
                    if res.self_hero_damage > 0:
                        hp -= res.self_hero_damage
                        if hp <= 0:
                            return total, hp, mana_left

                if res.add_hand_spell_id:
                    next_defn = get_board_spell_def(res.add_hand_spell_id)
                    if next_defn:
                        next_cost = next_defn.base_cost
                        pending.append((
                            next_defn,
                            next_cost,
                            _SyntheticSpellCard(
                                res.add_hand_spell_id,
                                next_cost,
                                stored_damage=res.add_hand_spell_damage,
                            ),
                        ))
                for sid, scost, sdmg in res.add_hand_pending:
                    next_defn = get_board_spell_def(sid)
                    if next_defn:
                        pending.append((
                            next_defn,
                            scost if scost >= 0 else next_defn.base_cost,
                            _SyntheticSpellCard(
                                sid,
                                scost if scost >= 0 else next_defn.base_cost,
                                stored_damage=sdmg,
                            ),
                        ))

                if res.drinks_after > 0 and (hp is None or hp > 0):
                    if hp is not None and res.self_hero_damage > 0 and hp <= res.self_hero_damage:
                        break
                    cid = _spell_card_id(current_card) or (defn.card_ids[0] if defn.card_ids else "")
                    next_cid = DRINK_NEXT.get(cid)
                    if next_cid:
                        next_cost = drink_play_cost(next_cid, cost)
                        if mana_left is not None:
                            if next_cost > mana_left:
                                break
                            mana_left -= next_cost
                        current_card = _SyntheticSpellCard(next_cid, next_cost)
                        cost = next_cost
                        continue
                break

    return total, hp, mana_left


def monte_carlo_spell_face(
    taunts: List[dict],
    fighters: List[dict],
    sequence: List[SpellPlayStep],
    *,
    spell_mult: int = 1,
    enemy_shield: bool = False,
    trials: int = MC_TRIALS,
) -> Tuple[int, float]:
    """
    对仅法术序列做蒙特卡洛（不含场面攻击）。
    返回 (样本最高直伤, 样本均值)。
    """
    if not sequence:
        return 0, 0.0
    if not sequence_uses_random(sequence):
        res = apply_spell_sequence(
            deepcopy(taunts), deepcopy(fighters), sequence,
            spell_mult=spell_mult, enemy_shield=enemy_shield,
        )
        v = res.direct_face_damage
        return v, float(v)

    peak = 0
    total = 0
    for i in range(trials):
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        res = apply_spell_sequence(
            ts, fs, sequence, spell_mult=spell_mult, enemy_shield=enemy_shield,
            rng=random.Random(i + 1),
        )
        peak = max(peak, res.direct_face_damage)
        total += res.direct_face_damage
    return peak, total / trials
