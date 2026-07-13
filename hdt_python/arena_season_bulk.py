# arena_season_bulk.py — 竞技场新赛季缺口卡批量接入（ARENA_GAP_REPORT.md）

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .app_paths import resource_path
from .board_damage import hand_minion_attack, hand_minion_health
from .deathrattle import DeathrattleDef, DrKind
from .end_turn_board import EndTurnDef, EtKind

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GAP_REPORT = DOCS / "ARENA_GAP_REPORT.md"

_REGISTERED_LOG: List[Tuple[str, str, str, str]] = []  # category, cid, name, impl
_BULK_DONE = False


def _sb():
    from . import spell_board as sb
    return sb


@dataclass(frozen=True)
class _SpellSpec:
    kind: str
    amount: int = 0
    amount2: int = 0
    uses_random: bool = False
    note: str = ""


# 法术：精确效果（自动分类覆盖不到时）
_SPELL_OVERRIDES: Dict[str, _SpellSpec] = {
    "END_007": _SpellSpec("direct_plus_hero", 1, 1, note="1伤+英雄+1攻"),
    "TIME_218": _SpellSpec("direct_plus_hero", 1, 1),
    "JAM_013": _SpellSpec("all_other_minions", 1, note="+3/+3友方+1伤全场其他"),
    "END_014": _SpellSpec("face_direct", 3),
    "REV_369": _SpellSpec("random_enemy_minions", 6, amount2=3, uses_random=True),
    "REV_834": _SpellSpec("random_enemy_minion_hits", 1, amount2=2, uses_random=True),
    "TIME_001": _SpellSpec("random_split_enemies", 6, uses_random=True, note="3×2随机"),
    "TIME_441": _SpellSpec("random_split_enemies", 8, uses_random=True, note="Rewind 4×2"),
    "TIME_027": _SpellSpec("random_split_enemies", 6, uses_random=True),
    "ETC_528": _SpellSpec("random_split_enemies", 4, uses_random=True, note="2束×2"),
    "CORE_BAR_311": _SpellSpec("random_split_enemies", 4, uses_random=True),
    "ONY_011": _SpellSpec("random_split_enemies", 10, uses_random=True),
    "TOY_714": _SpellSpec("enemy_aoe", 1, note="每条龙重复"),
    "ETC_305": _SpellSpec("destroy_weak", 5),
    "CORE_CS2_108": _SpellSpec("destroy_damaged_enemy"),
    "VAC_460": _SpellSpec("face_direct", 2, note="连击铸币v1不计"),
    "JAM_022": _SpellSpec("minion_direct", 2, note="沉默+连击2伤"),
    "DEEP_011": _SpellSpec("minion_direct", 2),
    "CORE_BOT_222": _SpellSpec("minion_direct", 4, note="同时打英雄v1仅随从"),
    "TOY_640": _SpellSpec("minion_direct", 5, note="邻接溢出v1单目标"),
    "MIS_027": _SpellSpec("minion_direct", 2, note="多米诺v1首目标"),
    "CORE_RLK_035": _SpellSpec("all_minions_aoe", 1, note="残骸递增v1单次"),
    "END_023": _SpellSpec("destroy_damaged_enemy", note="冻结邻接v1消灭受伤"),
    "END_028": _SpellSpec("destroy_atk_le", 4),
    "REV_252": _SpellSpec("destroy_atk_le", 3, note="灌注v1按3攻"),
    "RLK_025": _SpellSpec("minion_direct", 3),
    "REV_364": _SpellSpec("face_direct", 3, note="休眠种子v1仅3伤"),
    "CORE_BT_072": _SpellSpec("noop", note="冻结+水元素v1不计"),
    "CORE_BAR_801": _SpellSpec("face_direct", 1, note="+1/1突袭v1仅1伤"),
    "REV_840": _SpellSpec("all_minions_aoe", 2, note="骷髅v1仅AOE"),
    "MAW_019": _SpellSpec("destroy_enemy", note="延迟消灭v1立即"),
    "MAW_023": _SpellSpec("destroy_enemy", note="延迟消灭v1立即"),
    "MAW_001": _SpellSpec("destroy_enemy", note="延迟消灭v1立即"),
    "CATA_EVENT_402": _SpellSpec("destroy_any"),
    "CORE_CS2_076": _SpellSpec("destroy_enemy"),
    "EX1_312": _SpellSpec("destroy_all_minions"),
    "CORE_EX1_407": _SpellSpec("destroy_all_minions", note="留一随机v1全灭"),
    "MIS_701": _SpellSpec("noop"),
    "JAM_008": _SpellSpec("noop"),
    "CORE_LOOT_101": _SpellSpec("noop", note="奥秘"),
    "CORE_EX1_610": _SpellSpec("noop", note="奥秘"),
    "MAW_010": _SpellSpec("noop", note="奥秘"),
    "CORE_ULD_152": _SpellSpec("noop", note="奥秘"),
    "TIME_715": _SpellSpec("noop"),
    "REV_920": _SpellSpec("noop"),
    "LOOT_504": _SpellSpec("noop"),
    "ETC_362": _SpellSpec("noop"),
    "TOY_602": _SpellSpec("noop"),
    "TOY_529": _SpellSpec("noop"),
    "REV_924": _SpellSpec("noop"),
    "REV_950": _SpellSpec("noop"),
    "TOY_384": _SpellSpec("noop"),
    "SCH_514": _SpellSpec("noop"),
    "ETC_413": _SpellSpec("hero_attack", 2, note="免疫+攻击v1仅+2攻"),
    "TIME_212": _SpellSpec("minion_direct", 4, note="先打友方v1打敌方"),
}

# 战吼精确效果
_BC_OVERRIDES: Dict[str, _SpellSpec] = {
    "CORE_EX1_082": _SpellSpec("random_split_characters", 3, uses_random=True),
    "TIME_019": _SpellSpec("all_enemies", 3),
    "CORE_UNG_848": _SpellSpec("all_other_minions", 2),
    "CORE_OG_149": _SpellSpec("all_other_minions", 1),
    "END_034": _SpellSpec("destroy_enemy", note="随机随从/地标/武器v1消灭随从"),
    "TIME_EVENT_301": _SpellSpec("destroy_enemy", uses_random=True, note="龙数重复v1一次"),
    "CORE_EX1_005": _SpellSpec("destroy_high_atk", 7),
    "CATA_EVENT_002": _SpellSpec("destroy_enemy"),
    "CORE_ULD_165": _SpellSpec("destroy_enemy"),
    "NEW1_030": _SpellSpec("all_other_minions_destroy"),
    "TOY_357": _SpellSpec("noop", note="冲锋+弹回"),
    "TOY_520": _SpellSpec("noop", note="战吼随机奥秘，消灭在回合开始"),
}

# 连击精确效果
_COMBO_OVERRIDES: Dict[str, _SpellSpec] = {
    "CORE_EX1_134": _SpellSpec("face_direct", 3),
    "ETC_072": _SpellSpec("random_split_enemies", 4, uses_random=True),
    "CORE_EX1_131": _SpellSpec("summon", 2, 1, note="2/1强盗"),
    "TIME_710": _SpellSpec("summon_copy"),
    "CORE_BOT_576": _SpellSpec("buff_friendly", 4),
    "END_032": _SpellSpec("rush_default", note="连击免疫v1默认突袭"),
    "JAM_021": _SpellSpec("rush_default", note="连击剧毒v1默认突袭"),
    "ETC_073": _SpellSpec("rush_default"),
    "TOY_516": _SpellSpec("rush_default", note="rush_p0已注册"),
    "ETC_077": _SpellSpec("combo_body_only"),
    "REV_826": _SpellSpec("combo_body_only"),
    "CORE_DMF_511": _SpellSpec("combo_body_only"),
}

# 亡语
_DEATHRATTLE_SPECS: Dict[str, DeathrattleDef] = {
    "REV_356": DeathrattleDef(DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=1, summon_count=1),
    "TOY_670": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=1, summon_health=2,
        summon_taunt=True, summon_count=2, summon_card_id="TOY_670t",
    ),
    "TIME_017": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=7, summon_health=7,
        summon_taunt=True, summon_card_id="TIME_017t",
    ),
    "TLC_468": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=2, summon_taunt=True,
    ),
    "REV_012": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=4, summon_taunt=True,
    ),
    "TOY_814": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=1, summon_health=1, summon_count=5,
    ),
    "GDB_331": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=4, summon_health=4, summon_count=2,
    ),
    "BOT_700": DeathrattleDef(
        DrKind.SUMMON_ENEMY, summon_atk=1, summon_health=1, summon_count=2,
    ),
    "TOY_908": DeathrattleDef(DrKind.RANDOM_SPLIT_ATTACKERS, amount=4),
    "CORE_SW_439": DeathrattleDef(DrKind.SUMMON_ENEMY, summon_atk=2, summon_health=1, summon_count=1),
}

# 回合结束（含旧清单）
_END_TURN_SPECS: Dict[str, EndTurnDef] = {
    "TOY_824": EndTurnDef(
        EtKind.RANDOM_SPLIT_ENEMIES, uses_self_atk=True, uses_random=True, name="黑棘针线师",
    ),
    "TOY_820": EndTurnDef(EtKind.ATTACK_LOWEST_ENEMY, uses_self_atk=True, name="废弃电子玩偶"),
    "CORE_TTN_866": EndTurnDef(EtKind.HERO_DAMAGE, amount=0, name="神秘恐魔"),
    "YOP_034": EndTurnDef(EtKind.RANDOM_SPLIT_ENEMIES, amount=10, uses_random=True, name="窜逃的黑翼龙"),
    "CORE_YOP_034": EndTurnDef(EtKind.RANDOM_SPLIT_ENEMIES, amount=10, uses_random=True, name="窜逃的黑翼龙"),
    "BAR_063": EndTurnDef(EtKind.ALL_ENEMIES_DAMAGE, amount=2, name="沃坎诺斯"),
    "BAR_064": EndTurnDef(EtKind.ALL_ENEMIES_DAMAGE, amount=2, name="亮铜之翼"),
}

_WEAPON_SPECIAL: Dict[str, Tuple[int, int, str]] = {
    "TOY_522": (4, 3, "水弹枪1/1海盗v1默认"),
    "END_012": (3, 3, "无穷之手v1默认"),
    "TLC_EVENT_402": (3, 3, "亡语全灭v1默认"),
    "ETC_520": (4, 3, "亡语1伤全场v1默认"),
}


def _log(category: str, cid: str, name: str, impl: str) -> None:
    _REGISTERED_LOG.append((category, cid, name, impl))


def _parse_gap_sections() -> Dict[str, List[str]]:
    if not GAP_REPORT.is_file():
        return {}
    text = GAP_REPORT.read_text(encoding="utf-8")
    sections: Dict[str, List[str]] = {}
    current: Optional[str] = None
    id_re = re.compile(r"`([A-Z][A-Z0-9_]+)`")
    for line in text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            if title.startswith("法术"):
                current = "spell"
            elif "战吼" in title:
                current = "battlecry"
            elif "突袭" in title:
                current = "rush"
            elif "武器" in title:
                current = "weapon"
            elif "连击" in title:
                current = "combo"
            elif "亡语" in title:
                current = "deathrattle"
            elif "回合结束" in title:
                current = "end_turn"
            elif title.startswith("法术 Top"):
                current = None
            else:
                current = None
            continue
        if current and line.startswith("| `"):
            m = id_re.search(line)
            if m:
                sections.setdefault(current, []).append(m.group(1))
    for cid, name in (
        ("YOP_034", "窜逃的黑翼龙"),
        ("CORE_YOP_034", "窜逃的黑翼龙"),
        ("BAR_063", "沃坎诺斯"),
        ("BAR_064", "亮铜之翼"),
    ):
        sections.setdefault("end_turn", [])
        if cid not in sections["end_turn"]:
            sections["end_turn"].append(cid)
    return sections


def _load_cards() -> Tuple[Dict[str, dict], Dict[str, str]]:
    cards_path = resource_path("json", "cards.json")
    zh_path = resource_path("json", "cards_zhCN.json")
    cards = {
        c["id"]: c
        for c in json.loads(cards_path.read_text(encoding="utf-8"))
        if c.get("id")
    }
    zh: Dict[str, str] = {}
    if zh_path.is_file():
        for c in json.loads(zh_path.read_text(encoding="utf-8")):
            if c.get("id") and c.get("name"):
                zh[c["id"]] = c["name"]
    return cards, zh


def _card_text(card: dict) -> str:
    return (card.get("text") or "").replace("\n", " ")


def _first_damage(text: str) -> int:
    m = re.search(r"Deal \$?(\d+)", text, re.I)
    return int(m.group(1)) if m else 0


def _destroy_atk_threshold(text: str) -> Optional[int]:
    m = re.search(r"with (\d+) or less Attack", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"with (\d+) or more Attack", text, re.I)
    if m:
        return -int(m.group(1))
    return None


def _classify_spell(text: str) -> _SpellSpec:
    t = text.lower()
    if "secret" in t:
        return _SpellSpec("noop", note="奥秘")
    if "discover" in t or "draw" in t and "damage" not in t:
        if "deal" not in t and "destroy" not in t:
            return _SpellSpec("noop", note="发现/过牌")
    if "transform all" in t:
        return _SpellSpec("noop", note="变形全场")
    dmg = _first_damage(text)
    thr = _destroy_atk_threshold(text)
    if thr is not None:
        if thr > 0:
            return _SpellSpec("destroy_atk_le", thr)
        return _SpellSpec("destroy_atk_ge", -thr)
    if "destroy all minions" in t:
        return _SpellSpec("destroy_all_minions")
    if "destroy a damaged enemy" in t or "destroy a damaged" in t:
        return _SpellSpec("destroy_damaged_enemy")
    if "destroy an enemy minion" in t or "destroy a minion" in t:
        return _SpellSpec("destroy_enemy")
    if "all enemy minions" in t and "deal" in t:
        return _SpellSpec("enemy_aoe", dmg or 1)
    if "all minions" in t and "deal" in t:
        return _SpellSpec("all_minions_aoe", dmg or 1)
    if "all enemies" in t or "all characters" in t:
        if "random" in t and "split" in t:
            return _SpellSpec("random_split_enemies", dmg or 1, uses_random=True)
        return _SpellSpec("all_enemies", dmg or 1)
    if "random" in t and ("split" in t or "among" in t):
        return _SpellSpec("random_split_enemies", dmg or 1, uses_random=True)
    if "to a minion" in t or "to an enemy minion" in t:
        return _SpellSpec("minion_direct", dmg or 1)
    if "give your hero" in t and "+1 attack" in t and "deal" in t:
        return _SpellSpec("direct_plus_hero", dmg or 1, 1)
    if "give your hero" in t and "attack" in t:
        m = re.search(r"\+(\d+) attack", t)
        return _SpellSpec("hero_attack", int(m.group(1)) if m else 1)
    if "deal" in t and dmg:
        return _SpellSpec("face_direct", dmg)
    return _SpellSpec("noop", note="未分类")


_TRIGGER_TEXT_SPLITS = (
    "at the start of your turn",
    "at the end of your turn",
    "at the end of each turn",
    "deathrattle:",
    "<b>deathrattle</b>",
    "dormant for",
)


def _immediate_effect_text(text: str) -> str:
    """截掉回合开始/结束、亡语等后续触发器，避免误归入战吼/当回合效果。"""
    portion = text.lower()
    for sep in _TRIGGER_TEXT_SPLITS:
        if sep in portion:
            portion = portion.split(sep, 1)[0]
    return portion


def _classify_battlecry(text: str) -> _SpellSpec:
    t = text.lower()
    bc = _immediate_effect_text(text)
    if "battlecry" not in t and "deal" not in bc and "destroy" not in bc:
        return _SpellSpec("noop", note="无直伤战吼")
    if "secret" in bc and ("cast" in bc or "play" in bc):
        return _SpellSpec("noop", note="战吼奥秘")
    dmg = _first_damage(bc)
    if "randomly split" in bc or "random" in bc and "split" in bc:
        return _SpellSpec("random_split_characters", dmg or 1, uses_random=True)
    if "all enemies" in bc:
        return _SpellSpec("all_enemies", dmg or 1)
    if "all other minions" in bc:
        return _SpellSpec("all_other_minions", dmg or 1)
    if "destroy" in bc and "7 or more" in bc:
        return _SpellSpec("destroy_high_atk", 7)
    if "destroy" in bc and "random" in bc:
        return _SpellSpec("destroy_enemy", uses_random=True)
    if "destroy" in bc and "all other" in bc:
        return _SpellSpec("all_other_minions_destroy")
    if "destroy" in bc:
        return _SpellSpec("destroy_enemy")
    if "deal" in bc and dmg:
        return _SpellSpec("face_direct", dmg)
    return _SpellSpec("noop", note="无直伤战吼")


def _destroy_atk_le(t, f, threshold: int, *, mult, enemy_shield, **_kw):
    sb = _sb()
    for unit in list(t):
        if unit.get("kind") == "hero":
            continue
        if int(unit.get("atk", 0) or 0) <= threshold:
            unit["health"] = 0
    for unit in list(f):
        if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
            continue
        if int(unit.get("atk", 0) or 0) <= threshold:
            unit["health"] = 0
    sb._remove_dead_taunts(t)
    return sb.SpellApplyResult()


def _destroy_atk_ge(t, f, threshold: int, *, mult, enemy_shield, **_kw):
    sb = _sb()
    for unit in list(t):
        if unit.get("kind") == "hero":
            continue
        if int(unit.get("atk", 0) or 0) >= threshold:
            unit["health"] = 0
    sb._remove_dead_taunts(t)
    return sb.SpellApplyResult()


def _destroy_all_minions(t, f, *, mult, **_kw):
    sb = _sb()
    for unit in list(t):
        if unit.get("kind") != "hero":
            unit["health"] = 0
    for unit in list(f):
        unit["health"] = 0
    sb._remove_dead_taunts(t)
    return sb.SpellApplyResult()


def _destroy_damaged_enemies(t, f, *, mult, enemy_shield, **_kw):
    sb = _sb()
    for unit in list(t):
        if unit.get("kind") == "hero":
            continue
        if int(unit.get("damage", 0) or 0) > 0:
            unit["health"] = 0
    sb._remove_dead_taunts(t)
    return sb.SpellApplyResult()


def _destroy_weak_minion(t, f, amount: int, *, mult, enemy_shield, **_kw):
    sb = _sb()
    targets = sb._lethal_target_enemy_minions(t)
    if not targets:
        return sb.SpellApplyResult()
    best = min(targets, key=lambda u: int(u.get("health", 0)))
    debuff = amount * mult
    best["atk"] = max(0, int(best.get("atk", 0)) - debuff)
    best["health"] = max(0, int(best.get("health", 0)) - debuff)
    if int(best.get("atk", 0)) <= 0:
        best["health"] = 0
    sb._remove_dead_taunts(t)
    return sb.SpellApplyResult()


def _make_spell_apply(spec: _SpellSpec) -> Callable:
    kind = spec.kind
    amt = spec.amount
    amt2 = spec.amount2
    sb = _sb()
    SpellApplyResult = sb.SpellApplyResult
    _add_temp_hero_attack = sb._add_temp_hero_attack
    _apply_all_enemies_damage = sb._apply_all_enemies_damage
    _apply_all_minions_aoe_spell = sb._apply_all_minions_aoe_spell
    _apply_optimal_single_target_damage = sb._apply_optimal_single_target_damage
    _apply_random_split_damage = sb._apply_random_split_damage
    from .spell_p0_aoe import _all_minions_aoe, _enemy_minions_aoe
    from .spell_p0_remove import (
        _apply_optimal_destroy_any_minion,
        _apply_optimal_destroy_enemy,
    )

    if kind == "noop":
        def _noop(*_a, **_k):
            return SpellApplyResult()
        return _noop
    if kind == "face_direct":
        from .spell_p0_minion import _optimal_damage_fn
        return _optimal_damage_fn(amt)
    if kind == "minion_direct":
        from .spell_p0_minion import _minion_damage_fn
        return _minion_damage_fn(amt)
    if kind == "enemy_aoe":
        return _enemy_minions_aoe(amt)
    if kind == "all_minions_aoe":
        return _all_minions_aoe(amt)
    if kind == "all_enemies":
        _sd = sb.scaled_spell_damage
        def _all_en(t, f, *, mult, enemy_shield, spell_power=0, **_kw):
            return _apply_all_enemies_damage(
                t, f, _sd(amt, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
            )
        return _all_en
    if kind == "all_other_minions":
        return lambda t, f, *, mult, **_kw: _apply_all_minions_aoe_spell(t, f, amt * mult)
    if kind == "random_split_enemies":
        def _rs(t, f, *, mult, enemy_shield, rng=None, **_kw):
            return _apply_random_split_damage(
                t, f, amt * mult, enemy_shield=enemy_shield, rng=rng,
            )
        return _rs
    if kind == "destroy_enemy":
        return _apply_optimal_destroy_enemy
    if kind == "destroy_any":
        def _destroy_any(t, f, *, mult, enemy_shield, **_kw):
            _apply_optimal_destroy_any_minion(
                t, f, enemy_shield=enemy_shield, **_kw,
            )
            return SpellApplyResult()
        return _destroy_any
    if kind == "destroy_damaged_enemy":
        return _destroy_damaged_enemies
    if kind == "destroy_atk_le":
        return lambda t, f, *, mult, enemy_shield, **_kw: _destroy_atk_le(
            t, f, amt, mult=mult, enemy_shield=enemy_shield,
        )
    if kind == "destroy_atk_ge":
        return lambda t, f, *, mult, enemy_shield, **_kw: _destroy_atk_ge(
            t, f, amt, mult=mult, enemy_shield=enemy_shield,
        )
    if kind == "destroy_all_minions":
        return _destroy_all_minions
    if kind == "destroy_weak":
        return lambda t, f, *, mult, enemy_shield, **_kw: _destroy_weak_minion(
            t, f, amt, mult=mult, enemy_shield=enemy_shield,
        )
    if kind == "hero_attack":
        def _ha(t, f, *, mult, **_kw):
            _add_temp_hero_attack(f, amt * mult)
            return SpellApplyResult()
        return _ha
    if kind == "direct_plus_hero":
        def _dph(t, f, *, mult, enemy_shield, spell_power=0, **_kw):
            res = _apply_optimal_single_target_damage(
                t, f, amt * mult, enemy_shield=enemy_shield, spell_power=spell_power,
            )
            _add_temp_hero_attack(f, amt2 * mult)
            return res
        return _dph
    if kind == "random_enemy_minion_hits":
        from .spell_board import _apply_random_enemy_hits
        def _reh(t, f, *, mult, enemy_shield, rng=None, **_kw):
            return _apply_random_enemy_hits(
                t, f,
                hits=amt2 * mult,
                damage=amt * mult,
                enemy_shield=enemy_shield,
                rng=rng,
            )
        return _reh
    if kind == "random_enemy_minions":
        from .spell_board import _apply_random_minion_hits
        def _rem(t, f, *, mult, enemy_shield, rng=None, **_kw):
            return _apply_random_minion_hits(
                t, f,
                hits=amt2 * mult,
                damage=amt * mult,
                enemy_shield=enemy_shield,
                rng=rng,
            )
        return _rem
  # fallback
    def _noop2(*_a, **_k):
        return SpellApplyResult()
    return _noop2


def _make_battlecry_apply(spec: _SpellSpec) -> Callable:
    sb = _sb()
    SpellApplyResult = sb.SpellApplyResult
    _apply_random_split_damage = sb._apply_random_split_damage
    if spec.kind == "random_split_characters":
        def _rsc(t, f, *, mult, enemy_shield, rng=None, **_kw):
            return _apply_random_split_damage(
                t, f, spec.amount * mult, enemy_shield=enemy_shield, rng=rng,
            )
        return _rsc
    if spec.kind == "all_other_minions_destroy":
        return _destroy_all_minions
    if spec.kind == "destroy_high_atk":
        def _dh(t, f, *, mult, enemy_shield, **_kw):
            targets = [
                u for u in sb._lethal_target_enemy_minions(t)
                if int(u.get("atk", 0)) >= spec.amount
            ]
            if not targets:
                return SpellApplyResult()
            best = max(targets, key=lambda u: int(u.get("atk", 0)))
            best["health"] = 0
            sb._remove_dead_taunts(t)
            return SpellApplyResult()
        return _dh
    return _make_spell_apply(spec)


def _summon_bc_body(f, card, *, mult: int = 1) -> None:
    if card is None:
        return
    atk = hand_minion_attack(card) * mult
    hp = hand_minion_health(card) * mult
    cid = card.card_id or ""
    _sb()._summon_friendly_fighter(f, atk, hp, card_id=cid)


def _make_combo_apply(spec: _SpellSpec, cid: str) -> Callable:
    sb = _sb()
    SpellApplyResult = sb.SpellApplyResult
    hand_effect_active = sb.hand_effect_active
    _summon_friendly_fighter = sb._summon_friendly_fighter
    if spec.kind == "rush_default":
        from .rush_p0 import _apply_default_rush_minion
        return _apply_default_rush_minion
    if spec.kind == "combo_body_only":
        def _body(t, f, *, mult, card=None, **_kw):
            _summon_bc_body(f, card, mult=mult)
            return SpellApplyResult()
        return _body
    if spec.kind == "summon":
        def _sum(t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **_kw):
            _summon_bc_body(f, card, mult=mult)
            if hand_effect_active(
                card, combo_active=combo_active, gs=gs, player_id=player_id,
            ):
                for _ in range(mult):
                    _summon_friendly_fighter(
                        f, spec.amount, spec.amount2, card_id=f"{cid}t",
                    )
            return SpellApplyResult()
        return _sum
    if spec.kind == "summon_copy":
        def _copy(t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **_kw):
            _summon_bc_body(f, card, mult=mult)
            if hand_effect_active(
                card, combo_active=combo_active, gs=gs, player_id=player_id,
            ):
                _summon_bc_body(f, card, mult=mult)
            return SpellApplyResult()
        return _copy
    if spec.kind == "buff_friendly":
        def _buff(t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **_kw):
            _summon_bc_body(f, card, mult=mult)
            if hand_effect_active(
                card, combo_active=combo_active, gs=gs, player_id=player_id,
            ):
                mins = sb._friendly_minions(f)
                if mins:
                    best = max(mins, key=lambda u: int(u.get("atk", 0)))
                    best["atk"] = int(best.get("atk", 0)) + spec.amount * mult
            return SpellApplyResult()
        return _buff

    base = _make_spell_apply(spec)

    def _combo_wrap(
        t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **kw,
    ):
        _summon_bc_body(f, card, mult=mult)
        if hand_effect_active(
            card, combo_active=combo_active, gs=gs, player_id=player_id,
        ):
            return base(t, f, mult=mult, card=card, combo_active=combo_active, gs=gs, player_id=player_id, **kw)
        return SpellApplyResult()

    return _combo_wrap


def _spell_registered(cid: str) -> bool:
    board = _sb().BOARD_CLEAR_SPELLS
    if cid in board:
        return True
    base = cid[5:] if cid.startswith("CORE_") else cid
    return base in board or f"CORE_{base}" in board


def _board_registered(cid: str, board: dict) -> bool:
    if cid in board:
        return True
    base = cid[5:] if cid.startswith("CORE_") else cid
    return base in board or f"CORE_{base}" in board


def _register_spells(ids: List[str], cards: dict, zh: dict) -> None:
    sb = _sb()
    seen: set[str] = set()
    for cid in ids:
        if cid in seen or _spell_registered(cid):
            continue
        seen.add(cid)
        card = cards.get(cid, {})
        text = _card_text(card)
        spec = _SPELL_OVERRIDES.get(cid) or _classify_spell(text)
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        impl = spec.note or spec.kind
        if spec.amount and spec.kind not in ("noop",):
            impl = f"{spec.kind}({spec.amount})"
        sb._register(sb.BoardSpellDef(
            (cid,), cost, name, _make_spell_apply(spec),
            uses_random=spec.uses_random,
        ))
        _log("法术", cid, name, impl)


def _register_battlecries(ids: List[str], cards: dict, zh: dict) -> None:
    from .battlecry_board import BOARD_BATTLECRY, _register_bc
    sb = _sb()
    seen: set[str] = set()
    for cid in ids:
        if cid in seen or _board_registered(cid, BOARD_BATTLECRY):
            continue
        seen.add(cid)
        card = cards.get(cid, {})
        text = _card_text(card)
        spec = _BC_OVERRIDES.get(cid) or _classify_battlecry(text)
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        impl = spec.note or spec.kind

        def _apply(t, f, *, mult, card=None, _spec=spec, **kw):
            _summon_bc_body(f, card, mult=mult)
            bc = _make_battlecry_apply(_spec)
            return bc(t, f, mult=mult, card=card, **kw)

        _register_bc(sb.BoardSpellDef(
            (cid,), cost, name, _apply, uses_random=spec.uses_random,
        ))
        _log("战吼", cid, name, impl)


def _register_rush_cards(ids: List[str], cards: dict, zh: dict) -> None:
    from .battlecry_board import BOARD_BATTLECRY
    from .rush_board import BOARD_RUSH, _register_rush
    from .rush_p0 import _apply_default_rush_minion
    sb = _sb()
    seen: set[str] = set()
    for cid in ids:
        if cid in seen or _board_registered(cid, BOARD_RUSH) or _board_registered(cid, BOARD_BATTLECRY):
            continue
        seen.add(cid)
        card = cards.get(cid, {})
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        _register_rush(sb.BoardSpellDef((cid,), cost, name, _apply_default_rush_minion))
        _log("突袭", cid, name, "default_rush")


def _register_weapons(ids: List[str], cards: dict, zh: dict) -> None:
    from .weapon_board import BOARD_WEAPON, _register_weapon
    from .weapon_p0 import _equip, _weapon_stats_from_card
    sb = _sb()
    seen: set[str] = set()
    for cid in ids:
        if cid in seen or _board_registered(cid, BOARD_WEAPON):
            continue
        seen.add(cid)
        card = cards.get(cid, {})
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        atk = int(card.get("attack", 1) or 1)
        dur = int(card.get("durability", 1) or 1)
        note = _WEAPON_SPECIAL.get(cid, (atk, dur, "equip"))[2]

        def _weapon_fn(t, f, *, mult, card=None, _a=atk, _d=dur, _cid=cid, **_kw):
            wa, wd = _weapon_stats_from_card(card, _a, _d)
            _equip(f, wa, wd, _cid, mult=mult)
            return sb.SpellApplyResult()

        _register_weapon(sb.BoardSpellDef((cid,), cost, name, _weapon_fn))
        _log("武器", cid, name, note)


def _register_combos(ids: List[str], cards: dict, zh: dict) -> None:
    from .combo_board import BOARD_COMBO, _register_combo
    from .rush_board import BOARD_RUSH
    sb = _sb()
    seen: set[str] = set()
    for cid in ids:
        if cid in seen or _board_registered(cid, BOARD_COMBO):
            continue
        if _board_registered(cid, BOARD_RUSH) and cid not in _COMBO_OVERRIDES:
            continue
        seen.add(cid)
        card = cards.get(cid, {})
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        spec = _COMBO_OVERRIDES.get(cid, _SpellSpec("combo_body_only"))
        _register_combo(sb.BoardSpellDef(
            (cid,), cost, name, _make_combo_apply(spec, cid),
            uses_random=spec.uses_random,
        ))
        _log("连击", cid, name, spec.note or spec.kind)


def _register_deathrattles(ids: List[str], cards: dict, zh: dict) -> None:
    from .deathrattle import DEATHRATTLE_BY_CARD
    for cid in ids:
        if cid in DEATHRATTLE_BY_CARD:
            continue
        spec = _DEATHRATTLE_SPECS.get(cid)
        if spec is None:
            continue
        DEATHRATTLE_BY_CARD[cid] = spec
        name = zh.get(cid) or cards.get(cid, {}).get("name") or cid
        _log("亡语", cid, name, spec.kind.value)


def _register_end_turn(ids: List[str], cards: dict, zh: dict) -> None:
    from .end_turn_board import END_TURN_BY_CARD
    for cid in ids:
        if cid in END_TURN_BY_CARD:
            continue
        spec = _END_TURN_SPECS.get(cid)
        if spec is None:
            continue
        END_TURN_BY_CARD[cid] = spec
        name = zh.get(cid) or cards.get(cid, {}).get("name") or cid
        _log("回合结束", cid, name, spec.kind.value)


def _ensure_board_modules_loaded() -> None:
    """加载各 BOARD 模块（须在 spell_board 完全初始化后调用）。"""
    from . import battlecry_board  # noqa: F401
    from . import rush_board  # noqa: F401
    from . import weapon_board  # noqa: F401
    from . import combo_board  # noqa: F401


def register_arena_season_gap() -> List[Tuple[str, str, str, str]]:
    """注册 ARENA_GAP_REPORT 中全部缺口卡，返回登记日志。"""
    global _BULK_DONE
    if _BULK_DONE:
        return list(_REGISTERED_LOG)
    _ensure_board_modules_loaded()
    _REGISTERED_LOG.clear()
    sections = _parse_gap_sections()
    if not sections:
        _BULK_DONE = True
        return []
    cards, zh = _load_cards()
    _register_spells(sections.get("spell", []), cards, zh)
    _register_battlecries(sections.get("battlecry", []), cards, zh)
    _register_rush_cards(sections.get("rush", []), cards, zh)
    _register_weapons(sections.get("weapon", []), cards, zh)
    _register_combos(sections.get("combo", []), cards, zh)
    _register_deathrattles(sections.get("deathrattle", []), cards, zh)
    _register_end_turn(sections.get("end_turn", []), cards, zh)
    _BULK_DONE = True
    return list(_REGISTERED_LOG)


def write_new_cards_md(path: Optional[Path] = None) -> Path:
    """将本次登记写入 ARENA_NEW_CARDS_ADDED.md。"""
    out = path or (DOCS / "ARENA_NEW_CARDS_ADDED.md")
    log = _REGISTERED_LOG or register_arena_season_gap()
    by_cat: Dict[str, List[Tuple[str, str, str]]] = {}
    for cat, cid, name, impl in log:
        by_cat.setdefault(cat, []).append((cid, name, impl))
    lines = [
        "# 竞技场新赛季新增接入卡牌",
        "",
        f"> 来源: `ARENA_GAP_REPORT.md` 缺口清单批量接入",
        f"> 合计: **{len(log)}** 条注册",
        "",
        "## 总览",
        "",
        "| 模块 | 新增数 |",
        "|------|--------|",
    ]
    for cat in ("法术", "战吼", "突袭", "武器", "连击", "亡语", "回合结束"):
        lines.append(f"| {cat} | {len(by_cat.get(cat, []))} |")
    lines.extend(["", "## 明细", ""])
    for cat in ("法术", "战吼", "突袭", "武器", "连击", "亡语", "回合结束"):
        items = by_cat.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat}（{len(items)}）")
        lines.append("")
        lines.append("| card_id | 中文名 | 实现 |")
        lines.append("|---------|--------|------|")
        for cid, name, impl in items:
            lines.append(f"| `{cid}` | {name} | {impl} |")
        lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- **完整**：效果与卡牌文本一致或接近")
    lines.append("- **简化/v1**：仅模拟主要伤害/场攻贡献，忽略发现、奥秘触发、延迟消灭等")
    lines.append("- 修改缺口清单后重新运行 `python scripts/export_arena_new_cards.py` 可刷新本文档")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
