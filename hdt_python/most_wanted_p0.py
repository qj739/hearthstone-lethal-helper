# most_wanted_p0.py — 艾泽拉斯头号通缉（CAP_）斩杀接入
#
# Patch 36.4 职业套装：牧师/潜行者/术士/战士 + 通缉海报。
# 火炮手体系（CAP_107t / Crowley / Hand Cannon）为 P0；其余按文本做可计算线。

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

from .board_damage import hand_minion_attack, hand_minion_health
from .end_turn_board import END_TURN_BY_CARD, EndTurnDef, EtKind
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_buff_to_spell_target,
    _apply_optimal_single_target_damage,
    _apply_random_destroy_enemy_minions,
    _apply_random_enemy_hits,
    _apply_random_minion_hits,
    _pick_best_spell_target_fighter,
    _register,
    _summon_friendly_fighter,
    hand_effect_active,
    scaled_spell_damage as _sd,
)
from .spell_p0_remove import _apply_cataclysm

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

MC_DEFAULT_SEED = 0
CANNONEER_TOKEN_ID = "CAP_107t"
GHOST_TOKEN_ID = "CAP_802t"
_REGISTERED = False


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def _summon_cannoneers(fighters: List[dict], count: int = 2, *, mult: int = 1) -> None:
    for _ in range(max(0, int(count)) * max(int(mult), 1)):
        _summon_friendly_fighter(
            fighters, 1, 1, card_id=CANNONEER_TOKEN_ID,
        )
        fighters[-1]["sim_summon"] = True


def _unit_is_stealthed(unit: dict, gs=None, player_id=None) -> bool:
    if unit.get("stealth"):
        return True
    eid = unit.get("entity_id")
    if gs is None or eid is None:
        return False
    ent = gs.get_entity(eid)
    if ent is None:
        return False
    return int(ent.tags.get("STEALTH", 0) or 0) == 1


# --- 法术 ---

def _apply_silent_strike(
    taunts, fighters, *, mult, enemy_shield, spell_power=0,
    rng=None, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """静默打击：友方+3攻；若潜行，再对随机敌方随从造成等同其攻击的伤害。"""
    from .spell_board import _friendly_spell_target_minions

    candidates = []
    for item in _friendly_spell_target_minions(fighters, gs, player_id):
        unit = item[2]
        stealth = _unit_is_stealthed(unit, gs, player_id)
        ready = int(unit.get("attacks_left", 0) or 0) > 0
        atk = int(unit.get("atk", 0) or 0)
        candidates.append((stealth, ready, atk, item))
    if not candidates:
        return SpellApplyResult()
    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    picked = candidates[0][3]
    bonus = _sd(3, mult=mult, spell_power=0)
    _apply_buff_to_spell_target(
        fighters, picked, bonus_atk=bonus, bonus_health=0,
    )
    unit = picked[2]
    src, key, _ = picked
    if src == "fighter":
        unit = fighters[int(key)]
    else:
        for f in fighters:
            if f.get("entity_id") == key:
                unit = f
                break
    if not _unit_is_stealthed(unit, gs, player_id):
        return SpellApplyResult()
    dmg = max(0, int(unit.get("atk", 0) or 0))
    if dmg <= 0:
        return SpellApplyResult()
    return _apply_random_minion_hits(
        taunts, fighters, hits=1, damage=dmg,
        enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_tricks_of_trade(
    taunts, fighters, *, mult, enemy_shield, spell_power=0,
    card=None, combo_active=False, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """嫁祸诀窍：1 伤；手中时有潜行随从攻击过（亮边）则 3 伤。"""
    dmg = 3 if hand_effect_active(
        card, combo_active=combo_active, gs=gs, player_id=player_id,
    ) else 1
    return _apply_optimal_single_target_damage(
        taunts, fighters,
        _sd(dmg, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
    )


def _apply_follow_fuse(
    taunts, fighters, *, mult, enemy_shield, spell_power=0, rng=None, **_kw,
) -> SpellApplyResult:
    """跟随引线：随机对一个敌人 2 伤（发现/挂效 v1 忽略）。"""
    return _apply_random_enemy_hits(
        taunts, fighters,
        hits=1,
        damage=_sd(2, mult=mult, spell_power=spell_power),
        enemy_shield=enemy_shield,
        rng=_rng(rng),
    )


def _apply_land_ho(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """眺望陆地：抽 2（忽略）+ 召唤两个火炮手。"""
    _summon_cannoneers(fighters, 2, mult=mult)
    return SpellApplyResult()


def _apply_hook_n_heave(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """钩手拖曳：发现海盗（忽略）+ 召唤两个火炮手。"""
    _summon_cannoneers(fighters, 2, mult=mult)
    return SpellApplyResult()


def _apply_follow_ghosts(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """跟随幽灵：召唤 2/1 复生幽灵（挂效 v1 忽略）。"""
    for _ in range(max(int(mult), 1)):
        _summon_friendly_fighter(
            fighters, 2, 1, card_id=GHOST_TOKEN_ID,
        )
        fighters[-1]["reborn"] = True
        fighters[-1]["sim_summon"] = True
    return SpellApplyResult()


def _apply_haunt(
    taunts, fighters, *, mult, enemy_shield, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """幽魂不散：友方 +2/+3、复生、嘲讽。"""
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=player_id)
    if picked is None:
        return SpellApplyResult()
    _apply_buff_to_spell_target(
        fighters, picked,
        bonus_atk=_sd(2, mult=mult, spell_power=0),
        bonus_health=_sd(3, mult=mult, spell_power=0),
        grant_taunt=True,
    )
    src, key, unit = picked
    target = None
    if src == "fighter":
        target = fighters[int(key)]
    else:
        for f in fighters:
            if f.get("entity_id") == key:
                target = f
                break
    if target is not None:
        target["reborn"] = True
        target["taunt"] = True
    return SpellApplyResult()


def _apply_frame_job(
    taunts, fighters, *, mult, enemy_shield, rng=None, **_kw,
) -> SpellApplyResult:
    """陷害：随机消灭两个敌方随从（发现牌库顶 v1 忽略）。"""
    return _apply_random_destroy_enemy_minions(
        taunts, fighters, count=2 * max(int(mult), 1), rng=_rng(rng),
    )


def _apply_slime_em(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """灵质处决：消灭所有随从（获取回召法术 v1 忽略）。"""
    return _apply_cataclysm(taunts, fighters)


def _apply_noop_spell(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    return SpellApplyResult()


# --- 战吼 ---

def _apply_crowley(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """克罗雷船长：上场 + 召唤两个火炮手（额外开火由光环处理）。"""
    atk = hand_minion_attack(card) if card is not None else 4
    hp = hand_minion_health(card) if card is not None else 5
    _summon_friendly_fighter(
        f, atk * mult, hp * mult, card_id="CAP_106", aura=True,
    )
    _summon_cannoneers(f, 2, mult=mult)
    return SpellApplyResult()


def _apply_cannonmaster(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """火炮长：上场；战吼获取火炮手牌（本回合斩杀线无直接伤害）。"""
    atk = hand_minion_attack(card) if card is not None else 3
    hp = hand_minion_health(card) if card is not None else 1
    _summon_friendly_fighter(f, atk * mult, hp * mult, card_id="CAP_107")
    return SpellApplyResult()


def _apply_specter_specialist(
    t, f, *, mult, card=None, gs=None, player_id=None, **_kw,
) -> SpellApplyResult:
    """捉鬼专家：友方获得复生；已有则复制。"""
    atk = hand_minion_attack(card) if card is not None else 3
    hp = hand_minion_health(card) if card is not None else 2
    before_ids = {
        u.get("entity_id")
        for u in f
        if u.get("kind") == "minion" and u.get("health", 0) > 0
    }
    _summon_friendly_fighter(f, atk * mult, hp * mult, card_id="CAP_804")
    picked = None
    best = None
    for i, unit in enumerate(f):
        if unit.get("kind") != "minion" or unit.get("health", 0) <= 0:
            continue
        if unit.get("entity_id") not in before_ids:
            continue
        rank = (
            1 if unit.get("reborn") else 0,
            1 if int(unit.get("attacks_left", 0) or 0) > 0 else 0,
            int(unit.get("atk", 0) or 0),
        )
        if best is None or rank > best:
            best = rank
            picked = ("fighter", i, unit)
    if picked is None and gs is not None and player_id is not None:
        picked = _pick_best_spell_target_fighter(f, gs=gs, player_id=player_id)
        if picked is not None and picked[2].get("entity_id") not in before_ids:
            picked = None
    if picked is None:
        return SpellApplyResult()
    src, key, unit = picked
    target = f[int(key)] if src == "fighter" else None
    if target is None:
        for u in f:
            if u.get("entity_id") == key:
                target = u
                break
    if target is None:
        return SpellApplyResult()
    if target.get("reborn"):
        _summon_friendly_fighter(
            f,
            int(target.get("atk", 0) or 0),
            int(target.get("health", 0) or 0),
            rush=bool(target.get("rush")),
            charge=bool(target.get("charge")),
            card_id=str(target.get("card_id") or ""),
        )
    else:
        target["reborn"] = True
    return SpellApplyResult()


def _apply_kabal_mastermind(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """暗金教主谋：嘲讽上场（小鬼光环本回合斩杀忽略）。"""
    atk = hand_minion_attack(card) if card is not None else 5
    hp = hand_minion_health(card) if card is not None else 5
    _summon_friendly_fighter(
        f, atk * mult, hp * mult, taunt=True, card_id="CAP_406",
    )
    return SpellApplyResult()


def _apply_body_only_bc(cid: str, default_atk: int, default_hp: int, *, taunt: bool = False):
    def _fn(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
        atk = hand_minion_attack(card) if card is not None else default_atk
        hp = hand_minion_health(card) if card is not None else default_hp
        _summon_friendly_fighter(
            f, atk * mult, hp * mult, taunt=taunt, card_id=cid,
        )
        return SpellApplyResult()
    return _fn


def _apply_hand_cannon(t, f, *, mult, card=None, **_kw) -> SpellApplyResult:
    """手持火炮：英雄攻击后火炮手开火。"""
    from .weapon_p0 import _equip, _weapon_stats_from_card

    wa, wd = _weapon_stats_from_card(card, 3, 2)
    _equip(
        f, wa, wd, "CAP_103", mult=mult,
        cannoneers_fire=True, **_kw,
    )
    return SpellApplyResult()


def register_most_wanted() -> None:
    """注册 CAP_ 卡牌（幂等；须在 spell_board / battlecry 等模块就绪后调用）。"""
    global _REGISTERED
    if _REGISTERED:
        return

    from .battlecry_board import _register_bc
    from . import end_turn_hand_board as eth
    from .rush_board import _register_rush
    from .rush_p0 import _apply_default_rush_minion
    from .weapon_board import _register_weapon
    from .weapon_p0 import WEAPON_AFTER_ATTACK_META

    # 火炮手回合结束
    END_TURN_BY_CARD[CANNONEER_TOKEN_ID] = EndTurnDef(
        EtKind.RANDOM_SPLIT_ENEMIES, amount=1, uses_random=True, name="火炮手",
    )
    eth.HAND_END_TURN_PLAY_IDS = frozenset(
        set(eth.HAND_END_TURN_PLAY_IDS) | {CANNONEER_TOKEN_ID}
    )
    eth._register_hand_end_turn(BoardSpellDef(
        (CANNONEER_TOKEN_ID,), 1, "火炮手",
        eth._apply_play_end_turn_minion,
        uses_random=True,
    ))

    spell_specs = [
        (("CAP_001",), 2, "静默打击", _apply_silent_strike, True),
        (("CAP_006",), 1, "嫁祸诀窍", _apply_tricks_of_trade, False),
        (("CAP_002",), 1, "跟随足迹", _apply_noop_spell, False),
        (("CAP_101",), 1, "跟随引线", _apply_follow_fuse, True),
        (("CAP_102",), 4, "眺望陆地", _apply_land_ho, False),
        (("CAP_105",), 2, "钩手拖曳", _apply_hook_n_heave, False),
        (("CAP_402",), 1, "跟随证据", _apply_noop_spell, False),
        (("CAP_403",), 5, "陷害", _apply_frame_job, True),
        (("CAP_404",), 2, "强力裁决", _apply_noop_spell, False),
        (("CAP_407",), 2, "通缉海报", _apply_noop_spell, False),
        (("CAP_801",), 3, "幽魂不散", _apply_haunt, False),
        (("CAP_802",), 2, "跟随幽灵", _apply_follow_ghosts, False),
        (("CAP_805",), 4, "灵质处决", _apply_slime_em, False),
    ]
    for card_ids, cost, name, fn, uses_random in spell_specs:
        _register(BoardSpellDef(
            card_ids=card_ids, base_cost=cost, name=name,
            apply=fn, uses_random=uses_random,
        ))

    bc_specs = [
        (("CAP_106",), 5, "克罗雷船长", _apply_crowley, False),
        (("CAP_107",), 1, "火炮长", _apply_cannonmaster, False),
        (("CAP_804",), 3, "捉鬼专家", _apply_specter_specialist, False),
        (("CAP_406",), 5, "暗金教主谋", _apply_kabal_mastermind, False),
        (("CAP_401",), 4, "腐败警员",
         _apply_body_only_bc("CAP_401", 3, 5), False),
        (("CAP_405",), 3, "教父卡扎库斯",
         _apply_body_only_bc("CAP_405", 3, 3), False),
        (("CAP_806",), 7, "雷斯·范盖斯特",
         _apply_body_only_bc("CAP_806", 5, 5), False),
    ]
    for card_ids, cost, name, fn, uses_random in bc_specs:
        _register_bc(BoardSpellDef(
            card_ids=card_ids, base_cost=cost, name=name,
            apply=fn, uses_random=uses_random,
        ))

    _register_rush(BoardSpellDef(
        ("CAP_004",), 1, "伪装的特工", _apply_default_rush_minion,
    ))

    _register_weapon(BoardSpellDef(
        ("CAP_103",), 3, "手持火炮", _apply_hand_cannon,
    ))
    WEAPON_AFTER_ATTACK_META["CAP_103"] = {"cannoneers_fire": True}

    _REGISTERED = True


# 模块导入即注册（调用方须在 spell_board 初始化完成后 import）
register_most_wanted()
