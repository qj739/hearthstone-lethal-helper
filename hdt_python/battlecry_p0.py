# battlecry_p0.py — 竞技场 P0 战吼随从（64 张含泰兰德 + 吞星兽法术迸发）

from __future__ import annotations

import random
from copy import deepcopy
from typing import Callable, List, Optional, TYPE_CHECKING

from .battlecry_board import _register_bc
from .board_damage import hand_minion_attack, hand_minion_health
from .combat_sim import project_board_face_after_spell
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_enemies_damage,
    _apply_all_minions_aoe_spell,
    _apply_best_minion_damage,
    _apply_damage,
    _apply_damage_to_unit,
    _apply_damage_wave_all_minions,
    _apply_direct_face,
    _apply_enemy_minions_aoe,
    _apply_lowest_enemy_hits,
    _apply_optimal_single_target_damage,
    _apply_random_destroy_enemy_minions,
    _apply_random_enemy_hits,
    _apply_random_minion_hits,
    _apply_random_split_damage,
    _apply_split_to_lowest,
    _apply_targeted_minion,
    _can_spell_hit_enemy_face,
    _destroy_enemy_minion,
    _friendly_minions,
    _iter_spell_minion_target_indices,
    _living_enemy_board_minions,
    _living_enemy_taunts,
    _apply_buff_to_spell_target,
    _merge_spell_result,
    _pick_best_spell_target_fighter,
    _pick_lowest_unit,
    _remove_dead_taunts,
    _snapshot_health,
    _summon_friendly_fighter,
    _target_key,
    _any_death_since,
    _hero_unit,
    _add_temp_hero_attack,
    hand_effect_active,
    quickdraw_active,
    player_corpses,
    spell_script_damage,
)
from .spell_p0_remove import (
    _apply_optimal_destroy_any_minion,
    _apply_optimal_destroy_enemy,
    _apply_optimal_hex,
    _apply_optimal_silence_enemy,
    _destroy_friendly_minion,
    _hex_transform,
    _living_friendly_minions,
    _strip_enemy_minion_keywords,
)

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

MC_DEFAULT_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _hero_armor(gs: Optional["GameState"], player_id: Optional[int]) -> int:
    if gs is None or player_id is None:
        return 0
    hero = gs.get_hero(player_id)
    if not hero:
        return 0
    return int(hero.tags.get("ARMOR", 0) or 0)


def _hand_card_attack(card: Optional["Entity"], default: int) -> int:
    if card is None:
        return default
    atk = getattr(card, "atk", 0) or card.tags.get("ATK", 0)
    return int(atk) if int(atk) > 0 else default


def _living_by_zone(taunts: List[dict]) -> List[dict]:
    living = [
        t for t in taunts
        if t.get("health", 0) > 0 and not t.get("spell_immune")
    ]
    return sorted(living, key=lambda t: int(t.get("zone_pos", 0) or 0))


def _flash_flood_once(
    taunts: List[dict],
    fighters: List[dict],
    dmg: int,
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
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


def _iter_battlecry_enemy_minion_indices(taunts: List[dict]) -> List[int]:
    """战吼可选的敌方随从（不受嘲讽限制；休眠/魔免不可点）。"""
    from .combat_sim import unit_is_active_minion

    out: List[int] = []
    for i, t in enumerate(taunts):
        if not unit_is_active_minion(t):
            continue
        if t.get("spell_immune"):
            continue
        out.append(i)
    return out


def _apply_night_elf_huntress(
    taunts: List[dict],
    fighters: List[dict],
    *,
    mult: int,
    enemy_shield: bool,
    **_kw,
) -> SpellApplyResult:
    """暗夜精灵女猎手：对三个不同敌人各 3 伤（随从/英雄均可，互不重复）。"""
    return _apply_optimal_distinct_damage(
        taunts,
        fighters,
        hits=3,
        damage=3,
        enemy_shield=enemy_shield,
        mult=mult,
        any_enemy_minion=True,
        ignore_taunt_face_block=True,
    )


def _apply_optimal_distinct_damage(
    taunts: List[dict],
    fighters: List[dict],
    *,
    hits: int,
    damage: int,
    enemy_shield: bool,
    mult: int = 1,
    any_enemy_minion: bool = False,
    ignore_taunt_face_block: bool = False,
) -> SpellApplyResult:
    """对多个不同敌人各造成固定伤害（斩杀贪心最优）。"""
    amt = max(damage * mult, 0)
    if amt <= 0:
        return SpellApplyResult()

    total = SpellApplyResult()
    used: set = set()

    for _ in range(hits):
        best_score = -1
        best_key = None
        best_apply: Optional[Callable[[], SpellApplyResult]] = None

        can_face = ignore_taunt_face_block or _can_spell_hit_enemy_face(taunts)
        if can_face and ("hero",) not in used:
            ts = deepcopy(taunts)
            fs = deepcopy(fighters)
            wave = _apply_direct_face(amt, enemy_shield)
            score = wave.direct_face_damage + project_board_face_after_spell(ts, fs, enemy_shield)
            if score > best_score:
                best_score = score
                best_key = ("hero",)
                best_apply = lambda: _apply_direct_face(amt, enemy_shield)

        if any_enemy_minion:
            target_indices = _iter_battlecry_enemy_minion_indices(taunts)
        else:
            target_indices = _iter_spell_minion_target_indices(
                taunts, allow_all_without_taunt=True,
            )

        for i in target_indices:
            key = _target_key(taunts[i])
            if key in used:
                continue
            ts = deepcopy(taunts)
            fs = deepcopy(fighters)
            target = next(
                (x for x in ts if x.get("entity_id") == taunts[i].get("entity_id")),
                ts[i],
            )
            heal, face, _ = _apply_damage_to_unit(
                target, amt, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
            )
            _remove_dead_taunts(ts)
            score = face + project_board_face_after_spell(ts, fs, enemy_shield)
            if score > best_score:
                best_score = score
                best_key = key
                eid = taunts[i].get("entity_id")

                def _apply_one(eid=eid):
                    res = SpellApplyResult()
                    for unit in taunts:
                        if unit.get("entity_id") == eid:
                            heal, face, _ = _apply_damage_to_unit(
                                unit, amt, taunts=taunts, fighters=fighters,
                                enemy_shield=enemy_shield,
                            )
                            res.opponent_lifesteal_heal += heal
                            res.direct_face_damage += face
                            break
                    _remove_dead_taunts(taunts)
                    return res

                best_apply = _apply_one

        if best_apply is None:
            break
        wave = best_apply()
        _merge_spell_result(total, wave)
        used.add(best_key)

    return total


def _apply_repeat_while_death_all_other(
    taunts: List[dict],
    fighters: List[dict],
    damage: int,
) -> SpellApplyResult:
    """话痨奥术师：全场其他随从 1 伤，有死亡则重复。"""
    total = SpellApplyResult()
    while True:
        units = _living_enemy_board_minions(taunts) + _friendly_minions(fighters)
        if not units:
            break
        before = _snapshot_health(units)
        wave = _apply_damage_wave_all_minions(taunts, fighters, damage)
        _merge_spell_result(total, wave)
        if not _any_death_since(before, taunts, fighters):
            break
    return total


def _bounce_all_enemy_minions(taunts: List[dict]) -> None:
    """移回手牌：从场面移除，不触发亡语。"""
    kept = [t for t in taunts if t.get("health", 0) <= 0 or t.get("kind") == "hero"]
    taunts[:] = kept


def _destroy_all_other_minions(taunts: List[dict], fighters: List[dict]) -> None:
    for t in list(taunts):
        if t.get("health", 0) > 0 and t.get("kind") != "hero":
            _destroy_enemy_minion(t, taunts, fighters)
    for f in list(fighters):
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            _destroy_friendly_minion(f)


def _silence_destroy_all_other(taunts: List[dict], fighters: List[dict]) -> None:
    for t in taunts:
        if t.get("health", 0) > 0 and t.get("kind") != "hero":
            _strip_enemy_minion_keywords(t)
    for f in fighters:
        if f.get("kind") == "minion" and f.get("health", 0) > 0:
            _strip_enemy_minion_keywords(f)
    _destroy_all_other_minions(taunts, fighters)


def _pick_lowest_friendly(fighters: List[dict]) -> Optional[dict]:
    friends = _friendly_minions(fighters)
    if not friends:
        return None
    return min(friends, key=lambda f: (f.get("health", 0), f.get("atk", 0)))


def _buff_lowest_friendly(
    fighters: List[dict],
    *,
    atk: int = 0,
    health: int = 0,
    taunt: bool = False,
) -> SpellApplyResult:
    target = _pick_lowest_friendly(fighters)
    if target is None:
        return SpellApplyResult()
    if atk:
        target["atk"] = target.get("atk", 0) + atk
    if health:
        target["health"] = target.get("health", 0) + health
    if taunt:
        target["taunt"] = True
    return SpellApplyResult()


def _optimal_set_minion_stats(
    taunts: List[dict],
    fighters: List[dict],
    atk: int,
    health: int,
    *,
    enemy_shield: bool,
) -> SpellApplyResult:
    """将最优随从变为指定身材（敌我皆可）。"""
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
            unit = ts[idx]
        else:
            unit = fs[idx]
        unit["atk"] = atk
        unit["health"] = health
        unit["shield"] = False
        score = project_board_face_after_spell(ts, fs, enemy_shield)
        if score > best_score:
            best_score = score
            best = (side, idx)

    if best is None:
        return SpellApplyResult()
    side, idx = best
    if side == "enemy":
        unit = taunts[idx]
    else:
        unit = fighters[idx]
    unit["atk"] = atk
    unit["health"] = health
    unit["shield"] = False
    return SpellApplyResult()


# --- 1. 直伤（22）---

def _apply_hardcore_cultist(
    t, f, *, mult, enemy_shield, card=None, finale_active=False, **_kw,
):
    if finale_active or hand_effect_active(card):
        return _apply_all_enemies_damage(t, f, 2 * mult, enemy_shield=enemy_shield)
    return _apply_optimal_single_target_damage(
        t, f, 2 * mult, enemy_shield=enemy_shield,
    )


def _apply_eulogizer(t, f, *, mult, enemy_shield, gs=None, player_id=None, **_kw):
    corpses = player_corpses(gs, player_id) if gs and player_id is not None else 3
    if corpses < 3:
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 3 * mult, enemy_shield=enemy_shield,
    )


def _apply_ball_hog(t, f, *, mult, enemy_shield, **_kw):
    return _apply_lowest_enemy_hits(
        t, f, 3 * mult, hits=1, enemy_shield=enemy_shield, self_lifesteal=True,
        **_kw,
    )


def _apply_tidal_revenant(t, f, *, mult, enemy_shield, **_kw):
    return _apply_optimal_single_target_damage(
        t, f, 5 * mult, enemy_shield=enemy_shield,
    )


def _apply_thornveil(t, f, *, mult, enemy_shield, rng=None, **_kw):
    return _apply_random_minion_hits(
        t, f, hits=1, damage=2 * mult, enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_amber_whelp(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 3 * mult, enemy_shield=enemy_shield,
    )


def _apply_bolide_behemoth(t, f, **_kw):
    return SpellApplyResult()


def _denathrius_battlecry_damage(card, *, default: int = 5) -> int:
    """
    德纳修斯大帝：无限注能后战吼总伤写在 TAG_SCRIPT_DATA_NUM_1。
    未注能/日志缺失时回退基底 5。
    """
    return spell_script_damage(card, default=default)


def _apply_sire_denathrius(t, f, *, mult, enemy_shield, rng=None, card=None, **_kw):
    """战吼：对敌人分配 N 点伤害（N 随注能增加）；含吸血。"""
    total = _denathrius_battlecry_damage(card, default=5) * mult
    if total <= 0:
        return SpellApplyResult()
    return _apply_random_split_damage(
        t, f, total, enemy_shield=enemy_shield, rng=_rng(rng),
        include_enemy_hero=True, effect_lifesteal=True,
    )


def _apply_tainted_remnant(t, f, *, mult, enemy_shield, rng=None, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_random_split_damage(
        t, f, 7 * mult, enemy_shield=enemy_shield, rng=_rng(rng),
        include_enemy_hero=True,
    )


def _apply_burrowing_scorpid(t, f, *, mult, enemy_shield, **_kw):
    return _apply_optimal_single_target_damage(
        t, f, 2 * mult, enemy_shield=enemy_shield,
    )


def _apply_stoneborn_accuser(t, f, *, mult, enemy_shield, card=None, **_kw):
    """石裔指控者：注能后 / REV_013t 战吼造成 5 点伤害。"""
    cid = (card.card_id if card is not None else "") or ""
    infused = cid in ("REV_013t",) or (
        card is not None and (
            int(card.tags.get("INFUSED", 0) or 0) == 1
            or hand_effect_active(card)
        )
    )
    if not infused:
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 5 * mult, enemy_shield=enemy_shield,
    )


def _apply_rowdy_partner(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 4 * mult, enemy_shield=enemy_shield,
    )


def _apply_slithering_deathscale(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_all_enemies_damage(t, f, 3 * mult, enemy_shield=enemy_shield)


def _apply_astalor(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 2 * mult, enemy_shield=enemy_shield,
    )


def _apply_marrow_manipulator(t, f, *, mult, enemy_shield, gs=None, player_id=None, rng=None, **_kw):
    corpses = min(player_corpses(gs, player_id) if gs and player_id is not None else 5, 5)
    if corpses <= 0:
        return SpellApplyResult()
    total = SpellApplyResult()
    roll = _rng(rng)
    for _ in range(corpses * mult):
        wave = _apply_random_enemy_hits(
            t, f, hits=1, damage=2, enemy_shield=enemy_shield, rng=roll,
        )
        _merge_spell_result(total, wave)
    return total


def _apply_nostalgic_clown(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_optimal_single_target_damage(
        t, f, 4 * mult, enemy_shield=enemy_shield,
    )


def _apply_triplewick(t, f, *, mult, enemy_shield, rng=None, **_kw):
    return _apply_random_enemy_hits(
        t, f, hits=3, damage=2 * mult, enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_skarr(t, f, *, mult, enemy_shield, card=None, **_kw):
    dmg = max(1, spell_script_damage(card, 1)) * mult
    return _apply_all_enemies_damage(t, f, dmg, enemy_shield=enemy_shield)


def _apply_conflux_crasher(t, f, *, mult, enemy_shield, rng=None, **_kw):
    return _apply_random_enemy_hits(
        t, f, hits=1, damage=7 * mult, enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_lamplighter(t, f, *, mult, enemy_shield, card=None, **_kw):
    dmg = max(1, spell_script_damage(card, 1)) * mult
    return _apply_optimal_single_target_damage(
        t, f, dmg, enemy_shield=enemy_shield,
    )


def _apply_wasteland_vanguard(t, f, *, mult, enemy_shield, rng=None, **_kw):
    roll = _rng(rng)
    units = _living_enemy_board_minions(t) + [_hero_unit(enemy_shield)]
    before = _snapshot_health(units)
    res = _apply_random_split_damage(
        t, f, 3 * mult, enemy_shield=enemy_shield, rng=roll, include_enemy_hero=True,
    )
    if _any_death_since(before, t, f):
        extra = _apply_random_split_damage(
            t, f, 3 * mult, enemy_shield=enemy_shield, rng=roll, include_enemy_hero=True,
        )
        _merge_spell_result(res, extra)
    return res


def _apply_sylvanas_ranger(t, f, *, mult, enemy_shield, **_kw):
    return _apply_all_enemies_damage(t, f, 2 * mult, enemy_shield=enemy_shield)


# --- 2. 解场伤（9）---

def _apply_latorvian_armorer(t, f, *, mult, enemy_shield, **_kw):
    return _apply_targeted_minion(t, f, 2 * mult, enemy_shield=enemy_shield)


def _apply_crows_nest(t, f, *, mult, enemy_shield, **_kw):
    return _flash_flood_once(t, f, 2 * mult, enemy_shield=enemy_shield)


def _apply_spinetail_drake(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_targeted_minion(t, f, 5 * mult, enemy_shield=enemy_shield)


def _apply_uv_breaker(t, f, *, mult, enemy_shield, **_kw):
    return _apply_targeted_minion(t, f, 3 * mult, enemy_shield=enemy_shield)


def _apply_guardian_augmerchant(t, f, *, mult, enemy_shield, **_kw):
    return _apply_targeted_minion(t, f, 1 * mult, enemy_shield=enemy_shield)


def _apply_wrathguard(t, f, *, mult, enemy_shield, **_kw):
    return _apply_targeted_minion(t, f, 2 * mult, enemy_shield=enemy_shield)


def _apply_onyxian_drake(t, f, *, mult, enemy_shield, gs=None, player_id=None, **_kw):
    dmg = _hero_armor(gs, player_id) * mult
    if dmg <= 0:
        return SpellApplyResult()
    return _apply_targeted_minion(t, f, dmg, enemy_shield=enemy_shield)


def _apply_firework_elemental(t, f, *, mult, enemy_shield, card=None, **_kw):
    dmg = 12 if hand_effect_active(card) else 3
    return _apply_best_minion_damage(
        t, f, dmg * mult, enemy_shield=enemy_shield,
    )


def _apply_fire_elemental(t, f, *, mult, enemy_shield, card=None, **_kw):
    """火元素 CS2_042：战吼造成3/4点伤害（可打脸或解嘲讽）。"""
    cid = (getattr(card, "card_id", None) or "") if card else ""
    base = 3 if cid.startswith("VAN_") else 4
    return _apply_optimal_single_target_damage(
        t, f, base * mult, enemy_shield=enemy_shield,
    )


def _apply_ebonscale_scout(t, f, *, mult, enemy_shield, card=None, **_kw):
    atk = 8 if hand_effect_active(card) else _hand_card_attack(card, 4)
    return _apply_optimal_single_target_damage(
        t, f, atk * mult, enemy_shield=enemy_shield,
    )


# --- 3. AOE（9）---

def _apply_hostile_invader(t, f, *, mult, enemy_shield, **_kw):
    return _apply_all_minions_aoe_spell(t, f, 2 * mult)


def _apply_bunker_sergeant(t, f, *, mult, enemy_shield, **_kw):
    if len(_living_enemy_board_minions(t)) < 2:
        return SpellApplyResult()
    return _apply_enemy_minions_aoe(t, f, 1 * mult, enemy_shield=enemy_shield)


def _apply_spammy_arcanist(t, f, *, mult, enemy_shield, **_kw):
    return _apply_repeat_while_death_all_other(t, f, 1 * mult)


def _apply_disposalbot(t, f, *, mult, enemy_shield, rng=None, **_kw):
    return _apply_random_split_damage(
        t, f, 5 * mult, enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_whirling_combatant(t, f, *, mult, enemy_shield, **_kw):
    return _apply_all_minions_aoe_spell(t, f, 1 * mult)


def _apply_duskbreaker(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_all_minions_aoe_spell(t, f, 3 * mult)


def _apply_blast_tortoise(t, f, *, mult, enemy_shield, card=None, **_kw):
    atk = _hand_card_attack(card, 2)
    return _apply_enemy_minions_aoe(t, f, atk * mult, enemy_shield=enemy_shield)


def _apply_earth_revenant(t, f, *, mult, enemy_shield, **_kw):
    return _apply_enemy_minions_aoe(t, f, 1 * mult, enemy_shield=enemy_shield)


def _apply_hollow_abomination(t, f, *, mult, enemy_shield, **_kw):
    return _apply_enemy_minions_aoe(t, f, 1 * mult, enemy_shield=enemy_shield)


# --- 4. 移除（16）---

def _apply_twilight_mistress(t, f, **_kw):
    _bounce_all_enemy_minions(t)
    return SpellApplyResult()


def _apply_coroner(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_optimal_silence_enemy(t, f, enemy_shield=enemy_shield)


def _apply_royal_librarian(t, f, *, mult, enemy_shield, **_kw):
    return _apply_optimal_silence_enemy(t, f, enemy_shield=enemy_shield)


def _transform_friendly_to_rush_copy(unit: dict, *, mult: int) -> None:
    """变形为 5/4 突袭复制（不触发亡语）。"""
    unit["atk"] = 5 * mult
    unit["health"] = 4 * mult
    unit["rush"] = True
    unit["can_face"] = False
    unit["shield"] = False
    unit["attacks_left"] = 1


def _pick_faceless_transform_target(friends: List[dict]) -> Optional[dict]:
    """优先变形本回合已攻击过的友方（attacks_left=0），否则选攻最低的。"""
    if not friends:
        return None
    spent = [fr for fr in friends if fr.get("attacks_left", 0) <= 0]
    pool = spent if spent else friends
    return min(pool, key=lambda x: (x.get("atk", 0), x.get("health", 0)))


def _apply_faceless_corruptor(t, f, *, mult, enemy_shield, **_kw):
    """
    无面腐蚀者：打出本体 5/4 突袭，并将一个友方随从变形为 5/4 突袭复制（不触发亡语）。
    友方已攻击时优先选其为变形目标，解场后可获得两个 5/4 突袭。
    """
    target = _pick_faceless_transform_target(_living_friendly_minions(f))
    _summon_friendly_fighter(f, 5 * mult, 4 * mult, rush=True)
    if target is None:
        return SpellApplyResult()
    for unit in f:
        if unit.get("entity_id") == target.get("entity_id") and unit.get("kind") == "minion":
            _transform_friendly_to_rush_copy(unit, mult=mult)
            break
    return SpellApplyResult()


def _apply_soulstealer(t, f, **_kw):
    _destroy_all_other_minions(t, f)
    return SpellApplyResult()


def _apply_undercooked_calamari(t, f, *, mult, enemy_shield, **_kw):
    return _apply_optimal_destroy_enemy(
        t, f, enemy_shield=enemy_shield,
        filter_fn=lambda u: u.get("atk", 0) <= 3,
    )


def _apply_medivh_hallowed(t, f, **_kw):
    _silence_destroy_all_other(t, f)
    return SpellApplyResult()


def _apply_sylvanas_accused(t, f, *, mult, enemy_shield, **_kw):
    return _apply_optimal_destroy_enemy(t, f, enemy_shield=enemy_shield)


def _apply_brittlebone(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    _apply_optimal_destroy_any_minion(t, f, enemy_shield=enemy_shield)
    return SpellApplyResult()


def _apply_keeper_uldaman(t, f, *, mult, enemy_shield, **_kw):
    return _optimal_set_minion_stats(t, f, 3, 3, enemy_shield=enemy_shield)


def _apply_lilypad_lurker(t, f, *, mult, enemy_shield, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    living = _living_enemy_board_minions(t)
    if not living:
        return SpellApplyResult()
    best = max(living, key=lambda u: (u.get("health", 0), u.get("atk", 0)))
    for unit in t:
        if unit.get("entity_id") == best.get("entity_id"):
            _hex_transform(unit)
            break
    return SpellApplyResult()


def _apply_spawn_deathwing(t, f, *, mult, enemy_shield, rng=None, **_kw):
    return _apply_random_destroy_enemy_minions(
        t, f, count=mult, rng=_rng(rng),
    )


def _apply_swordshiner(t, f, *, mult, enemy_shield, **_kw):
    _add_temp_hero_attack(f, 3 * mult)
    return SpellApplyResult()


def _apply_chrono_lord_epoch(t, f, **_kw):
    for unit in list(t):
        if unit.get("health", 0) > 0 and unit.get("kind") != "hero":
            _destroy_enemy_minion(unit, t, f)
    return SpellApplyResult()


def _apply_backstage_bouncer(t, f, *, mult, enemy_shield, **_kw):
    friends = _living_friendly_minions(f)
    if not friends:
        return SpellApplyResult()
    best = max(friends, key=lambda x: (x.get("atk", 0), x.get("health", 0)))
    for unit in f:
        if unit.get("entity_id") == best.get("entity_id"):
            unit["atk"] = 4 * mult
            unit["health"] = 5 * mult
            unit["taunt"] = True
            break
    return SpellApplyResult()


def _apply_toy_tarim(t, f, *, mult, enemy_shield, **_kw):
    return _optimal_set_minion_stats(t, f, 3 * mult, 7 * mult, enemy_shield=enemy_shield)


# --- 5. 场面（4）---

def _apply_vrykul_necrolyte(t, f, **_kw):
    """维库通灵师：仅标记生命值最低友方（亡语本回合不计入斩杀）。"""
    _pick_lowest_friendly(f)
    return SpellApplyResult()


def _apply_gruesome_nightmare(t, f, *, mult, **_kw):
    target = _pick_lowest_friendly(f)
    if target is None:
        return SpellApplyResult()
    target["atk"] = target.get("atk", 0) + 3 * mult
    return SpellApplyResult()


def _apply_herald_nature(t, f, *, mult, card=None, **_kw):
    if not hand_effect_active(card):
        return SpellApplyResult()
    for unit in f:
        if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
            continue
        unit["atk"] = unit.get("atk", 0) + 1 * mult
        unit["health"] = unit.get("health", 0) + 1 * mult
    return SpellApplyResult()


def _apply_bonemare(t, f, *, mult, **_kw):
    return _buff_lowest_friendly(f, atk=4 * mult, health=4 * mult, taunt=True)


def _count_damaged_minions(taunts: List[dict], fighters: List[dict]) -> int:
    n = 0
    for u in list(taunts) + [x for x in fighters if x.get("kind") == "minion"]:
        if u.get("health", 0) <= 0:
            continue
        if int(u.get("damage", 0) or 0) > 0:
            n += 1
    return n


def _apply_sand_elemental(t, f, *, mult, **_kw) -> SpellApplyResult:
    """沙画元素：+1 攻风怒 + 召唤 4/4。"""
    _summon_friendly_fighter(f, 4 * mult, 4 * mult, card_id="TOY_513")
    f.append({
        "kind": "hero",
        "atk": 1 * mult,
        "health": 10**9,
        "attacks_left": 2 * mult,
        "can_face": True,
    })
    return SpellApplyResult()


def _apply_sharpclaw(t, f, *, mult, **_kw) -> SpellApplyResult:
    """怒爪精锐：其他友方角色 +1 攻。"""
    before = {u.get("entity_id") for u in f if u.get("kind") == "minion"}
    _summon_friendly_fighter(f, 2 * mult, 3 * mult, card_id="AV_294")
    for unit in f:
        if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
            continue
        if unit.get("entity_id") not in before:
            continue
        unit["atk"] = unit.get("atk", 0) + 1 * mult
    _add_temp_hero_attack(f, 1 * mult)
    return SpellApplyResult()


def _grant_rush_on_buff_target(
    fighters: List[dict],
    picked: tuple,
) -> None:
    """战吼赋予突袭：可获得 1 次攻击；新建突袭不能打脸，原本可打脸则保留。"""
    src, key, _unit = picked
    target = None
    idx = None
    if src == "fighter":
        idx = int(key)
        fighters[idx] = dict(fighters[idx])
        target = fighters[idx]
    else:
        eid = key
        for i, f in enumerate(fighters):
            if f.get("entity_id") == eid and f.get("kind") == "minion":
                fighters[i] = dict(f)
                idx = i
                target = fighters[i]
                break
    if target is None or idx is None:
        return
    had_face = bool(target.get("can_face"))
    had_attacks = int(target.get("attacks_left", 0) or 0) > 0
    target["rush"] = True
    if not target.get("charge") and int(target.get("attacks_left", 0) or 0) <= 0:
        target["attacks_left"] = 1
    # 仅靠本次突袭才动手：当回合不能打脸；原本就能出手打脸则保留
    if had_face and had_attacks:
        target["can_face"] = True
    else:
        target["can_face"] = bool(target.get("charge"))


def _apply_defias_smuggler(
    t,
    f,
    *,
    mult,
    card=None,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """迪菲亚私运者：战吼使一个友方随从 +2 攻并获得突袭（预备费由 hand_minion_cost 处理）。"""
    before_ids = {
        u.get("entity_id")
        for u in f
        if u.get("kind") == "minion" and u.get("health", 0) > 0
    }
    if gs is not None and player_id is not None:
        for m in gs.get_board(player_id):
            if m.current_health > 0 and m.entity_id is not None:
                before_ids.add(m.entity_id)
    _summon_friendly_fighter(f, 3 * mult, 3 * mult, card_id="JAIL_998")
    if not before_ids:
        return SpellApplyResult()
    picked = _pick_best_spell_target_fighter(f, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    src, key, unit = picked
    if src == "fighter" and unit.get("entity_id") not in before_ids:
        return SpellApplyResult()
    if src == "board" and key not in before_ids:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        f,
        picked,
        bonus_atk=2 * mult,
        bonus_health=0,
    )
    _grant_rush_on_buff_target(f, picked)
    return SpellApplyResult()


def _apply_abusive_sergeant(
    t,
    f,
    *,
    mult,
    card=None,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """叫嚣的中士：上场（失调）；战吼使一个友方随从本回合 +2 攻。"""
    before_ids = {
        u.get("entity_id")
        for u in f
        if u.get("kind") == "minion" and u.get("health", 0) > 0
    }
    atk = hand_minion_attack(card) if card is not None else 1
    hp = hand_minion_health(card) if card is not None else 1
    if atk <= 0:
        atk = 1
    if hp <= 0:
        hp = 1
    taunt = bool(card and int(card.tags.get("TAUNT", 0) or 0))
    cid = (card.card_id if card and card.card_id else "") or "CORE_CS2_188"
    _summon_friendly_fighter(
        f, atk * mult, hp * max(int(mult), 1),
        taunt=taunt, card_id=cid,
    )
    if not before_ids:
        return SpellApplyResult()
    # 只 buff 已在场上的随从（不含刚上场的中士）；优先能打脸的高攻
    picked = None
    best_rank = None
    for i, unit in enumerate(f):
        if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
            continue
        if unit.get("entity_id") not in before_ids:
            continue
        can_face_now = bool(
            unit.get("can_face") and int(unit.get("attacks_left", 0) or 0) > 0
        )
        rank = (
            1 if can_face_now else 0,
            int(unit.get("atk", 0) or 0) * max(int(unit.get("attacks_left", 0) or 0), 1),
            int(unit.get("atk", 0) or 0),
        )
        if best_rank is None or rank > best_rank:
            best_rank = rank
            picked = ("fighter", i, unit)
    if picked is None:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        f, picked, bonus_atk=2 * mult, bonus_health=0,
    )
    return SpellApplyResult()


def _apply_ogrillon(t, f, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """屠戮者奥格拉：受伤随从数 → +1/+1，对所有敌人攻击。"""
    n = _count_damaged_minions(t, f)
    atk = (3 + n) * mult
    hp = (7 + n) * mult
    res = _apply_all_enemies_damage(t, f, atk, enemy_shield=enemy_shield)
    _summon_friendly_fighter(f, atk, hp, card_id="REV_934")
    return res


def _apply_star_eater(t, f, *, mult, **_kw) -> SpellApplyResult:
    """吞星兽：8/8 嘲讽；法术迸发 +8 攻由 spell_board 处理。"""
    _summon_friendly_fighter(f, 8 * mult, 8 * mult, taunt=True, card_id="GDB_855")
    return SpellApplyResult()


def _apply_tyrande(t, f, *, mult, **_kw) -> SpellApplyResult:
    """泰兰德：5/7；下三张法术双倍施放由 spell_board 处理。"""
    _summon_friendly_fighter(f, 5 * mult, 7 * mult, card_id="EDR_464")
    return SpellApplyResult()


def _apply_sunspot_dragon(
    taunts, fighters, *, mult, enemy_shield, card=None, rng=None, **_kw,
) -> SpellApplyResult:
    """日斑巨龙 WW_434：快枪（POWERED_UP=本回合抽到）造成 6 伤 + 6/6 吸血。"""
    res = SpellApplyResult()
    if quickdraw_active(card):
        res = _apply_optimal_single_target_damage(
            taunts, fighters, 6 * mult, enemy_shield=enemy_shield,
        )
    _summon_friendly_fighter(
        fighters, 6 * mult, 6 * mult, lifesteal=True, card_id="WW_434",
    )
    return res


def _apply_leokk(
    taunts, fighters, *, mult, enemy_shield, **_kw,
) -> SpellApplyResult:
    """雷欧克：下场光环使其他友方随从 +1 攻（本回合自身失调）。"""
    for _ in range(max(1, int(mult))):
        _summon_friendly_fighter(
            fighters, 2, 4, card_id="NEW1_033", aura=True,
        )
    return SpellApplyResult()


def _apply_team_spirit(t, f, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """团队之灵：潜行一回合；你的回合英雄 +2 攻（光环，本回合可挥击）。"""
    _summon_friendly_fighter(
        f, 0, 3 * mult, card_id="TOY_028", aura=True,
    )
    _add_temp_hero_attack(f, 2 * mult)
    return SpellApplyResult()


def _apply_manifested_timeways(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    card=None,
    gs=None,
    player_id=None,
    **_kw,
) -> SpellApplyResult:
    """时间流具象：战吼——若控制光环，对所有敌人造成 3 点伤害。"""
    from .battlecry_board import timeways_aura_condition_met

    atk = hand_minion_attack(card) if card is not None else 3
    hp = hand_minion_health(card) if card is not None else 3
    _summon_friendly_fighter(
        fighters, atk * mult, hp * mult, card_id="TIME_019",
    )
    if not timeways_aura_condition_met(card, gs, player_id, fighters):
        return SpellApplyResult()
    return _apply_all_enemies_damage(
        taunts, fighters, 3 * mult, enemy_shield=enemy_shield,
    )


def _register_p0_battlecry() -> None:
    specs = [
        # 1. 直伤
        (("TOY_101",), 5, "暗夜精灵女猎手", _apply_night_elf_huntress, False),
        (("ETC_209",), 3, "硬核信徒", _apply_hardcore_cultist, False),
        (("TTN_457",), 3, "悼词宣诵者", _apply_eulogizer, False),
        (("TOY_642",), 4, "球霸野猪人", _apply_ball_hog, False),
        (("TID_716",), 8, "潮汐亡魂", _apply_tidal_revenant, False),
        (("TTN_456",), 2, "蔽刺触手", _apply_thornveil, True),
        (("RLK_915",), 3, "琥珀雏龙", _apply_amber_whelp, False),
        (("GDB_434",), 4, "流彩巨岩", _apply_bolide_behemoth, False),
        (("YOG_519",), 5, "腐化残渣", _apply_tainted_remnant, True),
        (("REV_906", "CORE_REV_906"), 10, "德纳修斯大帝", _apply_sire_denathrius, True),
        (("BT_717",), 4, "潜地蝎", _apply_burrowing_scorpid, False),
        (("REV_013", "REV_013t", "CORE_REV_013"), 5, "石裔指控者", _apply_stoneborn_accuser, False),
        (("WW_906",), 4, "吵闹的伴侣", _apply_rowdy_partner, False),
        (("TSC_064",), 7, "蛇行死鳞纳迦", _apply_slithering_deathscale, False),
        (("RLK_222",), 2, "阿斯塔洛·血誓", _apply_astalor, False),
        (("CORE_RLK_505",), 6, "髓骨使御者", _apply_marrow_manipulator, True),
        (("TOY_341",), 5, "恋旧的小丑", _apply_nostalgic_clown, False),
        (("TOY_370",), 4, "三芯诡烛", _apply_triplewick, True),
        (("WW_026",), 7, "灾变飓风斯卡尔", _apply_skarr, False),
        (("TIME_004",), 7, "时光流汇扫荡者", _apply_conflux_crasher, True),
        (("VAC_442",), 4, "燃灯元素", _apply_lamplighter, False),
        (("MEND_302",), 4, "废土先锋", _apply_wasteland_vanguard, True),
        (("TIME_609",), 3, "游侠将军希尔瓦娜斯", _apply_sylvanas_ranger, False),
        (("CS2_042", "CORE_CS2_042", "VAN_CS2_042"), 6, "火元素", _apply_fire_elemental, False),
        # 2. 解场伤
        (("TLC_606",), 3, "拉特维亚护甲师", _apply_latorvian_armorer, False),
        (("DED_507",), 3, "桅台观察员", _apply_crows_nest, False),
        (("WW_820",), 4, "棘尾幼龙", _apply_spinetail_drake, False),
        (("GDB_901",), 3, "极紫外破坏者", _apply_uv_breaker, False),
        (("BT_722",), 1, "防护改装师", _apply_guardian_augmerchant, False),
        (("GDB_132",), 3, "躁动的愤怒卫士", _apply_wrathguard, False),
        (("ONY_024",), 4, "奥妮克希亚幼龙", _apply_onyxian_drake, False),
        (("DMF_101",), 5, "焰火元素", _apply_firework_elemental, False),
        (("CATA_552",), 6, "乌鳞斥候", _apply_ebonscale_scout, False),
        # 3. AOE
        (("GDB_226",), 5, "凶恶的入侵者", _apply_hostile_invader, False),
        (("AV_126",), 3, "碉堡中士", _apply_bunker_sergeant, False),
        (("AV_222",), 5, "话痨奥术师", _apply_spammy_arcanist, False),
        (("TTN_458",), 5, "XB-488清理机器人", _apply_disposalbot, True),
        (("BAR_840",), 4, "旋风争斗者", _apply_whirling_combatant, False),
        (("LOOT_410",), 4, "破晓之龙", _apply_duskbreaker, False),
        (("WW_346",), 6, "爆破龟", _apply_blast_tortoise, False),
        (("BAR_750",), 4, "大地亡魂", _apply_earth_revenant, False),
        (("AV_313",), 5, "可怕的憎恶", _apply_hollow_abomination, False),
        # 4. 移除
        (("CATA_201",), 9, "暮光主母", _apply_twilight_mistress, False),
        (("RLK_951",), 2, "验尸官", _apply_coroner, False),
        (("CORE_SW_066",), 4, "王室图书管理员", _apply_royal_librarian, False),
        (("DRG_076",), 5, "无面腐蚀者", _apply_faceless_corruptor, False),
        (("RLK_741",), 8, "窃魂者", _apply_soulstealer, False),
        (("VAC_341",), 4, "断生鱿鱼", _apply_undercooked_calamari, False),
        (("TIME_890",), 10, "圣者麦迪文", _apply_medivh_hallowed, False),
        (("MAW_033",), 6, "被告希尔瓦娜斯", _apply_sylvanas_accused, False),
        (("SCH_513",), 4, "脆骨破坏者", _apply_brittlebone, False),
        (("LOE_017",), 3, "奥达曼守护者", _apply_keeper_uldaman, False),
        (("BAR_848",), 5, "荷塘潜伏者", _apply_lilypad_lurker, False),
        (("ONY_035",), 5, "死亡之翼的子嗣", _apply_spawn_deathwing, True),
        (("WW_434",), 6, "日斑巨龙", _apply_sunspot_dragon, False),
        (("VAC_701",), 3, "刀剑保养师", _apply_swordshiner, False),
        (("TIME_714",), 6, "时光领主埃博克", _apply_chrono_lord_epoch, False),
        (("JAM_014",), 4, "后台保镖", _apply_backstage_bouncer, False),
        (("TOY_813",), 5, "玩具队长塔林姆", _apply_toy_tarim, False),
        # 5. 场面
        (("RLK_867",), 2, "维库通灵师", _apply_vrykul_necrolyte, False),
        (("CATA_161",), 3, "残恶梦魇", _apply_gruesome_nightmare, False),
        (("TID_002",), 3, "自然使徒", _apply_herald_nature, False),
        (("ICC_705", "CORE_ICC_705"), 7, "骨魇", _apply_bonemare, False),
        (("TOY_513",), 4, "沙画元素", _apply_sand_elemental, False),
        (("AV_294",), 2, "怒爪精锐", _apply_sharpclaw, False),
        (("JAIL_998",), 3, "迪菲亚私运者", _apply_defias_smuggler, False),
        (("CORE_CS2_188", "CS2_188"), 1, "叫嚣的中士", _apply_abusive_sergeant, False),
        (("REV_934",), 6, "屠戮者奥格拉", _apply_ogrillon, False),
        (("GDB_855",), 8, "吞星兽", _apply_star_eater, False),
        (("EDR_464",), 7, "泰兰德", _apply_tyrande, False),
        (("NEW1_033", "VAN_NEW1_033"), 3, "雷欧克", _apply_leokk, False),
        (("TOY_028",), 2, "团队之灵", _apply_team_spirit, False),
        (("TIME_019",), 4, "时间流具象", _apply_manifested_timeways, False),
    ]
    for card_ids, cost, name, fn, uses_random in specs:
        _register_bc(
            BoardSpellDef(
                card_ids=card_ids,
                base_cost=cost,
                name=name,
                apply=fn,
                uses_random=uses_random,
            )
        )


_register_p0_battlecry()
