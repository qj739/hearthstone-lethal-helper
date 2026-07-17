# rush_p0.py — 竞技场突袭随从（59 张）场攻接入

from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_attack, hand_minion_health
from .rush_board import _register_rush, BOARD_RUSH
from .rush_combat import stamp_fighter_attack_effects
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _summon_friendly_fighter,
    hand_effect_active,
)

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

# 与 generate_arena_rush_worklist.collect 同步；动态加载失败时作兜底
_FALLBACK_RUSH_IDS: Tuple[str, ...] = (
    "VAC_514", "TOY_516", "TOY_312", "CATA_525", "CS3_020", "MIS_314", "DRG_076",
    "WW_418", "WORK_015", "BAR_896", "TSC_645", "SW_431", "ETC_357", "TTN_713",
    "DAL_047", "WW_326", "CATA_469", "CORE_BT_156", "TTN_042", "TLC_630",
    "CORE_DRG_079", "CATA_153", "VAC_527", "WW_043", "RLK_955", "RLK_604",
    "TIME_209", "BT_761", "TLC_243", "CORE_WC_701", "BT_720", "GDB_322",
    "TOY_811", "EDR_421", "TSC_007", "VAC_950", "WW_825", "YOG_506", "EDR_486",
    "REV_352", "TTN_466", "REV_375", "JAM_004", "ONY_004", "SW_062", "WW_808",
    "TIME_850", "DINO_401", "RLK_913", "RLK_916", "TOY_356", "TLC_240",
    "TSC_945", "TLC_366", "GDB_141", "BT_487", "SW_323", "TIME_029", "CATA_493",
)


def _tag_on(entity: Optional["Entity"], key: str) -> bool:
    if entity is None:
        return False
    return entity.tags.get(key, 0) == 1


def _hand_has_dragon(gs: Optional["GameState"], player_id: Optional[int]) -> bool:
    if gs is None or player_id is None:
        return False
    for card in gs.get_hand(player_id):
        if not card.is_minion:
            continue
        if _tag_on(card, "DRAGON") or card.tags.get("CARDRACE") in ("DRAGON", 24):
            return True
        races = card.tags.get("RACE") or card.tags.get("516")
        if races in ("DRAGON", 24):
            return True
    return False


def _summon_rush_fighter(
    fighters: List[dict],
    atk: int,
    hp: int,
    card_id: str = "",
    *,
    infused_cleave: bool = False,
    **kw,
) -> None:
    _summon_friendly_fighter(
        fighters, atk, hp, rush=True, card_id=card_id, **kw,
    )
    stamp_fighter_attack_effects(
        fighters[-1], card_id, infused_cleave=infused_cleave,
    )


def _summon_from_hand_card(
    fighters: List[dict],
    card: Optional["Entity"],
    *,
    mult: int = 1,
    atk_bonus: int = 0,
    hp_bonus: int = 0,
    rush: bool = True,
    infused_cleave: bool = False,
    **kw,
) -> None:
    if card is None:
        return
    cid = card.card_id or ""
    atk = hand_minion_attack(card) * mult + atk_bonus
    hp = hand_minion_health(card) * mult + hp_bonus
    _summon_rush_fighter(
        fighters, atk, hp, cid,
        infused_cleave=infused_cleave or (
            cid == "REV_352" and hand_effect_active(card)
        ),
        poisonous=_tag_on(card, "POISONOUS"),
        taunt=_tag_on(card, "TAUNT"),
        divine_shield=_tag_on(card, "DIVINE_SHIELD"),
        lifesteal=_tag_on(card, "LIFESTEAL"),
        windfury=_tag_on(card, "WINDFURY"),
        **kw,
    )


def _apply_default_rush_minion(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    _summon_from_hand_card(f, card, mult=mult)
    return SpellApplyResult()


def _apply_ruststeed_raider(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """锈骑劫匪：1/8 嘲讽突袭，战吼 +4 攻。"""
    _summon_rush_fighter(
        f, 1 * mult + 4 * mult, 8 * mult, "BT_720", taunt=True,
    )
    return SpellApplyResult()


def _apply_daring_drake(t, f, *, mult, card=None, gs=None, player_id=None, **_kw) -> SpellApplyResult:
    """胆大的幼龙：手牌有龙则 5/5 否则 4/4 突袭。"""
    bonus = 1 * mult if _hand_has_dragon(gs, player_id) else 0
    _summon_rush_fighter(f, 4 * mult + bonus, 4 * mult + bonus, "RLK_916")
    return SpellApplyResult()


def _apply_raid_boss_onyxia(t, f, *, mult, **_kw) -> SpellApplyResult:
    """团本首领奥妮克希亚：8/8 突袭 + 六条 2/1 突袭雏龙。"""
    _summon_rush_fighter(f, 8 * mult, 8 * mult, "ONY_004")
    for _ in range(6):
        _summon_rush_fighter(f, 2 * mult, 1 * mult, "ONY_004")
    return SpellApplyResult()


def _apply_angry_helhound(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """生气的冥狱之犬：2/5 突袭，你的回合 +4 攻。"""
    _summon_rush_fighter(f, 2 * mult + 4 * mult, 5 * mult, "TTN_713")
    return SpellApplyResult()


def _apply_silvermoon_armorer(t, f, *, mult, card=None, mana_budget=None, **_kw) -> SpellApplyResult:
    """银月城军备官：法力渴求(7) +2/+2。"""
    bonus = 2 * mult if mana_budget is not None and mana_budget >= 7 else 0
    _summon_rush_fighter(f, 4 * mult + bonus, 4 * mult + bonus, "RLK_955")
    return SpellApplyResult()


def _apply_coilfang_warlord(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(f, 9 * mult, 5 * mult, "BT_761")
    return SpellApplyResult()


def _apply_stoneborn_general(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(f, 8 * mult, 8 * mult, "REV_375")
    return SpellApplyResult()


def _apply_illidari_inquisitor(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """伊利达雷审判官：8/8 突袭，英雄攻击后跟刀。"""
    _summon_rush_fighter(f, 8 * mult, 8 * mult, "CS3_020")
    return SpellApplyResult()


def _apply_brass_elemental(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(
        f, 3 * mult, 3 * mult, "ETC_357",
        taunt=True, divine_shield=True, windfury=True,
    )
    return SpellApplyResult()


def _apply_walking_fountain(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(
        f, 4 * mult, 8 * mult, "DAL_047", lifesteal=True, windfury=True,
    )
    return SpellApplyResult()


def _apply_evasive_wyrm(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(
        f, 5 * mult, 4 * mult, "CORE_DRG_079", divine_shield=True,
    )
    return SpellApplyResult()


def _apply_tigress_plushy(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(
        f, 3 * mult, 2 * mult, "TOY_811",
        divine_shield=True, lifesteal=True,
    )
    return SpellApplyResult()


def _apply_hollow_hound(t, f, *, mult, **_kw) -> SpellApplyResult:
    """镂骨恶犬：吸血突袭顺劈。"""
    _summon_rush_fighter(f, 3 * mult, 4 * mult, "JAM_004", lifesteal=True)
    return SpellApplyResult()


def _apply_shadehound(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """影犬（注能 MAW_009t）：突袭；攻击时使其他友方野兽 +2/+2。"""
    _summon_from_hand_card(f, card, mult=mult)
    return SpellApplyResult()


def _apply_felrattler(t, f, *, mult, **_kw) -> SpellApplyResult:
    _summon_rush_fighter(f, 3 * mult, 2 * mult, "CORE_WC_701")
    return SpellApplyResult()


def _apply_bargain_bin_buccaneer(
    t, f, *, mult, card=None, combo_active=False, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """折价区海盗：亮边（连击）召唤复制。"""
    _summon_from_hand_card(f, card, mult=mult)
    if hand_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ):
        _summon_from_hand_card(f, card, mult=mult)
    return SpellApplyResult()


# card_id -> (base_cost, name, apply_fn)
_RUSH_OVERRIDES = {
    "BT_720": (5, "锈骑劫匪", _apply_ruststeed_raider),
    "RLK_916": (4, "胆大的幼龙", _apply_daring_drake),
    "ONY_004": (10, "团本首领奥妮克希亚", _apply_raid_boss_onyxia),
    "TTN_713": (4, "生气的冥狱之犬", _apply_angry_helhound),
    "RLK_955": (4, "银月城军备官", _apply_silvermoon_armorer),
    "BT_761": (8, "盘牙督军", _apply_coilfang_warlord),
    "REV_375": (10, "石裔干将", _apply_stoneborn_general),
    "CS3_020": (8, "伊利达雷审判官", _apply_illidari_inquisitor),
    "ETC_357": (4, "铜管元素", _apply_brass_elemental),
    "DAL_047": (8, "活动喷泉", _apply_walking_fountain),
    "CORE_DRG_079": (6, "辟法巨龙", _apply_evasive_wyrm),
    "TOY_811": (3, "绒绒虎", _apply_tigress_plushy),
    "JAM_004": (6, "镂骨恶犬", _apply_hollow_hound),
    "MAW_009t": (5, "影犬", _apply_shadehound),
    "CORE_MAW_009t": (5, "影犬", _apply_shadehound),
    # 未注能牌面无突袭；手牌若已亮边/获得突袭也可按同逻辑召唤
    "MAW_009": (5, "影犬", _apply_shadehound),
    "CORE_MAW_009": (5, "影犬", _apply_shadehound),
    "CORE_WC_701": (3, "邪能响尾蛇", _apply_felrattler),
    "TOY_516": (3, "折价区海盗", _apply_bargain_bin_buccaneer),
}

_RANDOM_RUSH_IDS = frozenset({"WW_418"})


def _load_arena_rush_meta() -> List[tuple[str, int, str]]:
    try:
        from pathlib import Path
        import sys

        root = Path(__file__).resolve().parents[2]
        scripts = root / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from generate_arena_rush_worklist import collect as collect_rush  # noqa: WPS433

        items, _, _ = collect_rush()
        return [(it["cid"], it["cost"], it["name_zh"]) for it in items]
    except Exception:
        return [(cid, 0, cid) for cid in _FALLBACK_RUSH_IDS if cid != "DRG_076"]


def _register_all_rush_minions() -> None:
    from .battlecry_board import BOARD_BATTLECRY

    seen: set[str] = set()
    for cid, cost, name in _load_arena_rush_meta():
        if cid in seen or cid in BOARD_BATTLECRY:
            continue
        seen.add(cid)
        if cid in _RUSH_OVERRIDES:
            base_cost, zh, apply_fn = _RUSH_OVERRIDES[cid]
            _register_rush(BoardSpellDef(
                (cid,), base_cost or cost, zh, apply_fn,
                uses_random=cid in _RANDOM_RUSH_IDS,
            ))
            continue
        _register_rush(BoardSpellDef(
            (cid,), cost or 0, name, _apply_default_rush_minion,
            uses_random=cid in _RANDOM_RUSH_IDS,
        ))
    # 覆盖表中但未进突袭清单的牌（如注能后才有突袭的影犬 MAW_009t）
    for cid, (base_cost, zh, apply_fn) in _RUSH_OVERRIDES.items():
        if cid in seen or cid in BOARD_BATTLECRY or cid in BOARD_RUSH:
            continue
        _register_rush(BoardSpellDef(
            (cid,), base_cost, zh, apply_fn,
            uses_random=cid in _RANDOM_RUSH_IDS,
        ))
        seen.add(cid)


_register_all_rush_minions()
