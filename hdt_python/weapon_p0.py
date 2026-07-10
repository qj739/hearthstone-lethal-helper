# weapon_p0.py — 竞技场武器（31 张）

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

from .eudora_loot import _add_temp_weapon, _buff_friendly_minion, strip_weapon_fighters
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_minions_aoe_spell,
    _apply_direct_face,
    _apply_random_enemy_hits,
    _summon_friendly_fighter,
)
from .weapon_board import _register_weapon

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

MC_SEED = 0


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_SEED)


def _weapon_stats_from_card(
    card: Optional["Entity"],
    default_atk: int,
    default_dur: int,
) -> tuple[int, int]:
    """手牌武器打出时读取实体当前攻/耐久（含 BUFF）。"""
    if card is None:
        return default_atk, default_dur
    from .board_damage import _std_attack

    atk = _std_attack(card) or default_atk
    dur = card.current_durability
    if dur <= 0:
        dur = max(1, int(card.health or card.tags.get("HEALTH", 0) or default_dur))
    return atk, max(1, dur)


def _equip(
    fighters: List[dict],
    atk: int,
    dur: int,
    card_id: str,
    *,
    mult: int = 1,
    windfury: bool = False,
    lifesteal: bool = False,
    face_after_minion_attack: int = 0,
    all_minions_after_attack: int = 0,
    random_other_enemy_atk: bool = False,
    buff_friendly_atk_after: int = 0,
    buff_friendly_stats_after: tuple[int, int] = (0, 0),
    summon_on_attack: tuple[int, int] | None = None,
) -> None:
    had_equipped = any(f.get("kind") == "weapon" for f in fighters)
    remaining_hero_attacks = strip_weapon_fighters(fighters)
    max_swings = (2 if windfury else 1) * mult
    if had_equipped:
        swings = min(remaining_hero_attacks, max_swings, max(1, dur))
    else:
        swings = min(max_swings, max(1, dur))
    _add_temp_weapon(
        fighters,
        atk * mult,
        max(1, dur),
        card_id=card_id,
        attacks_left=swings,
    )
    w = fighters[-1]
    if lifesteal:
        w["lifesteal"] = True
    if face_after_minion_attack:
        w["face_after_minion_attack"] = face_after_minion_attack * mult
    if all_minions_after_attack:
        w["all_minions_after_attack"] = all_minions_after_attack * mult
    if random_other_enemy_atk:
        w["random_other_enemy_atk"] = True
    if buff_friendly_atk_after:
        w["buff_friendly_atk_after"] = buff_friendly_atk_after * mult
    if buff_friendly_stats_after != (0, 0):
        ba, bh = buff_friendly_stats_after
        w["buff_friendly_stats_after"] = (ba * mult, bh * mult)
    if summon_on_attack:
        sa, sh = summon_on_attack
        w["summon_on_attack"] = (sa * mult, sh * mult)


# 已装备武器的攻击后效果（与 _equip 中 hand 打出一致；供 _build_fighters 挂载）
WEAPON_AFTER_ATTACK_META: dict[str, dict] = {
    "RLK_516": {"face_after_minion_attack": 2},
    "CATA_467": {"buff_friendly_atk_after": 2},
    "EDR_842": {"random_other_enemy_atk": True},
    "TLC_478": {"all_minions_after_attack": 1},
    "DMF_705": {"buff_friendly_stats_after": (1, 1)},
    "TOY_358": {"summon_on_attack": (1, 1)},
}


def stamp_equipped_weapon_effects(fighter: dict, card_id: str) -> None:
    """把已装备武器 card_id 对应的攻击后触发写入 fighter（敲狼锤 +1/+1 等）。"""
    cid = card_id or ""
    meta = WEAPON_AFTER_ATTACK_META.get(cid)
    if meta is None and cid.startswith("CORE_"):
        meta = WEAPON_AFTER_ATTACK_META.get(cid[5:])
    if meta is None:
        meta = WEAPON_AFTER_ATTACK_META.get("CORE_" + cid)
    if not meta:
        return
    for key, val in meta.items():
        fighter[key] = val


def after_hero_weapon_attack(
    weapon: dict,
    target: dict,
    taunts: List[dict],
    fighters: List[dict],
    *,
    enemy_shield: bool,
    rng: Optional[random.Random] = None,
) -> int:
    """英雄武器攻击后触发（碎骨手斧、远祖之斧等）。"""
    if weapon.get("kind") != "weapon" or weapon.get("health", 0) <= 0:
        return 0
    heal = 0
    roll = _rng(rng)
    # 攻击结算后随从可能已死亡，不能用 health>0 判断是否为随从目标
    target_is_minion = target.get("kind") != "hero"

    face_extra = int(weapon.get("face_after_minion_attack", 0) or 0)
    if face_extra > 0 and target_is_minion:
        fighters.append({
            "kind": "hero",
            "atk": face_extra,
            "health": 10**9,
            "attacks_left": 1,
            "can_face": True,
        })

    aoe_min = int(weapon.get("all_minions_after_attack", 0) or 0)
    if aoe_min > 0:
        res = _apply_all_minions_aoe_spell(taunts, fighters, aoe_min)
        heal += res.opponent_lifesteal_heal

    if weapon.get("random_other_enemy_atk") and target_is_minion:
        dmg = int(weapon.get("atk", 0))
        if dmg > 0:
            res = _apply_random_enemy_hits(
                taunts, fighters, hits=1, damage=dmg,
                enemy_shield=enemy_shield, rng=roll,
            )
            heal += res.opponent_lifesteal_heal

    batk = int(weapon.get("buff_friendly_atk_after", 0) or 0)
    if batk > 0:
        _buff_friendly_minion(fighters, atk_bonus=batk)

    bstats = weapon.get("buff_friendly_stats_after")
    if bstats:
        ba, bh = bstats
        _buff_friendly_minion(fighters, atk_bonus=int(ba), hp_bonus=int(bh))

    summon = weapon.get("summon_on_attack")
    if summon:
        sa, sh = summon
        _summon_friendly_fighter(fighters, int(sa), int(sh))

    return heal


# --- 各武器 ---

def _apply_cata_axe(t, f, *, mult, **_kw):
    _equip(f, 3, 2, "CATA_580", mult=mult)
    return SpellApplyResult()


def _apply_ashbringer_lite(t, f, *, mult, **_kw):
    _equip(f, 3, 2, "ETC_423", mult=mult)
    return SpellApplyResult()


def _apply_shatterbone(t, f, *, mult, **_kw):
    _equip(f, 2, 2, "RLK_516", mult=mult, face_after_minion_attack=2)
    return SpellApplyResult()


def _apply_commanding_claw(t, f, *, mult, **_kw):
    _equip(f, 2, 2, "CATA_467", mult=mult, buff_friendly_atk_after=2)
    return SpellApplyResult()


def _apply_defiling_spear(t, f, *, mult, **_kw):
    _equip(f, 2, 4, "EDR_842", mult=mult, random_other_enemy_atk=True)
    return SpellApplyResult()


def _apply_forward_axe(t, f, *, mult, **_kw):
    _equip(f, 3, 4, "BAR_844", mult=mult)
    return SpellApplyResult()


def _apply_crimson_wings(t, f, *, mult, **_kw):
    _equip(f, 1, 2, "BT_922", mult=mult)
    for _ in range(2):
        _summon_friendly_fighter(f, 1 * mult, 1 * mult, card_id="BT_922")
    return SpellApplyResult()


def _apply_ancestral_axe(t, f, *, mult, **_kw):
    _equip(f, 2, 3, "TLC_478", mult=mult, all_minions_after_attack=1)
    return SpellApplyResult()


def _apply_hammer(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "DMF_705", mult=mult, buff_friendly_stats_after=(1, 1))
    return SpellApplyResult()


def _apply_plague_knife(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "BOT_286", mult=mult)
    return SpellApplyResult()


def _apply_kingslayer(t, f, *, mult, **_kw):
    _equip(f, 3, 2, "TIME_875t1", mult=mult)
    return SpellApplyResult()


def _apply_atiesh(t, f, *, mult, **_kw):
    _equip(f, 1, 10, "TIME_890t", mult=mult)
    return SpellApplyResult()


def _apply_muradin_hammer(t, f, *, mult, **_kw):
    _equip(f, 3, 4, "TIME_209t", mult=mult, windfury=True)
    return SpellApplyResult()


def _apply_swamp_knuckles(t, f, *, mult, **_kw):
    _equip(f, 4, 5, "BT_102", mult=mult)
    return SpellApplyResult()


def _apply_pluck(t, f, *, mult, **_kw):
    _equip(f, 4, 4, "CORE_DAL_720", mult=mult)
    return SpellApplyResult()


def _apply_smith_hammer(t, f, *, mult, **_kw):
    _equip(f, 3, 4, "TTN_467", mult=mult)
    return SpellApplyResult()


def _apply_ref_gloves(t, f, *, mult, **_kw):
    _equip(f, 3, 4, "TOY_641", mult=mult)
    return SpellApplyResult()


def _apply_astro_keyboard(t, f, *, mult, **_kw):
    _equip(f, 0, 2, "ETC_521", mult=mult)
    return SpellApplyResult()


def _apply_cenarius_axe(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "TIME_020t1", mult=mult, lifesteal=True)
    return SpellApplyResult()


def _apply_shepherds(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "EDR_416", mult=mult)
    return SpellApplyResult()


def _apply_bear_mace(t, f, *, mult, card=None, **_kw):
    atk, dur = _weapon_stats_from_card(card, 4, 4)
    _equip(f, atk, dur, "EDR_253", mult=mult)
    return SpellApplyResult()


def _apply_harpoon(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "TSC_070", mult=mult)
    return SpellApplyResult()


def _apply_inspiration(t, f, *, mult, **_kw):
    _equip(f, 2, 2, "CATA_472", mult=mult)
    return SpellApplyResult()


def _apply_star_blade(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "GDB_726", mult=mult)
    return SpellApplyResult()


def _apply_infused_axe(t, f, *, mult, **_kw):
    _equip(f, 2, 3, "REV_933", mult=mult)
    return SpellApplyResult()


def _apply_valiant_sword(t, f, *, mult, **_kw):
    _equip(f, 3, 5, "MEND_803", mult=mult)
    return SpellApplyResult()


def _apply_judgment(t, f, *, mult, **_kw):
    _equip(f, 5, 7, "YOP_011", mult=mult)
    return SpellApplyResult()


def _apply_virtue_brush(t, f, *, mult, **_kw):
    _equip(f, 2, 4, "TOY_810", mult=mult, lifesteal=True)
    return SpellApplyResult()


def _apply_hope(t, f, *, mult, **_kw):
    _equip(f, 4, 6, "RLK_828", mult=mult)
    return SpellApplyResult()


def _apply_remote(t, f, *, mult, **_kw):
    _equip(f, 1, 2, "TOY_358", mult=mult, summon_on_attack=(1, 1))
    return SpellApplyResult()


def _apply_amplify(t, f, *, mult, **_kw):
    _equip(f, 3, 3, "REV_509", mult=mult)
    return SpellApplyResult()


_WEAPON_OVERRIDES = {
    "CATA_580": ("灾变战斧", _apply_cata_axe),
    "ETC_423": ("奥金利斧", _apply_ashbringer_lite),
    "RLK_516": ("碎骨手斧", _apply_shatterbone),
    "CATA_467": ("命令之爪", _apply_commanding_claw),
    "EDR_842": ("亵渎之矛", _apply_defiling_spear),
    "BAR_844": ("前锋战斧", _apply_forward_axe),
    "BT_922": ("棕红之翼", _apply_crimson_wings),
    "TLC_478": ("远祖之斧", _apply_ancestral_axe),
    "DMF_705": ("敲狼锤", _apply_hammer),
    "BOT_286": ("死金匕首", _apply_plague_knife),
    "TIME_875t1": ("弑君者", _apply_kingslayer),
    "TIME_890t": ("圣杖埃提耶什", _apply_atiesh),
    "TIME_209t": ("高山之王的战锤", _apply_muradin_hammer),
    "BT_102": ("沼泽拳刺", _apply_swamp_knuckles),
    "CORE_DAL_720": ("摇摆矿锄", _apply_pluck),
    "TTN_467": ("匠人之锤", _apply_smith_hammer),
    "TOY_641": ("裁判拳套", _apply_ref_gloves),
    "ETC_521": ("星界键盘", _apply_astro_keyboard),
    "TIME_020t1": ("塞纳留斯之斧", _apply_cenarius_axe),
    "EDR_416": ("牧人之杖", _apply_shepherds),
    "EDR_253": ("巨熊之槌", _apply_bear_mace),
    "TSC_070": ("鱼叉炮", _apply_harpoon),
    "CATA_472": ("灵感之槌", _apply_inspiration),
    "GDB_726": ("斩星巨刃", _apply_star_blade),
    "REV_933": ("灌能战斧", _apply_infused_axe),
    "MEND_803": ("砺胆重剑", _apply_valiant_sword),
    "YOP_011": ("审判圣契", _apply_judgment),
    "TOY_810": ("画师的美德", _apply_virtue_brush),
    "RLK_828": ("奎尔萨拉斯的希望", _apply_hope),
    "TOY_358": ("遥控器", _apply_remote),
    "REV_509": ("放大战刃", _apply_amplify),
}


def _load_arena_weapon_meta() -> List[tuple[str, int, str]]:
    try:
        from pathlib import Path
        import sys

        root = Path(__file__).resolve().parents[2]
        scripts = root / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from generate_arena_weapon_worklist import collect as collect_weapons  # noqa: WPS433

        items, _, _ = collect_weapons()
        return [(it["cid"], it["cost"], it["name_zh"]) for it in items]
    except Exception:
        return [(cid, 0, name) for cid, (name, _) in _WEAPON_OVERRIDES.items()]


def _register_all_weapons() -> None:
    seen: set[str] = set()
    for cid, cost, name in _load_arena_weapon_meta():
        if cid in seen:
            continue
        seen.add(cid)
        if cid in _WEAPON_OVERRIDES:
            zh, fn = _WEAPON_OVERRIDES[cid]
            _register_weapon(BoardSpellDef((cid,), cost, zh, fn))
            continue
        def _fallback(t, f, *, mult, _cid=cid, **_kw):
            _equip(f, 1, 1, _cid, mult=mult)
            return SpellApplyResult()

        _register_weapon(BoardSpellDef((cid,), cost or 0, name, _fallback))


_register_all_weapons()
