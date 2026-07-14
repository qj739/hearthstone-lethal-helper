# spell_p0_direct.py — P0 第一阶段直伤法术（仿月亮井 BoardSpellDef 注册）

from __future__ import annotations

import random
from copy import deepcopy
from typing import List, Optional

from .combat_sim import project_board_face_after_spell
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_damage,
    _apply_damage_to_unit,
    _apply_direct_face,
    _apply_hellfire,
    _apply_lowest_enemy_hits,
    _apply_optimal_single_target_damage,
    _apply_random_enemy_hits,
    _apply_random_minion_hits,
    _apply_split_to_lowest,
    _apply_targeted_minion,
    _living_enemy_taunts,
    _register,
    _remove_dead_taunts,
    _target_key,
    hand_effect_active,
    spell_script_damage,
)
from .spell_p0_other import _mark_red_card_dormant, _red_card_projected_face

MC_DEFAULT_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


# --- 确定直伤 ---

def _apply_rite_twilight(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, card=None, combo_active=False, gs=None, player_id=None, **_kw) -> SpellApplyResult:
    dmg = 3 if hand_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ) else 2
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_wicked_stab_2(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_wicked_stab_4(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_wicked_stab_6(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(6, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_hammer_of_wrath(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_corpsicle(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """甜筒殡淇淋：2 费 3 伤，可打脸/随从。残骸≥3 时回合结束回手（同回合斩杀只计一次 3 伤）。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_grish_stinger(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """格里什毒刺虫：2 伤 + 2/1 突袭衍生物（当回合仅解场）。"""
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    from .spell_board import _summon_friendly_fighter
    for _ in range(mult):
        _summon_friendly_fighter(fighters, 2, 1, rush=True, card_id="TLC_630t")
    return res


def _apply_frostbite(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_glacial_advance(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(4, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_bash(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_siphon_mana(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_arcane_arrow(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None,
    gs=None, player_id=None, card=None, **_kw,
) -> SpellApplyResult:
    """奥术箭 RLK_843：2 伤；法力渴求(8 水晶) 3 伤。"""
    from .spell_board import manathirst_spell_face_damage
    cid = (getattr(card, "card_id", None) or "") if card else "RLK_843"
    dmg = manathirst_spell_face_damage(cid, gs, player_id, card=card) or 2
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _frozen_touch_infused(card) -> bool:
    """注能完成（REV_601t 或 REV_601 亮边）。"""
    if card is None:
        return False
    cid = getattr(card, "card_id", None) or ""
    if cid == "REV_601t":
        return True
    if cid == "REV_601" and card.tags.get("POWERED_UP") == 1:
        return True
    return False


def _apply_frozen_touch(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, rng=None, **_kw) -> SpellApplyResult:
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    if _frozen_touch_infused(card):
        # 注能后打出：将一张未注能冰冻之触置入手牌，本回合可再打一次
        res.add_hand_spell_id = "REV_601"
    return res


def _apply_timestop(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


# --- 最低生命值敌人（确定分配）---

def _apply_arcane_shot(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """奥术射击：对一个敌人造成 2 点伤害。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_fireball(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(6, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_swipe(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """横扫：主目标 4 伤，其余敌人各 1 伤（无嘲讽打脸 4）。"""
    from copy import deepcopy
    from .spell_board import (
        SpellApplyResult,
        _apply_damage_to_unit,
        _can_spell_hit_enemy_face,
        _iter_spell_minion_target_indices,
        _remove_dead_taunts,
        apply_divine_shield_to_hits,
        project_board_face_after_spell,
    )

    primary = _sd(4, mult=mult, spell_power=spell_power)
    splash = _sd(1, mult=mult, spell_power=spell_power)
    if primary <= 0:
        return SpellApplyResult()

    best_res = SpellApplyResult()
    best_score = -1

    def splash_other_enemies(ts, fs, *, skip_hero: bool, skip_eid):
        extra = SpellApplyResult()
        if not skip_hero:
            extra.direct_face_damage += apply_divine_shield_to_hits([splash], enemy_shield)
        for t in ts:
            if t.get("health", 0) <= 0:
                continue
            if skip_eid is not None and t.get("entity_id") == skip_eid:
                continue
            heal, face, _ = _apply_damage_to_unit(
                t, splash, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
            )
            extra.opponent_lifesteal_heal += heal
            extra.direct_face_damage += face
        return extra

    if _can_spell_hit_enemy_face(taunts):
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        res = SpellApplyResult(
            direct_face_damage=apply_divine_shield_to_hits([primary], enemy_shield),
        )
        extra = splash_other_enemies(ts, fs, skip_hero=True, skip_eid=None)
        res.direct_face_damage += extra.direct_face_damage
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
        _remove_dead_taunts(ts)
        score = res.direct_face_damage + project_board_face_after_spell(ts, fs, enemy_shield)
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
        extra = splash_other_enemies(
            ts, fs, skip_hero=False, skip_eid=target.get("entity_id"),
        )
        res.direct_face_damage += extra.direct_face_damage
        res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
        _remove_dead_taunts(ts)
        score = res.direct_face_damage + project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score, best_res = score, res

    return best_res


def _apply_fel_barrage(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_lowest_enemy_hits(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), hits=2,
        enemy_shield=enemy_shield, **_kw,
    )


def _apply_fan_the_hammer(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_split_to_lowest(
        taunts, fighters, _sd(6, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_lava_flow(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_lowest_enemy_hits(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), hits=3,
        enemy_shield=enemy_shield, **_kw,
    )


def _apply_renewing_flames(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_lowest_enemy_hits(
        taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), hits=2,
        enemy_shield=enemy_shield, self_lifesteal=True, **_kw,
    )


# --- 随机 ---

def _apply_consumption(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_random_minion_hits(
        taunts, fighters, hits=2, damage=_sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _pick_arcane_barrage_primary(taunts, *, prefer_taunt: bool = True):
    """主目标 3 伤：有嘲讽时优先打嘲讽；无嘲讽时主目标打脸。"""
    living = [
        t for t in taunts
        if t.get("health", 0) > 0 and not t.get("spell_immune")
    ]
    if not living:
        return None
    if prefer_taunt:
        taunts_only = [t for t in living if t.get("taunt")]
        if taunts_only:
            return max(taunts_only, key=lambda t: (t.get("health", 0), t.get("atk", 0)))
        return None
    return max(living, key=lambda t: (t.get("health", 0), t.get("atk", 0)))


def _apply_arcane_barrage(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    r = _rng(rng)
    dmg3 = _sd(3, mult=mult, spell_power=spell_power)
    primary = _pick_arcane_barrage_primary(taunts)
    res = SpellApplyResult()
    if primary is None:
        res = _apply_direct_face(dmg3, enemy_shield)
        primary_key = ("hero",)
    else:
        heal, face, _ = _apply_damage_to_unit(
            primary, dmg3, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal = heal
        res.direct_face_damage = face
        _remove_dead_taunts(taunts)
        primary_key = _target_key(primary)
    extra = _apply_random_enemy_hits(
        taunts, fighters, hits=2, damage=_sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        rng=r, distinct_targets=True, exclude_keys={primary_key},
    )
    res.direct_face_damage += extra.direct_face_damage
    res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    return res


def _apply_astral_phaser(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    rng=None,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """
    星域相变射线：抉择 — 随机两随从 2 伤，或使一个敌方随从休眠 2 回合。
    有嘲讽时评估休眠分支（与红牌一致，优选解嘲后场面打脸更高的一侧）。
    """
    r = _rng(rng)
    dmg = _sd(2, mult=mult, spell_power=spell_power)

    ts_d = deepcopy(taunts)
    fs_d = deepcopy(fighters)
    dmg_res = _apply_random_minion_hits(
        ts_d, fs_d, hits=2, damage=dmg, enemy_shield=enemy_shield, rng=r,
    )
    dmg_score = dmg_res.direct_face_damage + (
        project_board_face_after_spell(ts_d, fs_d, enemy_shield) or 0
    )

    dormant_score = -1.0
    best_eid = None
    for m in _living_enemy_taunts(taunts):
        eid = m.get("entity_id")
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == eid and x.get("health", 0) > 0),
            None,
        )
        if target is None:
            continue
        _mark_red_card_dormant(target, friendly=False)
        score = _red_card_projected_face(
            ts, fs, enemy_shield=enemy_shield, gs=gs, player_id=player_id,
        )
        if score > dormant_score:
            dormant_score = score
            best_eid = eid

    if best_eid is not None and dormant_score > dmg_score:
        target = next(
            (x for x in taunts if x.get("entity_id") == best_eid and x.get("health", 0) > 0),
            None,
        )
        if target is not None:
            _mark_red_card_dormant(target, friendly=False)
        return SpellApplyResult()

    return _apply_random_minion_hits(
        taunts, fighters, hits=2, damage=dmg, enemy_shield=enemy_shield, rng=r,
    )


def _apply_sleet_storm(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    res = _apply_direct_face(_sd(2, mult=mult, spell_power=spell_power), enemy_shield)
    extra = _apply_random_minion_hits(
        taunts, fighters, hits=1, damage=_sd(1, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield, rng=_rng(rng),
    )
    res.opponent_lifesteal_heal += extra.opponent_lifesteal_heal
    return res


def _apply_rafaams_stand(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, card=None, **_kw) -> SpellApplyResult:
    """随机对两个敌方随从造成伤害；手牌 TAG_SCRIPT_DATA_NUM_1 为当前单次伤害（默认 2）。"""
    dmg = spell_script_damage(card, default=2)
    return _apply_random_minion_hits(
        taunts, fighters, hits=2, damage=_sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_bursting_shot(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_random_enemy_hits(
        taunts, fighters, hits=3, damage=_sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        rng=_rng(rng), distinct_targets=True,
    )


def _apply_scorching_winds(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, card=None, **_kw) -> SpellApplyResult:
    """灼烧之风：3 伤；亮边（手牌有火焰法术可弃）再 +3。"""
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    if hand_effect_active(card):
        dmg += _sd(3, mult=mult, spell_power=spell_power)
    return _apply_optimal_single_target_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )


def _apply_star_power(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    r = _rng(rng)
    total = SpellApplyResult()
    for dmg in (5, 4, 3, 2, 1):
        part = _apply_random_minion_hits(
            taunts, fighters, hits=1, damage=_sd(dmg, mult=mult, spell_power=spell_power),
            enemy_shield=enemy_shield, rng=r,
        )
        total.opponent_lifesteal_heal += part.opponent_lifesteal_heal
        total.direct_face_damage += part.direct_face_damage
    return total


# --- 解场向（仅随从）---

def _apply_purifying_breath(taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw) -> SpellApplyResult:
    return _apply_targeted_minion(
        taunts, fighters, _sd(5, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        heal_enemy_on_kill=_sd(5, mult=mult, spell_power=spell_power),
        **_kw,
    )


def _apply_dragon_breath(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """龙息 CATA_464t：黑翼实验品亡语衍生，伤害=TAG_SCRIPT_DATA_NUM_1（等于其攻击力）。"""
    dmg = max(1, spell_script_damage(card, 1)) * mult
    return _apply_optimal_single_target_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )


def _apply_climactic_necrotic_explosion(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    card=None,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """通灵最强音：脚本伤害（TAG_SCRIPT_DATA_NUM_1，随消耗残骸提升）+ 吸血。"""
    raw = spell_script_damage(card, default=0, gs=gs, player_id=player_id)
    dmg = _sd(raw, mult=mult, spell_power=spell_power)
    if dmg <= 0:
        return SpellApplyResult()
    res = _apply_optimal_single_target_damage(
        taunts, fighters, dmg, enemy_shield=enemy_shield,
    )
    if res.direct_face_damage > 0:
        res.self_hero_heal = res.direct_face_damage
    else:
        res.self_hero_heal = dmg
    return res


def _register_p0_direct() -> None:
    specs: List[tuple] = [
        (("CATA_785",), 2, "暮光祭礼", _apply_rite_twilight, False),
        (("BAR_319",), 2, "邪恶挥刺", _apply_wicked_stab_2, False),
        (("BAR_319t", "BAR_920"), 2, "邪恶挥刺", _apply_wicked_stab_4, False),
        (("BAR_319t2", "BAR_921"), 2, "邪恶挥刺", _apply_wicked_stab_6, False),
        (("CS2_094", "CORE_CS2_094"), 3, "愤怒之锤", _apply_hammer_of_wrath, False),
        (("TLC_630t",), 1, "格里什毒刺虫", _apply_grish_stinger, False),
        (("CORE_CATA_007",), 4, "吞噬", _apply_consumption, True),
        (("AV_259",), 2, "冰霜撕咬", _apply_frostbite, False),
        (("RLK_512",), 3, "冰川突进", _apply_glacial_advance, False),
        (("SW_040",), 2, "邪能弹幕", _apply_fel_barrage, False),
        (("CORE_AT_064",), 2, "怒袭", _apply_bash, False),
        (("CORE_CS2_062",), 3, "地狱烈焰", _apply_hellfire, False),
        (("WW_405",), 4, "迅疾连射", _apply_fan_the_hammer, False),
        (("TIME_855",), 3, "奥术弹幕", _apply_arcane_barrage, True),
        (("GDB_851",), 2, "星域相变射线", _apply_astral_phaser, True),
        (("CATA_485",), 1, "激寒急流", _apply_sleet_storm, True),
        (("CATA_498",), 3, "拉法姆的奋战", _apply_rafaams_stand, True),
        (("CATA_303",), 2, "净化吐息", _apply_purifying_breath, False),
        (("TIME_611",), 2, "时间停滞", _apply_timestop, False),
        (("DS1_185", "CORE_DS1_185"), 1, "奥术射击", _apply_arcane_shot, False),
        (("CS2_029", "CORE_CS2_029"), 4, "火球术", _apply_fireball, False),
        (("CS2_012", "CORE_CS2_012"), 3, "横扫", _apply_swipe, False),
        (("FIR_909",), 2, "爆裂射击", _apply_bursting_shot, True),
        (("FIR_910",), 3, "灼烧之风", _apply_scorching_winds, False),
        (("TLC_227",), 3, "熔岩涌流", _apply_lava_flow, False),
        (("EDR_255",), 7, "复苏烈焰", _apply_renewing_flames, False),
        (("JAM_002",), 5, "星辰能量", _apply_star_power, True),
        (("AV_212",), 2, "法力虹吸", _apply_siphon_mana, False),
        (("RLK_843",), 1, "奥术箭", _apply_arcane_arrow, False),
        (("VAC_427",), 2, "甜筒殡淇淋", _apply_corpsicle, False),
        (("REV_601", "REV_601t"), 2, "冰冻之触", _apply_frozen_touch, False),
        (("CATA_464t",), 2, "龙息", _apply_dragon_breath, False),
        (("ETC_210",), 10, "通灵最强音", _apply_climactic_necrotic_explosion, False),
    ]
    for card_ids, cost, name, fn, uses_random in specs:
        _register(
            BoardSpellDef(
                card_ids=card_ids,
                base_cost=cost,
                name=name,
                apply=fn,
                uses_random=uses_random,
            )
        )


_register_p0_direct()
