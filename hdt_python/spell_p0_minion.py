# spell_p0_minion.py — P0 第二阶段：解场伤法术（33 张）

from __future__ import annotations

from copy import deepcopy
from typing import Callable, List, Optional, TYPE_CHECKING

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_best_minion_damage,
    _apply_damage,
    _apply_damage_to_unit,
    _apply_direct_face,
    _apply_enemy_minions_aoe,
    _apply_optimal_single_target_damage,
    _can_spell_hit_enemy_face,
    _iter_spell_minion_target_indices,
    _register,
    _remove_dead_taunts,
    _summon_friendly_fighter,
    _target_key,
    hand_effect_active,
    player_corpses,
)
from .board_damage import apply_divine_shield_to_hits

if TYPE_CHECKING:
    from .power_parser import GameState


def _minion_damage_fn(
    base: int,
    *,
    heal_enemy_on_kill: int = 0,
    filter_fn: Optional[Callable[[dict], bool]] = None,
    summon_on_kill: Optional[tuple] = None,
    summon_copy_on_kill: bool = False,
    self_lifesteal: bool = False,
    allow_no_taunt_minion_targets: bool = False,
 spell_power=0) -> Callable:
    def fn(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw):
        token = summon_on_kill if summon_on_kill else None
        return _apply_best_minion_damage(
            taunts, fighters, _sd(base, mult=mult, spell_power=spell_power),
            enemy_shield=enemy_shield,
            heal_enemy_on_kill=_sd(heal_enemy_on_kill, mult=mult, spell_power=spell_power),
            filter_fn=filter_fn,
            summon_on_kill=token,
            summon_copy_on_kill=summon_copy_on_kill,
            self_lifesteal=self_lifesteal,
            allow_no_taunt_minion_targets=allow_no_taunt_minion_targets,
            **_kw,
        )
    return fn


def _optimal_damage_fn(base: int, spell_power=0) -> Callable:
    def fn(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw):
        return _apply_optimal_single_target_damage(
            taunts, fighters, _sd(base, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        )
    return fn


def _wounded(t: dict) -> bool:
    return int(t.get("damage", 0) or 0) > 0


def _vendetta_cost(gs: "GameState", player_id: int) -> int:
    hero = gs.get_hero(player_id)
    my_class = hero.tags.get("CLASS") if hero else None
    if not my_class:
        return 4
    for card in gs.get_hand(player_id):
        if not card.card_id or card.cardtype not in ("SPELL", "MINION", "WEAPON"):
            continue
        card_class = card.tags.get("CLASS")
        if not card_class or card_class in (my_class, "NEUTRAL"):
            continue
        return 0
    return 4


def _apply_torch(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    return _apply_best_minion_damage(
        taunts, fighters, _sd(8, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        filter_fn=_wounded,
    )


def _apply_fistful_of_corpses(taunts, fighters, *, mult, enemy_shield, spell_power=0, gs=None, player_id=None, **_kw) -> SpellApplyResult:
    corpses = player_corpses(gs, player_id) if gs is not None and player_id is not None else 0
    return _apply_best_minion_damage(
        taunts, fighters, _sd(corpses, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )


def _apply_morbid_swarm(taunts, fighters, *, mult, enemy_shield, spell_power=0, gs=None, player_id=None, **_kw) -> SpellApplyResult:
    # 抉择：残骸≥2 时取 4 伤分支（召唤蚂蚁不加本回合场攻）
    corpses = player_corpses(gs, player_id) if gs is not None and player_id is not None else 0
    if corpses < 2:
        return SpellApplyResult()
    return _apply_best_minion_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )


def _apply_infiltrate(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """选择一个随从，对其余所有随从造成 3 点伤害（含己方）。"""
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    all_units: List[tuple] = []
    for t in taunts:
        if t.get("health", 0) > 0:
            all_units.append(("enemy", _target_key(t)))
    for f in fighters:
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            all_units.append(("friendly", _target_key(f)))

    if len(all_units) <= 1:
        return SpellApplyResult()

    best_score = -1
    best_skip = all_units[0][1]

    for skip_key in {k for _, k in all_units}:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        for t in ts:
            if t.get("health", 0) <= 0 or _target_key(t) == skip_key:
                continue
            _apply_damage(t, dmg, taunts=ts, fighters=fs)
        for f in fs:
            if f.get("kind") != "minion" or f.get("health", 0) <= 0:
                continue
            if _target_key(f) == skip_key:
                continue
            _apply_damage(f, dmg, taunts=ts, fighters=fs)
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_skip = skip_key

    ts = taunts
    fs = fighters
    res = SpellApplyResult()
    for t in ts:
        if t.get("health", 0) <= 0 or _target_key(t) == best_skip:
            continue
        res.opponent_lifesteal_heal += _apply_damage(t, dmg, taunts=ts, fighters=fs)
    for f in fs:
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        if _target_key(f) == best_skip:
            continue
        _apply_damage(f, dmg, taunts=ts, fighters=fs)
    _remove_dead_taunts(ts)
    return res


def _apply_light_it_burns(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    best_score = -1
    best_idx: Optional[int] = None
    for i in _iter_spell_minion_target_indices(taunts, card=card):
        t = taunts[i]
        dmg = max(0, int(t.get("atk", 0))) * mult
        if dmg <= 0:
            continue
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            ts[i],
        )
        _apply_damage_to_unit(
            target, dmg, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return SpellApplyResult()

    target = taunts[best_idx]
    dmg = max(0, int(target.get("atk", 0))) * mult
    res = SpellApplyResult()
    heal, _, _ = _apply_damage_to_unit(
        target, dmg, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    _remove_dead_taunts(taunts)
    return res


def _living_by_zone(taunts: List[dict]) -> List[dict]:
    living = [
        t for t in taunts
        if t.get("health", 0) > 0 and not t.get("spell_immune")
    ]
    return sorted(living, key=lambda t: int(t.get("zone_pos", 0) or 0))


def _apply_meteor(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    primary_dmg = _sd(15, mult=mult, spell_power=spell_power)
    splash = _sd(4, mult=mult, spell_power=spell_power)
    by_pos = _living_by_zone(taunts)
    if not by_pos:
        return SpellApplyResult()

    best_score = -1
    best_primary_idx = 0

    for pi, primary in enumerate(by_pos):
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        pkey = _target_key(primary)
        for t in ts:
            if t.get("health", 0) <= 0:
                continue
            if _target_key(t) == pkey:
                amt = primary_dmg
            elif abs(int(t.get("zone_pos", 0) or 0) - int(primary.get("zone_pos", 0) or 0)) == 1:
                amt = splash
            else:
                continue
            _apply_damage(t, amt, taunts=ts, fighters=fs)
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_primary_idx = pi

    primary = by_pos[best_primary_idx]
    pkey = _target_key(primary)
    res = SpellApplyResult()
    for t in taunts:
        if t.get("health", 0) <= 0:
            continue
        if _target_key(t) == pkey:
            res.opponent_lifesteal_heal += _apply_damage(
                t, primary_dmg, taunts=taunts, fighters=fighters,
            )
        elif abs(int(t.get("zone_pos", 0) or 0) - int(primary.get("zone_pos", 0) or 0)) == 1:
            res.opponent_lifesteal_heal += _apply_damage(
                t, splash, taunts=taunts, fighters=fighters,
            )
    _remove_dead_taunts(taunts)
    return res


def _flash_flood_once(taunts, fighters, dmg: int, *, enemy_shield: bool) -> SpellApplyResult:
    by_pos = _living_by_zone(taunts)
    if not by_pos:
        return SpellApplyResult()
    targets = {_target_key(by_pos[0])}
    if len(by_pos) > 1:
        targets.add(_target_key(by_pos[-1]))
    res = SpellApplyResult()
    for t in taunts:
        if t.get("health", 0) <= 0 or _target_key(t) not in targets:
            continue
        res.opponent_lifesteal_heal += _apply_damage(
            t, dmg, taunts=taunts, fighters=fighters,
        )
    _remove_dead_taunts(taunts)
    return res


def _apply_flash_flood(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """最左 + 最右 5 伤；亮边（流放）时再执行一次。"""
    dmg = _sd(5, mult=mult, spell_power=spell_power)
    res = _flash_flood_once(taunts, fighters, dmg, enemy_shield=enemy_shield)
    if hand_effect_active(card):
        extra = _flash_flood_once(taunts, fighters, dmg, enemy_shield=enemy_shield)
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    return res


def _apply_fumigate(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """主目标 + 同 card_id 的其他随从 3 伤。"""
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    candidates = [
        t for t in taunts
        if t.get("health", 0) > 0 and not t.get("spell_immune")
    ]
    if not candidates:
        return SpellApplyResult()

    best_score = -1
    best_primary = candidates[0]

    for primary in candidates:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        cid = primary.get("card_id", "")
        for t in ts:
            if t.get("health", 0) <= 0:
                continue
            if _target_key(t) == _target_key(primary) or (cid and t.get("card_id") == cid):
                _apply_damage(t, dmg, taunts=ts, fighters=fs)
        _remove_dead_taunts(ts)
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_primary = primary

    cid = best_primary.get("card_id", "")
    res = SpellApplyResult()
    for t in taunts:
        if t.get("health", 0) <= 0:
            continue
        if _target_key(t) == _target_key(best_primary) or (cid and t.get("card_id") == cid):
            res.opponent_lifesteal_heal += _apply_damage(
                t, dmg, taunts=taunts, fighters=fighters,
            )
    _remove_dead_taunts(taunts)
    return res


def _apply_lightning_storm(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    return _apply_enemy_minions_aoe(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_blood_in_the_water(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """3 伤（可选目标）+ 始终召唤 5/5 突袭（当回合仅解场、不打脸）。"""
    amount = max(_sd(3, mult=mult, spell_power=spell_power), 0)
    if amount <= 0:
        return SpellApplyResult()

    def _score_with_shark(ts, fs, direct: int) -> int:
        _summon_friendly_fighter(fs, 5, 5, rush=True)
        return direct + project_board_face_after_spell(ts, fs, enemy_shield)

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
        return _score_with_shark(ts, fs, direct)

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
        return SpellApplyResult()

    if best_face_hit:
        res = _apply_direct_face(amount, enemy_shield)
        _summon_friendly_fighter(fighters, 5, 5, rush=True)
        return res

    assert best_minion_idx is not None
    res = SpellApplyResult()
    target = taunts[best_minion_idx]
    heal, face, _ = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    res.direct_face_damage = face
    _remove_dead_taunts(taunts)
    _summon_friendly_fighter(fighters, 5, 5, rush=True)
    return res


def _apply_initiation(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """4 伤；击杀后召唤复制（冲锋可打脸，突袭仅解场，普通随从召唤失调）。"""
    return _apply_best_minion_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        summon_copy_on_kill=True,
    )


def _apply_nightshade_tea(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """2 伤 + 自伤 2；剩余杯数>0 时由 apply_spell_sequence 回手再喝。"""
    from .spell_board import DRINKS_LEFT

    cid = (card.card_id if card and card.card_id else "") or "VAC_404"
    drinks_before = DRINKS_LEFT.get(cid, 1)
    res = _apply_best_minion_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        card=card,
    )
    res.self_hero_damage = _sd(2, mult=mult, spell_power=spell_power)
    res.drinks_after = max(0, drinks_before - 1)
    return res


def _apply_health_drink(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """吸血 3 伤；剩余杯数>0 时回手再喝（无自伤）。"""
    from .spell_board import DRINKS_LEFT

    cid = (card.card_id if card and card.card_id else "") or "VAC_951"
    drinks_before = DRINKS_LEFT.get(cid, 1)
    res = _apply_best_minion_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        self_lifesteal=True,
        card=card,
    )
    res.drinks_after = max(0, drinks_before - 1)
    return res


SHADELEAF_BOTTLE_ID = "WW_393t"
SHADELEAF_BOTTLE_IDS = frozenset({SHADELEAF_BOTTLE_ID})


def _stored_spell_damage(card, default: int = 0) -> int:
    """手牌瓶子：模拟 stored_damage；日志里为 TAG_SCRIPT_DATA_NUM_1。"""
    if card is None:
        return default
    stored = getattr(card, "stored_damage", None)
    if stored is not None and int(stored) > 0:
        return int(stored)
    tags = getattr(card, "tags", None) or {}
    for key in ("TAG_SCRIPT_DATA_NUM_1", "STORED_DAMAGE"):
        tag = tags.get(key)
        if tag is not None and int(tag) > 0:
            return int(tag)
    return default


def _apply_invasive_shadeleaf(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """10 伤（随从）；溢出置 1 费瓶子，伤害=溢出值，由 apply_spell_sequence 同回合续施。"""
    amount = _sd(10, mult=mult, spell_power=spell_power)
    if amount <= 0:
        return SpellApplyResult()

    best_score = -1
    best_idx: Optional[int] = None

    for i in _iter_spell_minion_target_indices(taunts, card=card):
        t = taunts[i]
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == t.get("entity_id")),
            ts[i],
        )
        _, _, dealt = _apply_damage_to_unit(
            target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        _remove_dead_taunts(ts)
        overflow = max(0, amount - dealt)
        if overflow > 0:
            _apply_best_minion_damage(
                ts, fs, overflow, enemy_shield=enemy_shield, card=card,
            )
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return SpellApplyResult()

    res = SpellApplyResult()
    target = taunts[best_idx]
    heal, _, dealt = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    overflow = max(0, amount - dealt)
    if overflow > 0:
        res.add_hand_spell_id = SHADELEAF_BOTTLE_ID
        res.add_hand_spell_damage = overflow
    _remove_dead_taunts(taunts)
    return res


def _apply_shadeleaf_bottle(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """瓶装影叶 WW_393t：对敌方随从造成等于存储伤害的伤。"""
    dmg = _stored_spell_damage(card) * mult
    if dmg <= 0:
        return SpellApplyResult()
    return _apply_best_minion_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )


def _apply_flame_chain(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """2 伤；打出后将链上下一张法术置入手牌（由 apply_spell_sequence 继续施放）。"""
    from .spell_board import FLAME_CHAIN_NEXT

    cid = (card.card_id if card and card.card_id else "") or "CORE_SW_108"
    res = _apply_best_minion_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        card=card,
    )
    next_id = FLAME_CHAIN_NEXT.get(cid)
    if next_id:
        res.add_hand_spell_id = next_id
    return res


def _register_p0_minion() -> None:
    specs: List[tuple] = [
        # (card_ids, cost, name, apply_fn, uses_random, cost_fn?)
        (("DAL_716",), 4, "宿敌", _minion_damage_fn(4), False, _vendetta_cost),
        (("REV_939",), 2, "锯齿骨刺", _minion_damage_fn(3), False, None),
        (("FIR_939",), 2, "影焰晕染", _optimal_damage_fn(2), False, None),
        (("CATA_585",), 1, "烈火炙烤", _apply_torch, False, None),
        (("WW_354",), 1, "残骸遍野", _apply_fistful_of_corpses, False, None),
        (("ETC_394",), 1, "混乱品味", _minion_damage_fn(2), False, None),
        (("RLK_018",), 2, "凋零打击", _minion_damage_fn(3, summon_on_kill=(2, 2, True)), False, None),
        (("TIME_750",), 2, "先行打击", _optimal_damage_fn(3), False, None),
        (("GDB_902",), 3, "潜入", _apply_infiltrate, False, None),
        (("EDR_813",), 1, "病变虫群", _apply_morbid_swarm, False, None),
        (("WW_393",), 4, "影叶入侵", _apply_invasive_shadeleaf, False, None),
        (("WW_393t",), 1, "影叶瓶子", _apply_shadeleaf_bottle, False, None),
        (("CORE_EX1_259",), 3, "闪电风暴", _apply_lightning_storm, False, None),
        (("CORE_EX1_391",), 1, "猛击", _minion_damage_fn(2), False, None),
        (("REV_249",), 1, "炽燃圣光", _apply_light_it_burns, False, None),
        (("TIME_702",), 2, "潮起潮落", _optimal_damage_fn(3), False, None),
        (("TSC_932",), 6, "血染大海", _apply_blood_in_the_water, False, None),
        (("EDR_460",), 3, "新月祈愿", _minion_damage_fn(6), False, None),
        (("CATA_533",), 5, "涣漫洪流", _apply_flash_flood, False, None),
        (("WORK_014",), 2, "恶魔交易", _minion_damage_fn(4, self_lifesteal=True), False, None),
        (("GDB_460",), 2, "神圣之星", _minion_damage_fn(3), False, None),
        (("VAC_404", "VAC_404t1", "VAC_404t2"), 1, "夜影花茶", _apply_nightshade_tea, False, None),
        (("ULD_714",), 2, "苦修", _minion_damage_fn(3, self_lifesteal=True), False, None),
        (("KAR_076",), 7, "火焰之地传送门", _optimal_damage_fn(6), False, None),
        (("VAC_951", "VAC_951t", "VAC_951t2"), 3, "健康饮品", _apply_health_drink, False, None),
        (("SW_090",), 1, "纳斯雷兹姆之触", _minion_damage_fn(2), False, None),
        (("TIME_216",), 3, "新生闪电", _minion_damage_fn(5), False, None),
        (("FIR_954",), 1, "焚烧", _minion_damage_fn(5), False, None),
        (("UNG_955",), 6, "陨石术", _apply_meteor, False, None),
        (("CORE_SW_108", "SW_108", "SW_108t"), 1, "初始之火", _apply_flame_chain, False, None),
        (("DED_517",), 5, "奥术溢爆", _minion_damage_fn(8), False, None),
        (("TLC_901",), 2, "烟雾熏蒸", _apply_fumigate, False, None),
        (("CATA_978",), 5, "辛达苟萨的胜利", _minion_damage_fn(8), False, None),
        (("SCH_512",), 6, "通窍", _apply_initiation, False, None),
        # 逃离紫罗兰堡 / DK：点解嘲讽，避免硬核信徒等战吼被挪去清嘲
        (("JAIL_441",), 2, "饮血术", _minion_damage_fn(3, self_lifesteal=True), False, None),
        (("RLK_024",), 4, "灵界打击", _minion_damage_fn(6, self_lifesteal=True), False, None),
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


_register_p0_minion()
