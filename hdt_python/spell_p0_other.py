# spell_p0_other.py — P0 第六阶段：其他法术（16 张）

from __future__ import annotations

import random
from copy import deepcopy
from typing import List, Optional

from .combat_sim import project_board_face_after_spell
from .end_turn_board import (
    EtKind,
    RED_CARD_FRIENDLY_WAKE_BENEFIT_IDS,
    end_turn_face_from_fighters,
    _resolve_end_turn_def,
)
from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    SpellApplyResult,
    _apply_best_minion_damage,
    _apply_damage_to_unit,
    _apply_direct_face,
    _apply_optimal_single_target_damage,
    _apply_random_enemy_hits,
    _apply_random_minion_hits,
    _can_spell_hit_enemy_face,
    _living_enemy_board_minions,
    _living_enemy_taunts,
    _register,
    _remove_dead_taunts,
    _steal_enemy_minion_to_fighter,
    _summon_friendly_fighter,
    player_corpses,
    apply_divine_shield_to_hits,
)

MC_DEFAULT_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _apply_optimal_friendly_buff(
    taunts: List[dict],
    fighters: List[dict],
    *,
    bonus_atk: int,
    bonus_health: int,
    enemy_shield: bool,
) -> None:
    """使一个友方随从获得额外攻血（优选提场攻）。"""
    best_score = -1
    best_idx: int | None = None
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        fs = deepcopy(fighters)
        ts = deepcopy(taunts)
        fs[i] = dict(fs[i])
        fs[i]["atk"] = fs[i].get("atk", 0) + bonus_atk
        fs[i]["health"] = fs[i].get("health", 0) + bonus_health
        score = project_board_face_after_spell(ts, fs, enemy_shield) or 0
        if score > best_score:
            best_score = score
            best_idx = i
    if best_idx is not None:
        fighters[best_idx]["atk"] = fighters[best_idx].get("atk", 0) + bonus_atk
        fighters[best_idx]["health"] = fighters[best_idx].get("health", 0) + bonus_health


def _apply_collaborative_spark(
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    **_kw,
) -> SpellApplyResult:
    """协作火花：对一名敌人 3 伤；若消灭随从，随机友方随从 +3/+3（取场攻最优）。"""
    amount = _sd(3, mult=mult, spell_power=spell_power)
    if amount <= 0:
        return SpellApplyResult()

    bonus_atk = _sd(3, mult=mult, spell_power=spell_power)
    bonus_health = _sd(3, mult=mult, spell_power=spell_power)
    best_score = -1
    best_plan: Optional[tuple] = None  # ("face",) | ("minion", entity_id)

    def _simulate(hit_face: bool, eid: Optional[int]) -> int:
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        if hit_face:
            face = apply_divine_shield_to_hits([amount], enemy_shield)
            return face + project_board_face_after_spell(ts, fs, enemy_shield)
        target = next(
            (x for x in ts if x.get("entity_id") == eid and x.get("health", 0) > 0),
            None,
        )
        if target is None:
            return -1
        was_alive = target.get("health", 0) > 0
        _, face, _ = _apply_damage_to_unit(
            target, amount, taunts=ts, fighters=fs, enemy_shield=enemy_shield,
        )
        _remove_dead_taunts(ts)
        if was_alive and target.get("health", 0) <= 0:
            _apply_optimal_friendly_buff(
                ts, fs,
                bonus_atk=bonus_atk,
                bonus_health=bonus_health,
                enemy_shield=enemy_shield,
            )
        return face + (project_board_face_after_spell(ts, fs, enemy_shield) or 0)

    if _can_spell_hit_enemy_face(taunts):
        face_score = _simulate(True, None)
        if face_score > best_score:
            best_score = face_score
            best_plan = ("face",)

    for m in _living_enemy_board_minions(taunts):
        if m.get("spell_immune"):
            continue
        eid = m.get("entity_id")
        s = _simulate(False, eid)
        if s > best_score:
            best_score = s
            best_plan = ("minion", eid)

    if best_plan is None:
        return SpellApplyResult()

    if best_plan[0] == "face":
        return _apply_direct_face(amount, enemy_shield)

    eid = best_plan[1]
    target = next(
        (x for x in taunts if x.get("entity_id") == eid and x.get("health", 0) > 0),
        None,
    )
    if target is None:
        return SpellApplyResult()
    res = SpellApplyResult()
    was_alive = target.get("health", 0) > 0
    heal, face, _ = _apply_damage_to_unit(
        target, amount, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
    )
    res.opponent_lifesteal_heal = heal
    res.direct_face_damage = face
    _remove_dead_taunts(taunts)
    if was_alive and target.get("health", 0) <= 0:
        _apply_optimal_friendly_buff(
            taunts, fighters,
            bonus_atk=bonus_atk,
            bonus_health=bonus_health,
            enemy_shield=enemy_shield,
        )
    return res


def _apply_tooth_of_nefarian(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_infested_breath(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """感染吐息：2 伤（0/2 水蛭 v1 不计场攻）。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_dart_throw(taunts, fighters, *, mult, enemy_shield, rng=None, spell_power=0, **_kw,) -> SpellApplyResult:
    """飞镖投掷：随机对敌方随从造成 2 点伤害，触发两次。"""
    return _apply_random_minion_hits(
        taunts, fighters, hits=_sd(2, mult=mult, spell_power=spell_power), damage=2,
        enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_army_of_the_dead(
    taunts, fighters, *, mult, enemy_shield, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """亡者大军：消耗最多5份残骸，各复活为2/2突袭复活的食尸鬼。"""
    corpses = player_corpses(gs, player_id) if gs is not None and player_id is not None else 0
    count = min(5, corpses) * mult
    if count <= 0:
        return SpellApplyResult()
    token_ids = ("RLK_060t", "CORE_RLK_060t")
    for i in range(count):
        _summon_friendly_fighter(
            fighters, 2, 2, rush=True, card_id=token_ids[i % len(token_ids)],
        )
    return SpellApplyResult()


def _apply_infestation(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """虫害侵扰：两张毒刺虫 token，各 2 伤 + 2/1 突袭。"""
    total = SpellApplyResult()
    for _ in range(_sd(2, mult=mult, spell_power=spell_power)):
        part = _apply_optimal_single_target_damage(
            taunts, fighters, 2, enemy_shield=enemy_shield,
        )
        total.opponent_lifesteal_heal += part.opponent_lifesteal_heal
        total.direct_face_damage += part.direct_face_damage
        _summon_friendly_fighter(fighters, 2, 1, rush=True)
    return total


def _apply_natural_causes(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    _summon_friendly_fighter(fighters, 2, 2)
    return res


def _apply_pop_up_book(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """立体书：2 伤（0/1 嘲讽青蛙 v1 不计场攻）。"""
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_living_roots(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """活体根须：抉择 — 2 伤或两个 1/1（选场攻更高分支）。"""
    dmg_score = 0
    ts_d = deepcopy(taunts)
    fs_d = deepcopy(fighters)
    _apply_optimal_single_target_damage(
        ts_d, fs_d, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    dmg_score = project_board_face_after_spell(ts_d, fs_d, enemy_shield) or 0

    ts_s = deepcopy(taunts)
    fs_s = deepcopy(fighters)
    for _ in range(_sd(2, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fs_s, 1, 1)
    summon_score = project_board_face_after_spell(ts_s, fs_s, enemy_shield) or 0

    if dmg_score >= summon_score:
        return _apply_optimal_single_target_damage(
            taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        )
    for _ in range(_sd(2, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fighters, 1, 1)
    return SpellApplyResult()


def _apply_darkbomb(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_frost_lich_cross_stitch(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """霜巫十字绣：3 伤；若消灭则召唤 3/6（当回合失调）。"""
    return _apply_best_minion_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
        summon_on_kill=(3, 6, False),
    )


def _apply_runed_orb(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_tar_slick(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """焦油飞溅：随从受伤翻倍，法术 1 伤对随从视为 2 伤。"""
    return _apply_best_minion_damage(
        taunts, fighters, _sd(2, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _apply_sizzling_swarm(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """炽火缠身：3 伤 + 召唤 3 个 2/1 炽烈烬火。"""
    res = _apply_optimal_single_target_damage(
        taunts, fighters, _sd(3, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )
    for _ in range(_sd(3, mult=mult, spell_power=spell_power)):
        _summon_friendly_fighter(fighters, 2, 1)
    return res


def _apply_call_of_the_wild(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,
) -> SpellApplyResult:
    """兽群呼唤：召唤米莎、雷欧克、霍弗；霍弗冲锋，雷欧克光环经 summon 自动挂到其他随从。"""
    m = _sd(1, mult=mult, spell_power=spell_power)
    _summon_friendly_fighter(
        fighters, 4 * m, 4 * m, taunt=True, card_id="NEW1_032",
    )
    _summon_friendly_fighter(fighters, 2 * m, 4 * m, card_id="NEW1_033")
    _summon_friendly_fighter(
        fighters, 4 * m, 2 * m, charge=True, card_id="NEW1_034",
    )
    return SpellApplyResult()


def _apply_velens_chosen(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """维伦的恩泽：友方随从 +2/+4。"""
    _apply_optimal_friendly_buff(
        taunts, fighters,
        bonus_atk=_sd(2, mult=mult, spell_power=spell_power), bonus_health=_sd(4, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )
    return SpellApplyResult()


def _apply_hold_them_off(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw,) -> SpellApplyResult:
    """拦住他们！：使一个友方随从获得 +5/+5 和吸血（吸血不计场攻）。"""
    _apply_optimal_friendly_buff(
        taunts, fighters,
        bonus_atk=_sd(5, mult=mult, spell_power=spell_power),
        bonus_health=_sd(5, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )
    return SpellApplyResult()


def _apply_spellweavers_brilliance(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """织法者的光辉：召唤 6/6 龙（当回合失调）。"""
    _summon_friendly_fighter(fighters, 6, 6)
    return SpellApplyResult()


def _apply_potion_of_madness(taunts, fighters, *, mult, enemy_shield, **_kw,) -> SpellApplyResult:
    """疯狂药水：夺取攻≤2 敌方随从；未冰冻可当回合打脸；亡语按我方触发。"""
    best_score = -1.0
    best_eid = None
    for m in _living_enemy_board_minions(taunts):
        if int(m.get("atk", 0) or 0) > 2 or m.get("spell_immune"):
            continue
        eid = m.get("entity_id")
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next(
            (x for x in ts if x.get("entity_id") == eid and x.get("health", 0) > 0),
            None,
        )
        if target is None:
            continue
        if not _steal_enemy_minion_to_fighter(target, ts, fs):
            continue
        score = float(project_board_face_after_spell(ts, fs, enemy_shield) or 0)
        if score > best_score:
            best_score = score
            best_eid = eid
    if best_eid is None:
        return SpellApplyResult()
    target = next(
        (x for x in taunts if x.get("entity_id") == best_eid and x.get("health", 0) > 0),
        None,
    )
    if target is None:
        return SpellApplyResult()
    _steal_enemy_minion_to_fighter(target, taunts, fighters)
    return SpellApplyResult()


def _red_card_projected_face(
    taunts, fighters, *, enemy_shield, gs=None, player_id=None,
) -> float:
    board = float(project_board_face_after_spell(taunts, fighters, enemy_shield) or 0)
    et = float(end_turn_face_from_fighters(
        fighters, taunts, enemy_shield, game_state=gs, player_id=player_id,
    ))
    return board + et


def _mark_red_card_dormant(unit: dict, *, friendly: bool) -> None:
    unit["dormant"] = True
    if friendly:
        unit["attacks_left"] = 0
        unit["can_face"] = False


def _red_card_dormant_wake_face_gain(card_id: str) -> int:
    """友方红牌休眠后可触发的回合结束打脸（如玛瑟里顿 +3）。"""
    defn = _resolve_end_turn_def(card_id)
    if defn is None or not defn.requires_dormant:
        return 0
    if defn.kind == EtKind.ALL_ENEMIES_DAMAGE:
        return int(defn.amount or 0)
    if defn.kind == EtKind.HERO_DAMAGE:
        return int(defn.amount or 0)
    return 0


def _friendly_red_card_wake_worth_it(cand: dict) -> bool:
    """已唤醒友方：仅当回合结束收益高于当回合可打脸时才考虑红牌。"""
    cid = cand.get("card_id", "") or ""
    wake_gain = _red_card_dormant_wake_face_gain(cid)
    if wake_gain <= 0:
        return False
    if not cand.get("can_face", True) or cand.get("attacks_left", 0) <= 0:
        return True
    atk_face = int(cand.get("atk", 0) or 0) * int(cand.get("attacks_left", 0) or 0)
    return atk_face < wake_gain


def _iter_red_card_friendly_wake_candidates(
    fighters: List[dict], gs, player_id,
):
    """已唤醒、红牌休眠后可触发回合结束的友方随从。"""
    seen_eids: set = set()
    for f in fighters:
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        cid = f.get("card_id", "") or ""
        eid = f.get("entity_id")
        if eid is not None:
            seen_eids.add(eid)
        if (
            cid in RED_CARD_FRIENDLY_WAKE_BENEFIT_IDS
            and not f.get("dormant")
            and _friendly_red_card_wake_worth_it(f)
        ):
            yield f
    if gs is None or player_id is None:
        return
    from .board_damage import is_dormant as entity_is_dormant

    for entity in gs.get_board(player_id):
        if entity.entity_id in seen_eids or entity.current_health <= 0:
            continue
        cid = entity.card_id or ""
        if cid not in RED_CARD_FRIENDLY_WAKE_BENEFIT_IDS or entity_is_dormant(entity):
            continue
        stub = {
            "kind": "minion",
            "entity_id": entity.entity_id,
            "card_id": cid,
            "atk": int(entity.tags.get("ATK", 0) or getattr(entity, "atk", 0) or 0),
            "health": entity.current_health,
            "attacks_left": 0,
            "can_face": False,
            "dormant": False,
        }
        if _friendly_red_card_wake_worth_it(stub):
            yield stub


def _apply_red_card_dormant_to_friendly(fighters: List[dict], eid) -> bool:
    for f in fighters:
        if f.get("entity_id") == eid and f.get("health", 0) > 0:
            _mark_red_card_dormant(f, friendly=True)
            return True
    return False


def _apply_lunar_ritual(taunts, fighters, *, mult, card=None, enemy_shield=False, rng=None, **_kw,) -> SpellApplyResult:
    """新月/满月仪式：随机召唤两个指定费随从（召唤失调，本回合不可攻击）。"""
    cid = getattr(card, "card_id", None) or ""
    pool_cost = 6 if cid == "EDR_461t" else 3
    for _ in range(mult):
        for i in range(2):
            if pool_cost >= 6:
                atk, health = (6, 6) if i == 0 else (4, 4)
            else:
                atk, health = 3, 3
            _summon_friendly_fighter(fighters, atk, health)
    return SpellApplyResult()


def _apply_red_card(taunts, fighters, *, mult, enemy_shield, gs=None, player_id=None, **_kw,) -> SpellApplyResult:
    """
    红牌：使一个随从休眠 2 回合；休眠随从本回合不计嘲讽、不参与交换。
    敌方：仅评估嘲讽随从（与其它单体法术一致）；友方例外：已唤醒玛瑟里顿可红牌休眠以触发回合结束 +3。
    """
    best_score = -1.0
    best_kind: Optional[str] = None
    best_eid = None
    best_friendly_stub: Optional[dict] = None

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
        if score > best_score:
            best_score = score
            best_kind = "enemy"
            best_eid = eid
            best_friendly_stub = None

    for cand in _iter_red_card_friendly_wake_candidates(fighters, gs, player_id):
        eid = cand.get("entity_id")
        ts = deepcopy(taunts)
        fs = deepcopy(fighters)
        target = next((x for x in fs if x.get("entity_id") == eid), None)
        if target is None:
            fs.append(dict(cand))
            target = fs[-1]
        _mark_red_card_dormant(target, friendly=True)
        score = _red_card_projected_face(
            ts, fs, enemy_shield=enemy_shield, gs=gs, player_id=player_id,
        )
        if score > best_score:
            best_score = score
            best_kind = "friendly"
            best_eid = eid
            best_friendly_stub = dict(cand) if target is fs[-1] else None

    if best_eid is None or best_kind is None:
        return SpellApplyResult()

    if best_kind == "enemy":
        target = next(
            (x for x in taunts if x.get("entity_id") == best_eid and x.get("health", 0) > 0),
            None,
        )
        if target is not None:
            _mark_red_card_dormant(target, friendly=False)
    else:
        if not _apply_red_card_dormant_to_friendly(fighters, best_eid):
            if best_friendly_stub is not None:
                stub = dict(best_friendly_stub)
                _mark_red_card_dormant(stub, friendly=True)
                fighters.append(stub)
    return SpellApplyResult()


# 玛法里奥的礼物：发现池固定为横扫 / 野性成长 / 野性之心（临时牌，按原价计）
_MALFURIONS_GIFT_DISCOVER = (
    "CORE_CS2_012",  # 横扫
    "CORE_CS2_013",  # 野性成长
    "CORE_OG_047",   # 野性之心
)


def _score_discovered_spell(
    card_id: str,
    taunts,
    fighters,
    *,
    mult,
    enemy_shield,
    spell_power=0,
    **kwargs,
) -> float:
    from .spell_board import get_board_spell_def

    defn = get_board_spell_def(card_id)
    if not defn:
        return -1.0
    ts = deepcopy(taunts)
    fs = deepcopy(fighters)
    sub = defn.apply(
        ts, fs, mult=mult, enemy_shield=enemy_shield,
        spell_power=spell_power, **kwargs,
    )
    return float(sub.direct_face_damage) + float(
        project_board_face_after_spell(ts, fs, enemy_shield) or 0
    )


def _apply_wild_growth(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """野性成长：+1 空水晶。"""
    res = SpellApplyResult()
    res.mana_crystal_gain = 1
    return res


def _apply_feral_rage(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """野性之心：斩杀搜索取 +4 攻分支（忽略 8 甲）。"""
    bonus = _sd(4, mult=mult, spell_power=spell_power)
    for f in fighters:
        if f.get("kind") in ("hero", "weapon") and f.get("health", 0) > 0:
            f["atk"] = f.get("atk", 0) + bonus
            if f.get("kind") == "hero":
                f["can_face"] = True
    return SpellApplyResult()


def _apply_malfurions_gift(taunts, fighters, *, mult, enemy_shield, spell_power=0, **_kw) -> SpellApplyResult:
    """玛法里奥的礼物：三选一发现，取对斩杀最优的衍生法术并立刻视为入手。"""
    best_id: Optional[str] = None
    best_score = -1.0
    for sid in _MALFURIONS_GIFT_DISCOVER:
        score = _score_discovered_spell(
            sid, taunts, fighters,
            mult=mult, enemy_shield=enemy_shield, spell_power=spell_power, **_kw,
        )
        if score > best_score:
            best_score = score
            best_id = sid
    if best_id:
        return SpellApplyResult(add_hand_spell_id=best_id)
    return SpellApplyResult()


def _register_p0_other() -> None:
    specs = [
        (("GIFT_10", "CORE_GIFT_10"), 1, "玛法里奥的礼物", _apply_malfurions_gift, False),
        (("CS2_013", "CORE_CS2_013"), 2, "野性成长", _apply_wild_growth, False),
        (("OG_047", "CORE_OG_047"), 3, "野性之心", _apply_feral_rage, False),
        (("ONY_032",), 2, "奈法利安的牙", _apply_tooth_of_nefarian, False),
        (("EDR_814",), 2, "感染吐息", _apply_infested_breath, False),
        (("WW_006",), 2, "飞镖投掷", _apply_dart_throw, True),
        (("TLC_902",), 2, "虫害侵扰", _apply_infestation, False),
        (("RLK_060", "CORE_RLK_060"), 5, "亡者大军", _apply_army_of_the_dead, False),
        (("REV_307",), 2, "自然死亡", _apply_natural_causes, False),
        (("TOY_508",), 1, "立体书", _apply_pop_up_book, False),
        (("CORE_AT_037",), 1, "活体根须", _apply_living_roots, False),
        (("GVG_015",), 2, "暗色炸弹", _apply_darkbomb, False),
        (("TOY_377",), 4, "霜巫十字绣", _apply_frost_lich_cross_stitch, False),
        (("CORE_BAR_541",), 2, "符文宝珠", _apply_runed_orb, False),
        (("TTN_726",), 1, "焦油飞溅", _apply_tar_slick, False),
        (("TLC_221",), 6, "炽火缠身", _apply_sizzling_swarm, False),
        (("GVG_010",), 3, "维伦的恩泽", _apply_velens_chosen, False),
        (("JAIL_913",), 5, "拦住他们！", _apply_hold_them_off, False),
        (("END_014",), 4, "协作火花", _apply_collaborative_spark, False),
        (("CATA_452",), 10, "织法者的光辉", _apply_spellweavers_brilliance, False),
        (("OG_211", "CORE_OG_211"), 8, "兽群呼唤", _apply_call_of_the_wild, False),
        (("CFM_603",), 1, "疯狂药水", _apply_potion_of_madness, False),
        (("TOY_644",), 1, "红牌", _apply_red_card, False),
        (("EDR_461",), 5, "新月仪式", _apply_lunar_ritual, False),
        (("EDR_461t",), 5, "满月仪式", _apply_lunar_ritual, False),
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


_register_p0_other()
