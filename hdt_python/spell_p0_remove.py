# spell_p0_remove.py — P0 第四阶段：消灭/变形法术（16 张）

from __future__ import annotations

import json
import random
from copy import deepcopy
from hdt_python.app_paths import resource_path
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    hand_effect_active,
    _apply_damage,
    _apply_random_destroy_enemy_minions,
    _destroy_enemy_minion,
    _lethal_target_enemy_minions,
    _living_enemy_board_minions,
    _register,
    _remove_dead_taunts,
    _strip_enemy_minion_keywords,
    _summon_friendly_fighter,
    _summon_minion_copy,
)

if TYPE_CHECKING:
    from .power_parser import Entity

# 回溯法术：随机结算后可重打一次，模拟 2 次取较好结果
REWIND_ATTEMPTS = 2
REWIND_SPELL_IDS = frozenset({"TIME_433"})

# 连环灾难：腐蚀后 card_id 变化，消灭数量递增
CASCADING_DISASTER_KILLS = {
    "DMF_117": 1,
    "DMF_117t": 2,
    "DMF_117t2": 3,
}

_CARD_COST_CACHE: Optional[Dict[str, int]] = None


def _card_mana_cost_from_db(card_id: str) -> Optional[int]:
    global _CARD_COST_CACHE
    if not card_id:
        return None
    if _CARD_COST_CACHE is None:
        path = resource_path("json", "cards.json")
        cache: Dict[str, int] = {}
        if path.is_file():
            try:
                for row in json.loads(path.read_text(encoding="utf-8")):
                    cid = row.get("id") or ""
                    cost = row.get("cost")
                    if cid and cost is not None:
                        cache[cid] = int(cost)
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                pass
        _CARD_COST_CACHE = cache
    return _CARD_COST_CACHE.get(card_id)


def _unit_mana_cost(unit: dict) -> int:
    """随从法力值：优先模拟 dict 的 cost，其次 CardID 查表，最后用 max(攻, 血) 兜底。"""
    if unit.get("kind") == "hero":
        return 0
    c = unit.get("cost")
    if c is not None and int(c) > 0:
        return int(c)
    cid = unit.get("card_id") or ""
    db_cost = _card_mana_cost_from_db(cid)
    if db_cost is not None:
        return db_cost
    return max(int(unit.get("atk", 0)), int(unit.get("health", 0)))


def _devolve_unit_once(unit: dict) -> None:
    """衰变一次：费用 -1，变为 N/N 白板随从（N = 新费用）。"""
    if unit.get("kind") == "hero" or unit.get("health", 0) <= 0:
        return
    new_cost = max(0, _unit_mana_cost(unit) - 1)
    unit["atk"] = new_cost
    unit["health"] = new_cost
    unit["cost"] = new_cost
    unit["card_id"] = ""
    unit["shield"] = False
    _strip_enemy_minion_keywords(unit)


def cascading_disaster_kill_count(card: Optional["Entity"]) -> int:
    cid = (card.card_id if card and card.card_id else "") or "DMF_117"
    return CASCADING_DISASTER_KILLS.get(cid, 1)


def _is_legendary_minion(unit: dict) -> bool:
    if unit.get("legendary"):
        return True
    rarity = unit.get("rarity")
    if rarity is None:
        tags = unit.get("tags") or {}
        rarity = tags.get("RARITY")
    return rarity in ("LEGENDARY", 5)


def _hex_transform(unit: dict) -> None:
    """妖术：0/1 嘲讽青蛙。"""
    unit["atk"] = 0
    unit["health"] = 1
    unit["taunt"] = True
    unit["shield"] = False
    unit["lifesteal"] = False
    unit["poisonous"] = False
    unit["spell_immune"] = False
    unit["charge"] = False
    unit["rush"] = False
    unit["card_id"] = ""


def _destroy_friendly_minion(unit: dict) -> None:
    if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
        return
    unit["health"] = 0
    unit["attacks_left"] = 0


def _destroy_all_minions(taunts: List[dict], fighters: List[dict]) -> None:
    """消灭双方所有随从（大灾变等）。"""
    for unit in list(taunts):
        if unit.get("health", 0) > 0:
            unit["health"] = 0
    _remove_dead_taunts(taunts)
    for f in fighters:
        _destroy_friendly_minion(f)


def _apply_cataclysm(
    taunts: List[dict],
    fighters: List[dict],
    **_kw,
) -> SpellApplyResult:
    """大灾变：消灭所有随从（弃牌斩杀模拟中不计）。"""
    _destroy_all_minions(taunts, fighters)
    return SpellApplyResult()


def _living_friendly_minions(fighters: List[dict]) -> List[dict]:
    return [
        f for f in fighters
        if f.get("kind") == "minion" and f.get("health", 0) > 0
    ]


def _score_board_face(
    taunts: List[dict],
    fighters: List[dict],
    enemy_shield: bool,
) -> int:
    return project_board_face_after_spell(taunts, fighters, enemy_shield) or 0


def _apply_optimal_destroy_enemy(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
    filter_fn: Optional[Callable[[dict], bool]] = None,
    card=None,
    **_kw,
) -> SpellApplyResult:
    """消灭最优敌方随从（有嘲讽时仅嘲讽；清场指向性无嘲讽时可点随从）。"""
    living = _lethal_target_enemy_minions(taunts, card=card)
    if filter_fn:
        living = [t for t in living if filter_fn(t)]
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            None,
        )
        if target is None or target.get("health", 0) <= 0:
            continue
        _destroy_enemy_minion(target, ts, fs)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")

    if best_eid is None:
        return SpellApplyResult()
    for unit in taunts:
        if unit.get("entity_id") == best_eid and unit.get("health", 0) > 0:
            _destroy_enemy_minion(unit, taunts, fighters)
            break
    return SpellApplyResult()


def _apply_optimal_destroy_any_minion(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
    filter_fn: Optional[Callable[[dict], bool]] = None,
    card=None,
    **_kw,
) -> Optional[dict]:
    """消灭最优随从（敌我皆可），返回被消灭单位（用于回血等）。"""
    candidates: List[tuple] = []
    for t in _lethal_target_enemy_minions(taunts, card=card):
        if filter_fn and not filter_fn(t):
            continue
        candidates.append(("enemy", t.get("entity_id"), t))
    for f in _living_friendly_minions(fighters):
        if filter_fn and not filter_fn(f):
            continue
        candidates.append(("friendly", f.get("entity_id"), f))

    best_score = -1
    best: Optional[tuple] = None
    best_unit: Optional[dict] = None

    for side, eid, ref in candidates:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        if side == "enemy":
            target = next((x for x in ts if x.get("entity_id") == eid), None)
            if target is None:
                continue
            killed = dict(target)
            _destroy_enemy_minion(target, ts, fs)
        else:
            target = next((x for x in fs if x.get("entity_id") == eid), None)
            if target is None:
                continue
            killed = dict(target)
            _destroy_friendly_minion(target)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best = (side, eid)
            best_unit = killed

    if best is None or best_unit is None:
        return None
    side, eid = best
    if side == "enemy":
        for unit in taunts:
            if unit.get("entity_id") == eid and unit.get("health", 0) > 0:
                _destroy_enemy_minion(unit, taunts, fighters)
                break
    else:
        for unit in fighters:
            if unit.get("entity_id") == eid and unit.get("health", 0) > 0:
                _destroy_friendly_minion(unit)
                break
    return best_unit


def _apply_optimal_silence_enemy(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """沉默单个敌方随从：有嘲讽时仅嘲讽；无嘲讽时不用法术点随从。"""
    living = _lethal_target_enemy_minions(taunts)
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next((x for x in ts if x.get("entity_id") == t.get("entity_id")), None)
        if target is None:
            continue
        _strip_enemy_minion_keywords(target)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")

    if best_eid is None:
        return SpellApplyResult()
    for unit in taunts:
        if unit.get("entity_id") == best_eid:
            _strip_enemy_minion_keywords(unit)
            break
    return SpellApplyResult()


def _random_silence_destroy_one(
    taunts: List[dict],
    fighters: List[dict],
    rng: random.Random,
) -> bool:
    """随机沉默并消灭一个敌方随从。无目标时返回 False。"""
    living = _living_enemy_board_minions(taunts)
    if not living:
        return False
    target = rng.choice(living)
    _strip_enemy_minion_keywords(target)
    _destroy_enemy_minion(target, taunts, fighters)
    return True


def _apply_rewind_random_silence_destroy(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
    rng: Optional[random.Random] = None,
    attempts: int = REWIND_ATTEMPTS,
) -> SpellApplyResult:
    """回溯：从同一初始场面随机消灭 attempts 次，取场攻最好的一次。"""
    initial_t = deepcopy(taunts)
    initial_f = deepcopy(fighters)
    best_score = -1
    best_t: Optional[List[dict]] = None
    best_f: Optional[List[dict]] = None

    if rng is None:
        rolls = [random.Random(seed) for seed in range(attempts)]
    else:
        rolls = [random.Random(rng.randint(0, 2**31 - 1)) for _ in range(attempts)]

    for roll in rolls:
        ts = deepcopy(initial_t)
        fs = deepcopy(initial_f)
        _random_silence_destroy_one(ts, fs, roll)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_t, best_f = ts, fs

    if best_t is not None and best_f is not None:
        taunts[:] = best_t
        fighters[:] = best_f
    return SpellApplyResult()


def _apply_optimal_silence_destroy_enemy(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """沉默并消灭单个敌方随从（枚举最优，供非回溯随机法术复用）。"""
    living = _living_enemy_board_minions(taunts)
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            None,
        )
        if target is None or target.get("health", 0) <= 0:
            continue
        _strip_enemy_minion_keywords(target)
        _destroy_enemy_minion(target, ts, fs)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")

    if best_eid is None:
        return SpellApplyResult()
    for unit in taunts:
        if unit.get("entity_id") == best_eid and unit.get("health", 0) > 0:
            _strip_enemy_minion_keywords(unit)
            _destroy_enemy_minion(unit, taunts, fighters)
            break
    return SpellApplyResult()


def _apply_optimal_hex(
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """妖术：使一个随从变为 0/1 嘲讽青蛙（敌我皆可点）。"""
    candidates: List[tuple] = []
    for i, t in enumerate(taunts):
        if t.get("health", 0) > 0 and t.get("kind") != "hero":
            candidates.append(("enemy", i, t.get("entity_id")))
    for i, f in enumerate(fighters):
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            candidates.append(("friendly", i, f.get("entity_id")))

    best_score = -1
    best: Optional[tuple] = None
    for side, idx, eid in candidates:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        if side == "enemy":
            target = ts[idx]
            _hex_transform(target)
        else:
            target = fs[idx]
            _hex_transform(target)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best = (side, idx)

    if best is None:
        return SpellApplyResult()
    side, idx = best
    if side == "enemy":
        _hex_transform(taunts[idx])
    else:
        _hex_transform(fighters[idx])
    return SpellApplyResult()


def _apply_asphyxiate(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """窒息：消灭攻击力最高的敌方随从。"""
    living = _living_enemy_board_minions(taunts)
    if not living:
        return SpellApplyResult()
    top_atk = max(t.get("atk", 0) for t in living)
    pool = [t for t in living if t.get("atk", 0) == top_atk]
    best = max(pool, key=lambda t: (t.get("health", 0), t.get("taunt", False)))
    for unit in taunts:
        if unit.get("entity_id") == best.get("entity_id"):
            _destroy_enemy_minion(unit, taunts, fighters)
            break
    return SpellApplyResult()


def _apply_chaotic_consumption(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """混乱吞噬：消灭一个友方随从以消灭一个敌方随从。"""
    friends = _living_friendly_minions(fighters)
    enemies = _living_enemy_board_minions(taunts)
    if not friends or not enemies:
        return SpellApplyResult()

    best_score = -1
    best_pair: Optional[tuple] = None
    for f in friends:
        for e in enemies:
            ts = deepcopy(taunts)
            fs = deepcopy(fighters)
            ft = next((x for x in fs if x.get("entity_id") == f.get("entity_id")), None)
            et = next((x for x in ts if x.get("entity_id") == e.get("entity_id")), None)
            if ft is None or et is None:
                continue
            _destroy_friendly_minion(ft)
            _destroy_enemy_minion(et, ts, fs)
            score = _score_board_face(ts, fs, enemy_shield)
            if score > best_score:
                best_score = score
                best_pair = (f.get("entity_id"), e.get("entity_id"))

    if best_pair is None:
        return SpellApplyResult()
    fid, eid = best_pair
    for unit in fighters:
        if unit.get("entity_id") == fid:
            _destroy_friendly_minion(unit)
            break
    for unit in taunts:
        if unit.get("entity_id") == eid:
            _destroy_enemy_minion(unit, taunts, fighters)
            break
    return SpellApplyResult()


def _apply_cascading_disaster(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    rng=None,
    card=None,
    **_kw,
) -> SpellApplyResult:
    count = cascading_disaster_kill_count(card) * mult
    roll = rng if rng is not None else random.Random(0)
    return _apply_random_destroy_enemy_minions(
        taunts, fighters, count=count, rng=roll,
    )


def _apply_devolve(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    **_kw,
) -> SpellApplyResult:
    """衰变（简化）：移除所有敌方随从关键词，身材不变。"""
    for _ in range(max(1, mult)):
        for unit in _living_enemy_board_minions(taunts):
            _strip_enemy_minion_keywords(unit)
    return SpellApplyResult()


def _apply_devolving_missiles(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    rng=None,
    **_kw,
) -> SpellApplyResult:
    """衰变飞弹：随机向敌方随从发射 3 枚飞弹，各衰变一次（5 费→4/4 白板）。"""
    roll = rng if rng is not None else random.Random(0)
    missiles = 3 * max(1, mult)
    for _ in range(missiles):
        living = _living_enemy_board_minions(taunts)
        if not living:
            break
        target = roll.choice(living)
        _devolve_unit_once(target)
        if target.get("health", 0) <= 0:
            _destroy_enemy_minion(target, taunts, fighters)
    return SpellApplyResult()


def _apply_dubious_purchase(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    rng=None,
    card=None,
    combo_active: bool = False,
    gs=None,
    player_id=None,
    next_turn_preview: bool = False,
    **_kw,
) -> SpellApplyResult:
    """可疑交易：连击时随机消灭一个敌方随从；未连击仅抽牌，场攻不计消灭。"""
    if not hand_effect_active(
        card,
        combo_active=combo_active,
        gs=gs,
        player_id=player_id,
        next_turn_preview=next_turn_preview,
    ):
        return SpellApplyResult()
    roll = rng if rng is not None else random.Random(0)
    return _apply_random_destroy_enemy_minions(
        taunts, fighters, count=mult, rng=roll,
    )


def _apply_dethrone(taunts, fighters, *, mult, enemy_shield, card=None, **_kw,) -> SpellApplyResult:
    """诛灭暴君：消灭一个随从（连击召唤 8 费随从 v1 不模拟）。"""
    for _ in range(max(1, mult)):
        _apply_optimal_destroy_any_minion(
            taunts, fighters, enemy_shield=enemy_shield, card=card,
        )
    return SpellApplyResult()


def _apply_siphon_soul(taunts, fighters, *, mult, enemy_shield, card=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """灵魂虹吸：消灭一个随从，英雄恢复 3 生命。"""
    _apply_optimal_destroy_any_minion(
        taunts, fighters, enemy_shield=enemy_shield, card=card,
    )
    return SpellApplyResult(self_hero_heal=_sd(3, mult=mult, spell_power=spell_power))


def _apply_garona_last_stand(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """迦罗娜的奋战：消灭一个传说随从。"""
    for _ in range(max(1, mult)):
        if not any(
            _is_legendary_minion(t)
            for t in _living_enemy_board_minions(taunts)
        ):
            break
        _apply_optimal_destroy_enemy(
            taunts, fighters, enemy_shield=enemy_shield,
            filter_fn=_is_legendary_minion,
        )
    return SpellApplyResult()


def _apply_hex(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    return _apply_optimal_hex(taunts, fighters, enemy_shield=enemy_shield)


def _apply_consume_magic(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    return _apply_optimal_silence_enemy(taunts, fighters, enemy_shield=enemy_shield)


def _apply_deafen(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    card=None,
    combo_active: bool = False,
    gs=None,
    player_id: Optional[int] = None,
    **_kw,
) -> SpellApplyResult:
    """致聋术 JAM_022：沉默一个敌方随从；连击并对其造成 2 点伤害。"""
    living = _lethal_target_enemy_minions(taunts)
    if not living:
        return SpellApplyResult()

    combo = hand_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    )
    dmg = _sd(2, mult=mult) if combo else 0
    best_score = -1
    best_eid = None
    best_heal = 0

    for t in living:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            None,
        )
        if target is None:
            continue
        _strip_enemy_minion_keywords(target)
        heal = 0
        if dmg > 0:
            heal = _apply_damage(target, dmg, taunts=ts, fighters=fs)
        _remove_dead_taunts(ts)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = t.get("entity_id")
            best_heal = heal

    if best_eid is None:
        return SpellApplyResult()

    for unit in taunts:
        if unit.get("entity_id") == best_eid:
            _strip_enemy_minion_keywords(unit)
            heal = best_heal
            if dmg > 0:
                heal = _apply_damage(unit, dmg, taunts=taunts, fighters=fighters)
            _remove_dead_taunts(taunts)
            return SpellApplyResult(opponent_lifesteal_heal=heal)
    return SpellApplyResult()


def _apply_cannibalize(taunts, fighters, *, mult, enemy_shield, card=None, **_kw,) -> SpellApplyResult:
    """野蛮残食：消灭一个随从，为友方角色恢复等同于其生命值的生命。"""
    killed = _apply_optimal_destroy_any_minion(
        taunts, fighters, enemy_shield=enemy_shield, card=card,
    )
    if killed is None:
        return SpellApplyResult()
    heal = max(0, int(killed.get("health", 0))) * mult
    return SpellApplyResult(self_hero_heal=heal)


def _apply_cease_to_exist(taunts, fighters, *, mult, enemy_shield, rng=None, **_kw,) -> SpellApplyResult:
    """抹除存在：随机沉默消灭 1 个敌方随从；回溯模拟 2 次取较好结果。"""
    res = SpellApplyResult()
    for _ in range(max(1, mult)):
        _apply_rewind_random_silence_destroy(
            taunts, fighters, enemy_shield=enemy_shield, rng=rng,
        )
    return res


def _apply_suffocating_shadows(taunts, fighters, *, mult, enemy_shield, rng=None, **_kw,) -> SpellApplyResult:
    """窒息暗影：正常打出时随机消灭一个敌方随从（弃牌触发不模拟）。"""
    roll = rng if rng is not None else random.Random(0)
    return _apply_random_destroy_enemy_minions(
        taunts, fighters, count=mult, rng=roll,
    )


def _apply_shard_of_naaru(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """纳鲁碎片：沉默所有敌方随从。"""
    for _ in range(max(1, mult)):
        for unit in _living_enemy_board_minions(taunts):
            _strip_enemy_minion_keywords(unit)
    return SpellApplyResult()


def _apply_schism(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """教派分歧：友方随从 +2/+3，召唤其复制（v1 复制当回合失调）。"""
    living = _living_friendly_minions(fighters)
    if not living:
        return SpellApplyResult()

    best_score = -1
    best_eid = None
    for f in living:
        fs = deepcopy(fighters)
        ts = deepcopy(taunts)
        target = next((x for x in fs if x.get("entity_id") == f.get("entity_id")), None)
        if target is None:
            continue
        target["atk"] = target.get("atk", 0) + _sd(2, mult=mult, spell_power=spell_power)
        target["health"] = target.get("health", 0) + _sd(3, mult=mult, spell_power=spell_power)
        _summon_minion_copy(fs, target)
        score = _score_board_face(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_eid = f.get("entity_id")

    if best_eid is None:
        return SpellApplyResult()
    for target in fighters:
        if target.get("entity_id") == best_eid:
            target["atk"] = target.get("atk", 0) + _sd(2, mult=mult, spell_power=spell_power)
            target["health"] = target.get("health", 0) + _sd(3, mult=mult, spell_power=spell_power)
            _summon_minion_copy(fighters, target)
            break
    return SpellApplyResult()


def _apply_flight_maneuvers(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """飞龙机动：召唤两条 4/2 幼龙；己方随从 +1 攻与圣盾（v1 幼龙当回合失调）。"""
    for _ in range(max(1, mult)):
        _summon_friendly_fighter(fighters, 4, 2)
        _summon_friendly_fighter(fighters, 4, 2)
        for f in fighters:
            if f.get("kind") != "minion" or f.get("health", 0) <= 0:
                continue
            f["atk"] = f.get("atk", 0) + 1
            f["shield"] = True
    return SpellApplyResult()


def _register_p0_remove() -> None:
    specs: List[tuple] = [
        (("MIS_903",), 4, "可疑交易", _apply_dubious_purchase, True, None),
        (("TIME_712",), 7, "诛灭暴君", _apply_dethrone, False, None),
        (("CORE_EX1_246",), 3, "妖术", _apply_hex, False, None),
        (("BT_490",), 1, "吞噬魔法", _apply_consume_magic, False, None),
        (("JAM_022",), 1, "致聋术", _apply_deafen, False, None),
        (("TIME_433",), 3, "抹除存在", _apply_cease_to_exist, True, None),
        (("CFM_696",), 2, "衰变", _apply_devolve, False, None),
        (("CORE_RLK_087",), 3, "窒息", _apply_asphyxiate, False, None),
        (("TTN_932",), 1, "混乱吞噬", _apply_chaotic_consumption, False, None),
        (("DMF_117", "DMF_117t", "DMF_117t2"), 4, "连环灾难", _apply_cascading_disaster, True, None),
        (("CORE_EX1_309",), 4, "灵魂虹吸", _apply_siphon_soul, False, None),
        (("CATA_203",), 2, "迦罗娜的奋战", _apply_garona_last_stand, False, None),
        (("NX2_020",), 4, "野蛮残食", _apply_cannibalize, False, None),
        (("CATA_306",), 4, "教派分歧", _apply_schism, False, None),
        (("REV_239",), 3, "窒息暗影", _apply_suffocating_shadows, True, None),
        (("CATA_479",), 4, "飞龙机动", _apply_flight_maneuvers, False, None),
        (("SW_441",), 1, "纳鲁碎片", _apply_shard_of_naaru, False, None),
        (("SCH_235",), 1, "衰变飞弹", _apply_devolving_missiles, True, None),
        (("LOOT_417",), 5, "大灾变", _apply_cataclysm, False, None),
    ]
    for card_ids, cost, name, fn, uses_random, cost_fn in specs:
        _register(
            BoardSpellDef(
                card_ids=card_ids,
                base_cost=cost,
                name=name,
                apply=fn,
                uses_random=uses_random,
                cost_fn=cost_fn,
            )
        )


_register_p0_remove()
