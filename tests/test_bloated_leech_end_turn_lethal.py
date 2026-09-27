#!/usr/bin/env python3
"""饱胀水蛭 EDR_810t 回合结束偷血应计入斩杀。

复盘（2026-09-16 末回合）：对手最大生命已被偷至 29、受伤后剩 2 血，
场上两条饱胀水蛭回合结束各偷 1 点生命值 → 斩杀。此前未注册回合结束效果。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.end_turn_board import (
    END_TURN_BY_CARD,
    EtKind,
    end_turn_face_damage,
    _resolve_end_turn_def,
)
from hdt_python.spell_board import get_board_spell_def, hand_board_spells
from hdt_python.spell_p0_other import _apply_blood_treant_infection


def _hero(gs, eid, pid, *, dmg=0, mana=10, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["HEALTH"] = health
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", exhausted=0, ntp=1):
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
    # 已攻击：须同时设 EXHAUSTED 与 NUM_ATTACKS_THIS_TURN，否则会当作陈旧疲劳清掉
    m.tags["NUM_ATTACKS_THIS_TURN"] = 1 if exhausted else 0
    m.tags["EXHAUSTED"] = exhausted
    m.tags["NUM_TURNS_IN_PLAY"] = ntp
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


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


def _deck(gs, eid, pid):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "DECK"
    c.tags["ZONE"] = "DECK"
    return c


def test_bloated_leech_end_turn_registered():
    defn = _resolve_end_turn_def("EDR_810t")
    assert defn is not None
    assert defn.kind == EtKind.ATTACK_LOWEST_ENEMY
    assert defn.amount == 1
    assert "EDR_810t" in END_TURN_BY_CARD


def test_bloated_leech_end_turn_faces_empty_board():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=28, health=29)  # 1 血
    _minion(gs, 30, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    _minion(gs, 31, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    face, notes = end_turn_face_damage(gs.get_board(1), [], False, game_state=gs, player_id=1)
    assert face == 2, f"expected 2 from two leeches, got {face} {notes}"
    assert any("饱胀水蛭" in n for n in notes)


def test_ugly_remains_buffs_leech_steal():
    """丑恶的残躯在场：每条水蛭偷血 1+1=2；两条共 4，对手 4 血应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=14, health=18)  # 4 血
    _minion(gs, 40, 1, 3, 5, card_id="EDR_810", exhausted=1, ntp=0)
    _minion(gs, 41, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    _minion(gs, 42, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    for eid in (301, 302, 303):
        _deck(gs, eid, 2)

    face, notes = end_turn_face_damage(gs.get_board(1), [], False, game_state=gs, player_id=1)
    assert face == 4, f"expected 4 with Ugly Remains aura, got {face} {notes}"

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    assert lc.overlay_end_turn_face_for_display() >= 4
    assert lethal, f"should lethal total={total} note={lc.overlay_spell_note()}"


def test_bloated_leech_enables_lethal_after_face():
    """复盘：场面 17 打脸后剩 2 血，两条水蛭回合结束斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    # HEALTH 29 / DAMAGE 10 → 19 血；场面 9+2+4+2=17 + 水蛭 2 = 19
    _hero(gs, 20, 2, dmg=10, health=29)
    _minion(gs, 48, 1, 9, 5, card_id="CATA_722")
    _minion(gs, 167, 1, 2, 2, card_id="CATA_780t")
    _minion(gs, 168, 1, 4, 4, card_id="CATA_470")
    _minion(gs, 150, 1, 2, 2, card_id="CATA_780t")
    _minion(gs, 207, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    _minion(gs, 208, 1, 0, 2, card_id="EDR_810t", exhausted=1, ntp=0)
    for eid in (301, 302, 303):
        _deck(gs, eid, 2)

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    assert face >= 19, f"face={face}"
    assert lethal, f"should lethal total={total} face={face} note={lc.overlay_spell_note()}"
    assert lc.overlay_end_turn_face_for_display() >= 2


def test_blood_infection_summons_leeches_for_end_turn():
    assert get_board_spell_def("EDR_817") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=28, health=30)  # 2 血
    _minion(gs, 11, 1, 1, 1, card_id="CS2_189")  # 施放目标
    _hand_spell(gs, 40, 1, "EDR_817", 5)
    for eid in (301, 302):
        _deck(gs, eid, 2)

    fighters = [{"kind": "minion", "atk": 1, "health": 1, "card_id": "CS2_189", "attacks_left": 0}]
    _apply_blood_treant_infection([], fighters, mult=1, enemy_shield=False)
    assert sum(1 for f in fighters if f.get("card_id") == "EDR_810t") == 2

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 2, f"EDR_817 line should add 2 end-turn face, got {face} note={lc.overlay_spell_note()}"
    assert any(c.card_id == "EDR_817" for c, _, _ in hand_board_spells(gs, 1, 10))


def _hero_power(gs, eid, pid, card_id="HERO_11bp", cost=2):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = cost
    p.tags["ZONE"] = "PLAY"
    p.tags["COST"] = cost
    p.tags["EXHAUSTED"] = 0
    if not hasattr(gs, "hero_power_entity_ids"):
        gs.hero_power_entity_ids = {}
    gs.hero_power_entity_ids[pid] = eid
    return p


def test_infested_breath_not_direct_prefix_tier():
    """感染吐息须走 combo（召唤水蛭回合结束），不能进无嘲讽直伤前缀。"""
    from hdt_python.spell_board import spell_sim_tier_for_card, SpellSimTier

    spell_sim_tier_for_card.cache_clear()
    assert spell_sim_tier_for_card("EDR_814") == SpellSimTier.UTILITY


def test_infested_breath_ghoul_leech_lethal():
    """复盘：对手 4 血；场面已攻完；技能食尸鬼 + 感染吐息(2+水蛭回1) = 4 斩。"""
    from hdt_python.spell_board import spell_sim_tier_for_card

    spell_sim_tier_for_card.cache_clear()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=4)
    _hero(gs, 20, 2, dmg=26, health=30)  # 4 血
    _minion(gs, 30, 1, 2, 3, card_id="JAIL_998", exhausted=1, ntp=2)
    _minion(gs, 31, 1, 1, 1, card_id="CATA_780t", exhausted=1, ntp=1)
    _hand_spell(gs, 40, 1, "EDR_814", 2)
    _hero_power(gs, 50, 1, "HERO_11bp", 2)
    for eid in (301, 302, 303):
        _deck(gs, eid, 2)

    lc = LethalChecker(gs)
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    assert face >= 4, f"face={face} note={note}"
    assert lethal, f"should lethal total={total} face={face} note={note}"
    assert "感染吐息" in note


if __name__ == "__main__":
    test_bloated_leech_end_turn_registered()
    test_bloated_leech_end_turn_faces_empty_board()
    test_ugly_remains_buffs_leech_steal()
    test_bloated_leech_enables_lethal_after_face()
    test_blood_infection_summons_leeches_for_end_turn()
    test_infested_breath_not_direct_prefix_tier()
    test_infested_breath_ghoul_leech_lethal()
    print("ok")
