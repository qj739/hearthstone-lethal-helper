#!/usr/bin/env python3
"""尸骨火炮攻后召唤冲锋食尸鬼 + 拦住他们！应识别斩杀。

复盘（Power.log 倒数第二回合）：对手 21 血空场，场面 6+3+4，
尸骨火炮 1 攻；拦住他们！+5 后英雄挥击召 1/1 冲锋 + 技能再召 1/1 = 21。
漏斩根因：JAIL_450 攻击后召唤未建模，场攻停在 20。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.weapon_p0 import (
    WEAPON_AFTER_ATTACK_META,
    apply_summon_on_attack,
    stamp_equipped_weapon_effects,
)


def _hero(gs, eid, pid, *, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.atk = atk
    h.tags["DAMAGE"] = dmg
    h.tags["ATK"] = atk
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, atk, dur, *, damage=0, card_id="JAIL_450"):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.health = dur
    w.damage = damage
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["HEALTH"] = dur
    w.tags["DURABILITY"] = dur
    w.tags["DAMAGE"] = damage
    if not hasattr(gs, "weapon_entity_ids"):
        gs.weapon_entity_ids = {}
    gs.weapon_entity_ids[pid] = eid
    return w


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def _hero_power(gs, eid, pid, card_id="HERO_11bp"):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = 2
    p.tags["ZONE"] = "PLAY"
    p.tags["COST"] = 2
    p.tags["EXHAUSTED"] = 0
    p.tags["HEROPOWER_ACTIVATIONS_THIS_TURN"] = 0
    if not hasattr(gs, "hero_power_entity_ids"):
        gs.hero_power_entity_ids = {}
    gs.hero_power_entity_ids[pid] = eid
    return p


def _deck_card(gs, eid, pid):
    """给对手牌库塞牌，避免空库疲劳把 20 误抬成 21。"""
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "DECK"
    c.card_id = "CS2_189"
    c.tags["ZONE"] = "DECK"
    return c


def _scene(*, with_spell=True, with_hp=True, opp_dmg=9, mana=8):
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 68, 1, mana=mana, atk=1)
    _hero(gs, 70, 2, dmg=opp_dmg)
    _weapon(gs, 32, 1, 1, 3, damage=2)
    _minion(gs, 17, 1, 6, 4, card_id="END_004")
    _minion(gs, 149, 1, 3, 4, card_id="CATA_474")
    _minion(gs, 151, 1, 4, 3, card_id="END_002")
    if with_spell:
        # 矛心哨兵回合结束圣法术 -3：日志 COST=2
        _hand_spell(gs, 156, 1, "JAIL_913", 2)
    if with_hp:
        _hero_power(gs, 69, 1)
    for i, eid in enumerate((201, 202, 203), start=1):
        _deck_card(gs, eid, 2)
    h = gs.get_entity(68)
    h.atk = 1
    h.tags["ATK"] = 1
    h.tags["479"] = 1
    return gs


def test_jail_450_meta_summons_charge_ghoul():
    meta = WEAPON_AFTER_ATTACK_META["JAIL_450"]
    assert meta["summon_on_attack"] == (1, 1)
    assert meta.get("summon_on_attack_charge") is True

    fighters: list = []
    weapon = {"kind": "weapon", "health": 30, "card_id": "JAIL_450"}
    stamp_equipped_weapon_effects(weapon, "JAIL_450")
    n = apply_summon_on_attack(weapon, fighters)
    assert n == 1
    assert fighters[0]["atk"] == 1
    assert fighters[0]["attacks_left"] == 1
    assert fighters[0]["can_face"] is True
    assert fighters[0]["card_id"] == "HERO_11bpt"


def test_corpse_cannon_hold_them_lethal():
    """拦住他们！+ 尸骨火炮召鬼 + 技能召鬼 → 21 斩 21 血。"""
    gs = _scene()
    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    assert face >= 21, f"face={face} note={note}"
    assert lethal, f"should lethal total={total} face={face} note={note}"
    assert "拦住" in note or "JAIL_913" in note or face >= 21


def test_without_cannon_summon_short_of_lethal():
    """若武器不召鬼，仅 buff+技能 = 20，不应靠疲劳假斩。"""
    gs = _scene(with_spell=True, with_hp=True)
    # 临时拆掉 meta，确认回归依赖召唤而非疲劳
    old = WEAPON_AFTER_ATTACK_META.pop("JAIL_450", None)
    try:
        lc = LethalChecker(gs)
        face = lc.overlay_board_face_damage()
        # 允许技能线到 20；关键是没有疲劳把线抬到 21
        assert lc.overlay_fatigue_face() == 0
        assert face < 21, f"without cannon summon expected <21 got {face}"
    finally:
        if old is not None:
            WEAPON_AFTER_ATTACK_META["JAIL_450"] = old


if __name__ == "__main__":
    test_jail_450_meta_summons_charge_ghoul()
    test_corpse_cannon_hold_them_lethal()
    test_without_cannon_summon_short_of_lethal()
    print("ok")
