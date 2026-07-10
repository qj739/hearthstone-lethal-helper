# spell_p0_aoe.py — P0 第三阶段：复杂 AOE 法术（33 张）

from __future__ import annotations

import random
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_enemies_damage,
    _apply_all_minions_aoe_spell,
    _apply_best_minion_damage,
    _apply_bladestorm,
    _apply_damage,
    _apply_defile,
    _apply_enemy_minions_aoe,
    _apply_optimal_single_target_damage,
    _apply_random_split_damage,
    _add_temp_hero_attack,
    pick_judge_unworthy_target,
    _living_enemy_board_minions,
    _register,
    _remove_dead_taunts,
    _snapshot_health,
    _summon_friendly_fighter,
    _any_death_since,
    _friendly_minions,
    hand_effect_active,
    spell_script_damage,
    unit_is_dragon,
)

if TYPE_CHECKING:
    from .power_parser import GameState

MC_DEFAULT_SEED = 0

CONDEMN_DAMAGE = {
    "BAR_314": 1,
    "BAR_915": 2,
    "BAR_916": 3,
}


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _enemy_minions_aoe(dmg: int, spell_power=0) -> Callable:
    def fn(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw):
        return _apply_enemy_minions_aoe(
            taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        )
    return fn


def _all_enemies_aoe(dmg: int, spell_power=0) -> Callable:
    def fn(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw):
        return _apply_all_enemies_damage(
            taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        )
    return fn


def _all_minions_aoe(dmg: int, spell_power=0) -> Callable:
    def fn(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw):
        return _apply_all_minions_aoe_spell(taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power))
    return fn


def _apply_condemn(taunts, fighters, *, mult, enemy_shield, card=None, gs=None, player_id=None, spell_power=0, **_kw,) -> SpellApplyResult:
    cid = (card.card_id if card and card.card_id else "") or "BAR_314"
    if cid == "BAR_314" and gs is not None and player_id is not None:
        from .spell_board import condemn_card_id_for_max_mana, max_mana_crystals_for_spells

        cid = condemn_card_id_for_max_mana(max_mana_crystals_for_spells(gs, player_id))
    dmg = CONDEMN_DAMAGE.get(cid, 1)
    return _apply_enemy_minions_aoe(
        taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_malted_magma(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """麦芽岩浆：全体敌人 1 伤，连喝（VAC_323 衍生链）。"""
    from .spell_board import DRINKS_LEFT

    cid = (card.card_id if card and card.card_id else "") or "VAC_323"
    drinks_before = DRINKS_LEFT.get(cid, 1)
    res = _apply_all_enemies_damage(
        taunts, fighters, _sd(1, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    res.drinks_after = max(0, drinks_before - 1)
    return res


def _apply_dragonfire_potion(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """龙息药水：对除龙以外的所有随从 5 伤（含己方）。"""
    dmg = _sd(5, mult=mult, spell_power=spell_power)
    res = SpellApplyResult()
    for t in list(taunts):
        if unit_is_dragon(t):
            continue
        res.opponent_lifesteal_heal += _apply_damage(
            t, dmg, taunts=taunts, fighters=fighters,
        )
    _remove_dead_taunts(taunts)
    for f in fighters:
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        if unit_is_dragon(f):
            continue
        _apply_damage(f, dmg, taunts=taunts, fighters=fighters)
    return res


def _apply_rising_waves(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """浪潮涌起：全场 2 伤；若无死亡再 2 伤。"""
    dmg = _sd(2, mult=mult, spell_power=spell_power)
    units = _living_enemy_board_minions(taunts) + _friendly_minions(fighters)
    before = _snapshot_health(units)
    res = _apply_all_minions_aoe_spell(taunts, fighters, dmg)
    if not _any_death_since(before, taunts, fighters):
        extra = _apply_all_minions_aoe_spell(taunts, fighters, dmg)
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    return res


def _apply_dunk_tank(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """深水炸弹：4 伤可选目标；腐蚀后再对所有敌方随从 2 伤（不含英雄）。"""
    from copy import deepcopy
    from .spell_board import (
        SpellApplyResult,
        _apply_enemy_minions_aoe,
        _apply_damage_to_unit,
        _apply_direct_face,
        _can_spell_hit_enemy_face,
        _iter_spell_minion_target_indices,
        _remove_dead_taunts,
        corrupt_active,
        project_board_face_after_spell,
    )

    primary = _sd(4, mult=mult, spell_power=spell_power)
    aoe = _sd(2, mult=mult, spell_power=spell_power) if corrupt_active(card) else 0
    if primary <= 0:
        return SpellApplyResult()

    best_res = SpellApplyResult()
    best_score = -1

    def finish(ts, fs, res: SpellApplyResult) -> Tuple[SpellApplyResult, int]:
        if aoe > 0:
            extra = _apply_enemy_minions_aoe(ts, fs, aoe, enemy_shield=enemy_shield)
            res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
        _remove_dead_taunts(ts)
        score = res.direct_face_damage + project_board_face_after_spell(ts, fs, enemy_shield)
        return res, score

    if _can_spell_hit_enemy_face(taunts):
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        res = _apply_direct_face(primary, enemy_shield)
        res, score = finish(ts, fs, res)
        if score > best_score:
            best_score, best_res = score, res

    for i in _iter_spell_minion_target_indices(taunts):
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = ts[i]
        res = SpellApplyResult()
        heal, face, _ = _apply_damage_to_unit(
            target, primary, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
        _remove_dead_taunts(ts)
        res, score = finish(ts, fs, res)
        if score > best_score:
            best_score, best_res = score, res

    return best_res


def _apply_bellowing_flames(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, rng=None, **_kw) -> SpellApplyResult:
    """鼓动火焰：5 伤单目标；锻造分支再 5 随机敌方随从。"""
    res = _apply_best_minion_damage(
        taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    if hand_effect_active(card):
        extra = _apply_random_split_damage(
            taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
            rng=_rng(rng),
        )
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
        res.direct_face_damage += extra.direct_face_damage
    return res


def _apply_mortal_eradication(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    """致命诛灭：5 伤随机分配到敌方随从。"""
    return _apply_random_split_damage(
        taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        rng=_rng(rng),
    )


def _total_board_minion_health(taunts, fighters) -> int:
    """场上所有随从（含己方）当前生命总和。"""
    total = sum(t.get("health", 0) for t in taunts if t.get("health", 0) > 0)
    total += sum(
        f.get("health", 0) for f in fighters
        if f.get("kind") == "minion" and f.get("health", 0) > 0
    )
    return total


def _apply_baking_soda_volcano(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    """苏打火山：10 伤随机分配到所有随从（吸血不计己方）。

    若场上随从生命总和 <= 10×mult，不跑随机逐点分配：全部清零并吸血回满 10×mult。
    """
    cap = _sd(10, mult=mult, spell_power=spell_power)
    if _total_board_minion_health(taunts, fighters) <= cap:
        res = SpellApplyResult()
        for t in list(taunts):
            if t.get("health", 0) > 0:
                res.opponent_lifesteal_heal += _apply_damage(
                    t, t["health"], taunts=taunts, fighters=fighters,
                )
        _remove_dead_taunts(taunts)
        for f in list(fighters):
            if f.get("kind") == "minion" and f.get("health", 0) > 0:
                _apply_damage(
                    f, f["health"], taunts=taunts, fighters=fighters,
                )
        res.self_hero_heal = cap
        return res
    return _apply_random_split_damage(
        taunts, fighters, cap, enemy_shield=enemy_shield,
        rng=_rng(rng), include_friendly_minions=True,
    )


def _apply_sunset_volley(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    """夕阳漫射：10 伤随机分配到所有敌人。"""
    return _apply_random_split_damage(
        taunts, fighters, _sd(10, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        rng=_rng(rng), include_enemy_hero=True,
    )


def _apply_boneblade_flurry(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    card=None,
    rng=None,
    friendly_minion_died_this_turn: bool = False,
    **_kw,
) -> SpellApplyResult:
    """骨刃乱舞：3 伤随机分配到所有敌人；本回合友方随从死亡则再 3（亮边共 6）。"""
    wave = _sd(3, mult=mult, spell_power=spell_power)
    res = _apply_random_split_damage(
        taunts, fighters, wave, enemy_shield=enemy_shield,
        rng=_rng(rng), include_enemy_hero=True,
    )
    if hand_effect_active(card, friendly_minion_died_this_turn=friendly_minion_died_this_turn):
        extra = _apply_random_split_damage(
            taunts, fighters, wave, enemy_shield=enemy_shield,
            rng=_rng(rng), include_enemy_hero=True,
        )
        res.direct_face_damage += extra.direct_face_damage
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    return res


def _apply_hot_coals(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, gs=None, player_id=None, hero_damaged_this_turn=False, **_kw) -> SpellApplyResult:
    """炽热火炭：全体敌人 2 伤；亮边（本回合英雄受过伤）再 +1。"""
    dmg = _sd(2, mult=mult, spell_power=spell_power)
    if hand_effect_active(card, hero_damaged_this_turn=hero_damaged_this_turn):
        dmg += _sd(1, mult=mult, spell_power=spell_power)
    return _apply_all_enemies_damage(taunts, fighters, dmg, enemy_shield=enemy_shield)


def _apply_sanitize(taunts, fighters, *, mult, enemy_shield, spell_power=0, gs=None, player_id=None, **_kw) -> SpellApplyResult:
    """清理污染：对所有随从造成等同于护甲的伤害。"""
    armor = 0
    if gs is not None and player_id is not None:
        hero = gs.get_hero(player_id)
        if hero:
            armor = int(hero.tags.get("ARMOR", 0) or 0)
    dmg = _sd(armor, mult=mult, spell_power=spell_power)
    if dmg <= 0:
        return SpellApplyResult()
    return _apply_all_minions_aoe_spell(taunts, fighters, dmg)


def _apply_frostwyrms_fury(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """冰霜巨龙之怒：全体敌人 5 伤 + 召唤 5/5 突袭。"""
    res = _apply_all_enemies_damage(
        taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    _summon_friendly_fighter(fighters, 5, 5, rush=True)
    return res


def _apply_judge_unworthy(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """审判恶徒：将一个敌方随从变为 1 血，再全体敌人 1 伤。须有敌方随从方可使用。"""
    target = pick_judge_unworthy_target(taunts)
    if target is None:
        return SpellApplyResult()
    if target.get("shield"):
        target["shield"] = False
    target["health"] = 1
    return _apply_all_enemies_damage(
        taunts, fighters, _sd(1, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_arcane_flow_single_taunt_or_face(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """奥术涌流单段：仅嘲讽随从或英雄脸（无嘲讽时不点非嘲讽随从）。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_arcane_flow_combined(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """奥术涌流（合体/完整裂变）：4 伤嘲讽或脸 + 全体敌人 2 伤。"""
    res = _apply_arcane_flow_single_taunt_or_face(
        taunts, fighters, mult=mult, enemy_shield=enemy_shield,
    )
    extra = _apply_all_enemies_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    res.direct_face_damage += extra.direct_face_damage
    return res


def _apply_arcane_flow_shattered_aoe(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """奥术涌流（碎裂·AOE 段）：全体敌人 2 伤。"""
    return _apply_all_enemies_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_sylvanas_triumph(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """希尔瓦娜斯的胜利：3 伤（简化：单目标最优）。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_experimental_animation(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """试验演示：全体敌方随从 4 伤（兆示/POWERED_UP 不改变伤害）。"""
    return _apply_enemy_minions_aoe(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_avatar_form(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """天神下凡形态：场攻向简化，不计入直伤。"""
    return SpellApplyResult()


def _apply_crescendo(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """渐强声浪：疲劳伤害（无疲劳数据时不计入）。"""
    return SpellApplyResult()


def _battlefield_minion_count(taunts: List[dict], fighters: List[dict]) -> int:
    return (
        len(_living_enemy_board_minions(taunts))
        + len(_friendly_minions(fighters))
    )


def _apply_decimation(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """屠灭：对所有随从造成等同于场上随从数量的伤害（TAG_SCRIPT / 实时场面）。"""
    live = _battlefield_minion_count(taunts, fighters)
    base = spell_script_damage(card, default=live if live > 0 else 1)
    if live > 0:
        base = max(base, live)
    dmg = max(1, base) * mult
    return _apply_all_minions_aoe_spell(taunts, fighters, dmg)


# 混搭狂想曲：手牌中每回合随机变为下列 id 之一（HJSON）
REMIXED_RHAPSODY_IDS = (
    "JAM_018",    # 混搭狂想曲（基础）
    "JAM_018t",   # 盛怒狂想曲：抽 3（场攻同 3 伤 AOE）
    "JAM_018t2",  # 高亢狂想曲：3 伤 ×2
    "JAM_018t3",  # 动情狂想曲：3 伤 + 英雄 +5 攻
    "JAM_018t4",  # 哀嚎狂想曲：3 伤 + 召唤 5/5
)


def _apply_remixed_rhapsody(taunts, fighters, *, mult, enemy_shield, card=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """混搭狂想曲及手牌衍生形态。"""
    cid = (card.card_id if card and card.card_id else "") or "JAM_018"
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    res = _apply_all_minions_aoe_spell(taunts, fighters, dmg)
    if cid == "JAM_018t2":
        extra = _apply_all_minions_aoe_spell(taunts, fighters, dmg)
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    elif cid == "JAM_018t3":
        _add_temp_hero_attack(fighters, _sd(5, mult=mult, spell_power=spell_power))
    elif cid == "JAM_018t4":
        _summon_friendly_fighter(fighters, 5, 5)
    return res


def _register_p0_aoe() -> None:
    specs: List[tuple] = [
        # (card_ids, cost, name, apply_fn, uses_random, cost_fn?)
        (("EX1_129",), 2, "刀扇", _enemy_minions_aoe(1), False, None),
        (("CATA_156",), 6, "试验演示", _apply_experimental_animation, False, None),
        (("VAC_323",), 1, "麦芽岩浆", _apply_malted_magma, False, None),
        (("VAC_323t", "VAC_323t1"), 2, "麦芽岩浆", _apply_malted_magma, False, None),
        (("VAC_323t2",), 2, "麦芽岩浆", _apply_malted_magma, False, None),
        (("RLK_709",), 4, "冷酷严冬", _all_enemies_aoe(2), False, None),
        (("TTN_753",), 3, "鼓动火焰", _apply_bellowing_flames, False, None),
        (("GDB_445",), 6, "陨石风暴", _all_minions_aoe(5), False, None),
        (("CATA_582",), 2, "灼热裂隙", _all_minions_aoe(1), False, None),
        (("JAM_018", "JAM_018t", "JAM_018t2", "JAM_018t3", "JAM_018t4"), 5, "混搭狂想曲", _apply_remixed_rhapsody, False, None),
        (("CORE_CS1_112",), 3, "神圣新星", _enemy_minions_aoe(2), False, None),
        (("TOY_500",), 4, "苏打火山", _apply_baking_soda_volcano, True, None),
        (("BAR_314", "BAR_915", "BAR_916"), 2, "罪罚", _apply_condemn, False, None),
        (("VAC_414",), 3, "炽热火炭", _apply_hot_coals, False, None),
        (("ICC_041",), 2, "亵渎", _apply_defile, False, None),
        (("WW_427",), 9, "夕阳漫射", _apply_sunset_volley, True, None),
        (("TIME_215",), 2, "雷霆动地", _all_minions_aoe(1), False, None),
        (("TIME_619t2",), 3, "赞达拉惨象", _all_enemies_aoe(2), False, None),
        (("TTN_460",), 3, "致命诛灭", _apply_mortal_eradication, True, None),
        (("JAIL_445",), 2, "骨刃乱舞", _apply_boneblade_flurry, True, None),
        (("DMF_701", "DMF_701t"), 4, "深水炸弹", _apply_dunk_tank, False, None),
        (("SW_107",), 4, "火热促销", _all_minions_aoe(3), False, None),
        (("CATA_489",), 4, "奥术涌流", _apply_arcane_flow_combined, False, None),
        (("CATA_489t",), 4, "奥术涌流·碎裂单点", _apply_arcane_flow_single_taunt_or_face, False, None),
        (("CATA_489t2",), 4, "奥术涌流·碎裂AOE", _apply_arcane_flow_shattered_aoe, False, None),
        (("TIME_209t2",), 3, "天神下凡形态", _apply_avatar_form, False, None),
        (("VAC_953",), 3, "浪潮涌起", _apply_rising_waves, False, None),
        (("ETC_069",), 2, "渐强声浪", _apply_crescendo, False, None),
        (("RLK_063",), 7, "冰霜巨龙之怒", _apply_frostwyrms_fury, False, None),
        (("CFM_662",), 5, "龙息药水", _apply_dragonfire_potion, False, None),
        (("GDB_305",), 5, "阳炎耀斑", _all_enemies_aoe(2), False, None),
        (("CORE_CS2_093",), 3, "奉献", _all_enemies_aoe(2), False, None),
        (("BT_117",), 2, "剑刃风暴", _apply_bladestorm, False, None),
        (("YOG_502",), 4, "清理污染", _apply_sanitize, False, None),
        (("ETC_314",), 6, "悦耳流行歌", _all_minions_aoe(3), False, None),
        (("CATA_557",), 2, "希尔瓦娜斯胜利", _apply_sylvanas_triumph, False, None),
        (("TTN_853",), 4, "审判恶徒", _apply_judge_unworthy, False, None),
        (("CORE_CS2_028",), 6, "暴风雪", _enemy_minions_aoe(2), False, None),
        (("CATA_581",), 6, "屠灭", _apply_decimation, False, None),
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


_register_p0_aoe()
