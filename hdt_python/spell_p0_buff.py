# spell_p0_buff.py — P0 第五阶段：加攻 / 武器 / 降血（6 张）

from __future__ import annotations

from typing import List

from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _add_temp_hero_attack,
    _apply_buff_to_spell_target,
    _apply_optimal_single_target_damage,
    _friendly_minion_count,
    _pick_best_spell_target_fighter,
    _register,
    _summon_friendly_fighter,
)


def _set_enemy_minions_health(taunts: List[dict], health: int) -> None:
    """将敌方随从生命值设为指定值（保留攻击力等；圣盾先破盾）。"""
    hp = max(1, int(health))
    for unit in taunts:
        if unit.get("health", 0) <= 0 or unit.get("kind") == "hero":
            continue
        if unit.get("shield"):
            unit["shield"] = False
        unit["health"] = hp
        if "max_health" in unit:
            unit["max_health"] = hp


def _set_all_minions_health(taunts: List[dict], fighters: List[dict], health: int) -> None:
    """将双方随从生命值设为指定值（生而平等）。"""
    _set_enemy_minions_health(taunts, health)
    hp = max(1, int(health))
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        fighters[i] = dict(f)
        if fighters[i].get("shield"):
            fighters[i]["shield"] = False
        fighters[i]["health"] = hp
        if "max_health" in fighters[i]:
            fighters[i]["max_health"] = hp


def _apply_equality(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """生而平等：将所有随从的生命值变为 1。"""
    _set_all_minions_health(taunts, fighters, 1)
    return SpellApplyResult()


def _buff_equipped_weapon(fighters: List[dict], bonus_atk: int) -> None:
    """给已装备且可参与攻击模拟的武器 +攻（无武器则无效）。"""
    bonus = max(0, int(bonus_atk))
    if bonus <= 0:
        return
    for i, f in enumerate(fighters):
        if f.get("kind") == "weapon" and f.get("health", 0) > 0:
            fighters[i] = dict(f)
            fighters[i]["atk"] = fighters[i].get("atk", 0) + bonus
            return


def _apply_hip_hop(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    card=None,
    **_kw,
) -> SpellApplyResult:
    """悦耳嘻哈 / 刺耳嘻哈：直伤 + 武器加攻（每回合切换形态）。"""
    cid = (card.card_id if card and card.card_id else "") or "ETC_717"
    if cid == "ETC_717t":
        dmg, weapon_bonus = 3, 1
    else:
        dmg, weapon_bonus = 1, 3
    res = _apply_optimal_single_target_damage(
        taunts,
        fighters,
        _sd(dmg, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )
    _buff_equipped_weapon(
        fighters,
        _sd(weapon_bonus, mult=mult, spell_power=spell_power),
    )
    return res


def _apply_chaos_strike(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    _add_temp_hero_attack(fighters, _sd(2, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _apply_punch_card(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """打卡：+3 攻（顺劈 v1 不模拟）。"""
    _add_temp_hero_attack(fighters, _sd(3, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _apply_verse_riff(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """主歌乐句：+2 攻（护甲 / 压轴复奏 v1 不模拟）。"""
    _add_temp_hero_attack(fighters, _sd(2, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _apply_libram_of_justice(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """正义圣契：敌方随从变 1 血 + 装备 1/4 武器。"""
    _set_enemy_minions_health(taunts, 1)
    _add_temp_hero_attack(fighters, _sd(1, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _apply_dispose_of_evidence(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    _add_temp_hero_attack(fighters, _sd(3, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _apply_muster_for_battle(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """作战动员：三个 1/1 + 1/4 武器（新兵当回合失调）。"""
    for _ in range(_sd(3, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fighters, 1, 1)
    _add_temp_hero_attack(fighters, _sd(1, mult=mult, spell_power=spell_power))
    return SpellApplyResult()


def _buff_all_friendly_minions(
    fighters: List[dict],
    *,
    bonus_atk: int,
    bonus_health: int,
) -> None:
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        fighters[i] = dict(f)
        fighters[i]["atk"] = fighters[i].get("atk", 0) + bonus_atk
        fighters[i]["health"] = fighters[i].get("health", 0) + bonus_health


def _apply_forests_gift(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """森林赠礼：使一个可指定的友方随从获得你每控制一个随从的 +1/+1（跳过魔法免疫）。"""
    count = _friendly_minion_count(fighters, gs=gs, player_id=player_id)
    if count <= 0:
        return SpellApplyResult()
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    bonus = _sd(count, mult=mult, spell_power=spell_power)
    _apply_buff_to_spell_target(
        fighters, picked, bonus_atk=bonus, bonus_health=bonus,
    )
    return SpellApplyResult()


def _apply_arbor_up(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """树木生长：召唤两个 2/2 树人；使你的随从获得 +2/+1（含新树人，当回合失调）。"""
    for _ in range(_sd(2, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fighters, 2, 2)
    _buff_all_friendly_minions(
        fighters,
        bonus_atk=_sd(2, mult=mult, spell_power=spell_power),
        bonus_health=_sd(1, mult=mult, spell_power=spell_power),
    )
    return SpellApplyResult()


def _apply_flash_sale(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """光速抢购：召唤 1/2 圣盾嘲讽机械；使你的随从获得 +1/+2（含新机械，当回合失调）。"""
    _summon_friendly_fighter(
        fighters, 1, 2,
        taunt=True, divine_shield=True,
        card_id="CORE_GVG_085",
    )
    _buff_all_friendly_minions(
        fighters,
        bonus_atk=_sd(1, mult=mult, spell_power=spell_power),
        bonus_health=_sd(2, mult=mult, spell_power=spell_power),
    )
    return SpellApplyResult()


def _apply_reliable_companion(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """可靠陪伴：使一个友方随从获得 +2/+3（抽牌 v1 不模拟）。"""
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        fighters,
        picked,
        bonus_atk=_sd(2, mult=mult, spell_power=spell_power),
        bonus_health=_sd(3, mult=mult, spell_power=spell_power),
    )
    return SpellApplyResult()


def _apply_spikeridged_steed(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """剑龙骑术：使一个随从获得 +2/+6 和嘲讽（亡语召唤剑龙 v1 不模拟）。"""
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        fighters,
        picked,
        bonus_atk=_sd(2, mult=mult, spell_power=spell_power),
        bonus_health=_sd(6, mult=mult, spell_power=spell_power),
    )
    return SpellApplyResult()


def _apply_banana_bunch(
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
    """一串香蕉：友方随从 +1/+1，回手可再打（共 3 根）；跳过魔法免疫/扰魔友方。"""
    from .spell_board import DRINKS_LEFT

    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        fighters,
        picked,
        bonus_atk=_sd(1, mult=mult, spell_power=spell_power),
        bonus_health=_sd(1, mult=mult, spell_power=spell_power),
    )
    cid = (card.card_id if card and card.card_id else "") or "ETC_201"
    drinks_before = DRINKS_LEFT.get(cid, 1)
    res = SpellApplyResult()
    res.drinks_after = max(0, drinks_before - 1)
    return res


def _register_p0_buff() -> None:
    specs = [
        (("CORE_BT_035", "BT_035"), 2, "混乱打击", _apply_chaos_strike, False),
        (("WORK_022",), 3, "打卡", _apply_punch_card, False),
        (("ETC_363",), 1, "主歌乐句", _apply_verse_riff, False),
        (("BT_011",), 5, "正义圣契", _apply_libram_of_justice, False),
        (("REV_507",), 0, "处理证据", _apply_dispose_of_evidence, False),
        (("CORE_GVG_061",), 3, "作战动员", _apply_muster_for_battle, False),
        (("YOP_026",), 5, "树木生长", _apply_arbor_up, False),
        (("CATA_138",), 3, "森林赠礼", _apply_forests_gift, False),
        (("WW_027",), 2, "可靠陪伴", _apply_reliable_companion, False),
        (("MAW_021", "CORE_MAW_021"), 3, "问心无愧", _apply_reliable_companion, False),
        (("CORE_UNG_952", "UNG_952"), 5, "剑龙骑术", _apply_spikeridged_steed, False),
        (("TOY_716",), 4, "光速抢购", _apply_flash_sale, False),
        (("ETC_717", "ETC_717t"), 2, "悦耳嘻哈", _apply_hip_hop, False),
        (("ETC_201", "ETC_201t", "ETC_201t2"), 1, "一串香蕉", _apply_banana_bunch, False),
        (("CORE_EX1_619", "EX1_619"), 2, "生而平等", _apply_equality, False),
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


_register_p0_buff()
