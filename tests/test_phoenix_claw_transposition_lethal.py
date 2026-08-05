#!/usr/bin/env python3
"""恶魔之爪 + 0 费火羽凤凰：勿被「爪后红牌空过」置换剪枝漏斩。

对齐 2026-08-05：剩 1 费、武器 3、场面 4、手牌 0 费凤凰战吼 3 + 1 费红牌，
对手 11 血。正确线：爪(+1) + 场攻 + 战吼 = 11。若指纹不计战吼打脸，
爪+红牌（买不起空过）会与爪+凤凰撞指纹，漏掉斩杀。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import SpellApplyResult, spell_sequence_transposition_key


def _hero(gs, eid, pid, *, mana=10, used=0, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.atk = atk
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["ATK"] = atk
    h.tags["EXHAUSTED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hero_power(gs, eid, pid, card_id="HERO_10bp", cost=1):
    hp = gs.get_entity(eid)
    hp.cardtype = "HERO_POWER"
    hp.controller = pid
    hp.zone = "PLAY"
    hp.card_id = card_id
    hp.cost = cost
    hp.tags.update({
        "ZONE": "PLAY", "CARDTYPE": "HERO_POWER", "COST": cost, "EXHAUSTED": 0,
    })
    return hp


def _weapon(gs, eid, pid, card_id, atk, health, damage=0):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.health = health
    w.damage = damage
    w.durability = health
    w.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": health, "DAMAGE": damage, "EXHAUSTED": 0,
    })
    gs.weapon_entity_ids[pid] = eid
    return w


def _board_minion(gs, eid, pid, card_id, atk, hp, *, can_attack=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "EXHAUSTED": 0 if can_attack else 1,
        "NUM_ATTACKS_THIS_TURN": 0,
        "NUM_TURNS_IN_PLAY": 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.zone_pos = pos
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_card(gs, eid, pid, card_id, cost, *, cardtype="MINION", atk=0, hp=1):
    c = gs.get_entity(eid)
    c.cardtype = cardtype
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.atk = atk
    c.health = hp
    c.tags.update({"ZONE": "HAND", "COST": cost, "ATK": atk, "HEALTH": hp})
    return c


def test_transposition_key_includes_battlecry_face():
    """战吼打脸必须进指纹，否则与空序列/空过序列撞键。"""
    empty = SpellApplyResult()
    with_bc = SpellApplyResult(battlecry_face_damage=3)
    k0 = spell_sequence_transposition_key([], [], empty, hero_hp=30, mana_left=0)
    k1 = spell_sequence_transposition_key([], [], with_bc, hero_hp=30, mana_left=0)
    assert k0 != k1, (k0, k1)


def test_phoenix_claw_not_pruned_by_red_card_noop():
    """1 费：爪 + 场 4 + 武器 3→4 + 凤凰战吼 3 = 11，应斩对手 11 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    # 奇数回合 + first_player=1 → 我方回合（避免疲劳/下回合预估干扰）
    game.tags["TURN"] = 11
    p1 = gs.get_entity(3)
    p1.cardtype = "PLAYER"
    p1.controller = 1
    p1.tags["CURRENT_PLAYER"] = 1

    _hero(gs, 1, 1, mana=9, used=8, atk=3)
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.damage = 19  # 11 血
    # 对手牌库非空，避免疲劳 +1 把「差 1 点」抬成假斩杀
    for i, deid in enumerate((200, 201, 202), start=1):
        d = gs.get_entity(deid)
        d.controller = 2
        d.zone = "DECK"
        d.tags["ZONE"] = "DECK"

    _hero_power(gs, 10, 1, "HERO_10bp", 1)
    _weapon(gs, 20, 1, "JAIL_730", 3, 3, damage=2)
    _board_minion(gs, 30, 1, "CORE_UNG_084", 3, 4)
    _board_minion(gs, 31, 1, "TIME_058", 1, 1)
    # 0 费凤凰战吼 3；1 费红牌（爪后买不起，空过会撞指纹）
    _hand_card(gs, 40, 1, "CORE_UNG_084", 0, atk=3, hp=4)
    _hand_card(gs, 41, 1, "TOY_644", 1, cardtype="SPELL")

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note() or ""
    assert getattr(lc, "_overlay_fatigue_face", 0) == 0, "test setup: no fatigue"
    assert face >= 11, (face, note, lc.overlay_board_breakdown())
    assert has, (face, has, note)
    assert "火羽凤凰" in note, note
    hp_name = getattr(lc, "_overlay_best_hp_name", None)
    assert "恶魔之爪" in note or hp_name == "恶魔之爪", (note, hp_name)


if __name__ == "__main__":
    test_transposition_key_includes_battlecry_face()
    test_phoenix_claw_not_pruned_by_red_card_noop()
    print("OK phoenix claw transposition lethal")
