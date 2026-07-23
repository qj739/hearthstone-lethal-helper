# hero_power_p0.py — 英雄技能 P0（恶魔猎手 / 法师 / 德鲁伊 / 猎人 / 盗贼 / 死亡骑士 / 迦拉克隆）

from __future__ import annotations

from typing import List, TYPE_CHECKING

from .spell_board import (
    BoardSpellDef, SpellApplyResult, _add_temp_hero_attack, _summon_friendly_fighter,
)
from .hero_power_board import _register_hero_power
from .weapon_p0 import _equip

if TYPE_CHECKING:
    from .power_parser import Entity, GameState


def _apply_dh_claws(attack: int):
    def _fn(
        t,
        f: List[dict],
        *,
        mult: int,
        gs=None,
        player_id=None,
        next_turn_preview: bool = False,
        **_kw,
    ) -> SpellApplyResult:
        """恶魔之爪：本回合 +N 攻；不提供额外攻击次数。

        若场面已有英雄/武器挥击，则并入其攻击；否则仅在英雄仍有剩余攻击次数时
        新建挥击（避免英雄已攻击后再造假挥击，误触发审判官跟刀）。
        """
        bonus = attack * mult
        if bonus <= 0:
            return SpellApplyResult()
        for fighter in f:
            if (
                fighter.get("kind") in ("hero", "weapon")
                and fighter.get("attacks_left", 0) > 0
                and fighter.get("health", 0) > 0
                and fighter.get("can_face", True)
            ):
                fighter["atk"] = int(fighter.get("atk", 0) or 0) + bonus
                return SpellApplyResult()
        for fighter in f:
            if (
                fighter.get("kind") in ("hero", "weapon")
                and fighter.get("attacks_left", 0) > 0
                and fighter.get("health", 0) > 0
            ):
                fighter["atk"] = int(fighter.get("atk", 0) or 0) + bonus
                return SpellApplyResult()
        if not next_turn_preview and gs is not None and player_id is not None:
            from .board_damage import hero_has_unused_attack_slot

            hero = gs.get_hero(player_id)
            if hero is None or not hero_has_unused_attack_slot(
                hero, gs.get_weapon(player_id), active_turn=True,
            ):
                return SpellApplyResult()
        _add_temp_hero_attack(f, bonus, from_hero_power=True)
        return SpellApplyResult()

    return _fn


def _apply_mage_fireblast(t, f: List[dict], *, mult: int, enemy_shield: bool = False, **_kw) -> SpellApplyResult:
    """火焰冲击：1 点定向伤害（无嘲讽打脸；有嘲讽则打随从）。"""
    from .spell_board import (
        _apply_best_minion_damage,
        _apply_direct_face,
        _can_spell_hit_enemy_face,
    )

    dmg = 1 * mult
    if _can_spell_hit_enemy_face(t):
        return _apply_direct_face(dmg, enemy_shield)
    return _apply_best_minion_damage(t, f, dmg, enemy_shield=enemy_shield)


def _apply_druid_shapeshift(
    t,
    f: List[dict],
    *,
    mult: int,
    gs=None,
    player_id=None,
    next_turn_preview: bool = False,
    **_kw,
) -> SpellApplyResult:
    """变形：+1 攻（护甲 v1 不计场攻）；不提供额外攻击次数。"""
    return _apply_dh_claws(1)(
        t, f, mult=mult, gs=gs, player_id=player_id,
        next_turn_preview=next_turn_preview, **_kw,
    )


def _apply_hunter_steady_shot(t, f: List[dict], *, mult: int, enemy_shield: bool = False, **_kw) -> SpellApplyResult:
    """稳固射击：对敌方英雄造成 2 点伤害（无视嘲讽）。"""
    from .spell_board import _apply_direct_face

    return _apply_direct_face(2 * mult, enemy_shield)


def _apply_void_spike(t, f: List[dict], *, mult: int, enemy_shield: bool = False, **_kw) -> SpellApplyResult:
    """虔诚者泽瑞拉「虚空之刺」：对敌方英雄造成 5 点伤害（无视嘲讽）。"""
    from .spell_board import _apply_direct_face

    return _apply_direct_face(5 * mult, enemy_shield)


def _apply_dk_ghoul_charge(atk: int, health: int):
    def _fn(t, f: List[dict], *, mult: int = 1, **_kw) -> SpellApplyResult:
        """食尸鬼冲锋：召唤冲锋食尸鬼，当回合可解场/打脸。"""
        _summon_friendly_fighter(
            f, atk, health, charge=True, card_id="HERO_11bpt",
            from_hero_power=True,
        )
        return SpellApplyResult()

    return _fn


def _apply_rogue_dagger(atk: int, dur: int, card_id: str):
    def _fn(t, f: List[dict], *, mult: int, **_kw) -> SpellApplyResult:
        """匕首精通 / 浸毒匕首：装备匕首（替换已有武器）。"""
        _equip(f, atk, dur, card_id, mult=mult)
        return SpellApplyResult()

    return _fn


_register_hero_power(BoardSpellDef(
    ("__dh_claws_1",),
    1,
    "恶魔之爪",
    _apply_dh_claws(1),
))
_register_hero_power(BoardSpellDef(
    ("__dh_claws_2",),
    1,
    "恶魔之咬",
    _apply_dh_claws(2),
))
_register_hero_power(BoardSpellDef(
    ("__mage_fireblast_1",),
    2,
    "火焰冲击",
    _apply_mage_fireblast,
))
_register_hero_power(BoardSpellDef(
    ("__druid_shapeshift_1",),
    2,
    "变形",
    _apply_druid_shapeshift,
))
_register_hero_power(BoardSpellDef(
    ("__hunter_steady_2",),
    2,
    "稳固射击",
    _apply_hunter_steady_shot,
))
_register_hero_power(BoardSpellDef(
    ("__rogue_dagger_1_2",),
    2,
    "匕首精通",
    _apply_rogue_dagger(1, 2, "CS2_082"),
))
_register_hero_power(BoardSpellDef(
    ("__rogue_dagger_2_2",),
    2,
    "浸毒匕首",
    _apply_rogue_dagger(2, 2, "AT_132_ROGUEt"),
))
_register_hero_power(BoardSpellDef(
    ("__dk_ghoul_1_1",),
    2,
    "食尸鬼冲锋",
    _apply_dk_ghoul_charge(1, 1),
))
_register_hero_power(BoardSpellDef(
    ("__dk_ghoul_2_1",),
    2,
    "食尸鬼冲锋",
    _apply_dk_ghoul_charge(2, 1),
))
_register_hero_power(BoardSpellDef(
    ("CATA_190p",),
    2,
    "无情",
    _apply_dh_claws(5),
))
_register_hero_power(BoardSpellDef(
    ("AV_207p2",),
    2,
    "虚空之刺",
    _apply_void_spike,
))
