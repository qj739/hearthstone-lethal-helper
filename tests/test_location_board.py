#!/usr/bin/env python3
"""地标：赎罪教堂 +2/+1 目标选择与可用性。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.location_board import board_location_plays, location_is_ready
from hdt_python.location_p0 import pick_cathedral_buff_target, erupting_volcano_total_damage
from hdt_python.lethal_checker import _clone_combat_states
from hdt_python.spell_board import (
    apply_spell_sequence_with_meta,
    get_board_spell_def,
)
from hdt_python.combat_sim import fighters_face_damage


def _set_local_turn(gs, local=1):
    gs.game_entity_id = 100
    ge = gs.get_entity(100)
    ge.cardtype = "GAME"
    ge.tags["TURN"] = 10
    ge.tags["CURRENT_PLAYER"] = local
    gs.first_player_id = local


def _hero(gs, eid, pid, hp=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.zone = "PLAY"
    h.health = hp
    h.tags["ZONE"] = "PLAY"
    h.tags["RESOURCES"] = 10
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, pos, card_id="", can_attack=True, windfury=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY",
        "ATK": atk,
        "HEALTH": hp,
        "ZONE_POSITION": pos,
    })
    if can_attack:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    else:
        m.tags["NUM_TURNS_IN_PLAY"] = 0
        m.tags["EXHAUSTED"] = 1
    if windfury:
        m.tags["WINDFURY"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid


def _location(gs, eid, pid, *, pos, dur=3, ready=True):
    loc = gs.get_entity(eid)
    loc.cardtype = "LOCATION"
    loc.controller = pid
    loc.zone = "PLAY"
    loc.card_id = "REV_290"
    loc.health = dur
    loc.damage = 0
    loc.tags.update({
        "ZONE": "PLAY",
        "CARDTYPE": "LOCATION",
        "HEALTH": dur,
        "ZONE_POSITION": pos,
    })
    if not ready:
        loc.tags["EXHAUSTED"] = 1
        loc.tags["LOCATION_ACTION_COOLDOWN"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid


def test_location_ready_and_plays():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _location(gs, 47, 1, pos=1, ready=True)
    _minion(gs, 10, 1, 5, 5, pos=2, can_attack=True)
    assert location_is_ready(gs.get_entity(47))
    plays = board_location_plays(gs, 1, 10)
    assert len(plays) == 1
    assert plays[0][0].card_id == "REV_290"
    print("OK location ready plays", len(plays))


def test_location_cooldown_not_offered():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _location(gs, 47, 1, pos=1, ready=False)
    _minion(gs, 10, 1, 3, 3, pos=2, can_attack=True)
    assert not location_is_ready(gs.get_entity(47))
    assert board_location_plays(gs, 1, 10) == []
    print("OK location cooldown excluded")


def test_cathedral_prefers_windfury_lowest_atk():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5, pos=2, can_attack=True)
    _minion(gs, 11, 1, 2, 2, pos=3, can_attack=True, windfury=True)
    _minion(gs, 12, 1, 3, 3, pos=4, can_attack=True, windfury=True)
    t = pick_cathedral_buff_target(gs, 1)
    assert t.entity_id == 11, f"expected wf 2/2, got {t.entity_id}"
    print("OK cathedral windfury priority", t.entity_id)


def test_cathedral_lowest_atk_without_windfury():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 8, 8, pos=2, can_attack=True)
    _minion(gs, 11, 1, 3, 3, pos=3, can_attack=True)
    t = pick_cathedral_buff_target(gs, 1)
    assert t.entity_id == 11
    print("OK cathedral lowest atk", t.entity_id)


def test_cathedral_skips_non_attackable():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _location(gs, 47, 1, pos=1, ready=True)
    _minion(gs, 10, 1, 12, 7, pos=2, card_id="EDR_453", can_attack=False)
    _minion(gs, 11, 1, 3, 3, pos=3, can_attack=True)
    t = pick_cathedral_buff_target(gs, 1)
    assert t.entity_id == 11
    assert board_location_plays(gs, 1, 10)
    print("OK cathedral skips exhausted minion")


def test_cathedral_buff_increases_face_damage():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=10)
    _location(gs, 47, 1, pos=1, ready=True)
    _minion(gs, 10, 1, 4, 4, pos=2, can_attack=True)
    lc = LethalChecker(gs)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    face_before = fighters_face_damage(fighters, False)
    assert face_before == 4
    plays = board_location_plays(gs, 1, 10)
    assert plays
    loc, defn, cost = plays[0]
    e = _clone_combat_states(lc._build_enemy_minion_states(1))
    fs = _clone_combat_states(fighters)
    apply_spell_sequence_with_meta(
        e, fs, [(defn, cost, loc)], spell_mult=1, enemy_shield=False,
        gs=gs, player_id=1, hero_hp=30, mana_budget=10,
    )
    face_after = fighters_face_damage(fs, False)
    assert face_after == 6, (face_before, face_after)
    print("OK cathedral +2 atk face", face_before, "->", face_after)


def _location_cata(gs, eid, pid, *, pos, dur=3, ready=True, powered_up=False):
    loc = gs.get_entity(eid)
    loc.cardtype = "LOCATION"
    loc.controller = pid
    loc.zone = "PLAY"
    loc.card_id = "CATA_584"
    loc.health = dur
    loc.damage = 0
    loc.tags.update({
        "ZONE": "PLAY",
        "CARDTYPE": "LOCATION",
        "HEALTH": dur,
        "ZONE_POSITION": pos,
    })
    if powered_up:
        loc.tags["POWERED_UP"] = 1
    if not ready:
        loc.tags["EXHAUSTED"] = 1
        loc.tags["LOCATION_ACTION_COOLDOWN"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid


def _hand_spell(gs, eid, pid, card_id, *, cost=2):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.tags.update({
        "ZONE": "HAND",
        "CARDTYPE": "SPELL",
        "COST": cost,
        "SPELL_SCHOOL": 2,
    })


def test_erupting_volcano_damage_tiers():
    assert erupting_volcano_total_damage() == 3
    assert erupting_volcano_total_damage(fire_spell_played_this_turn=True) == 6
    gs = GameState()
    loc = gs.get_entity(47)
    loc.tags["POWERED_UP"] = 1
    assert erupting_volcano_total_damage(card=loc) == 6
    print("OK volcano 3/6 tiers")


def test_erupting_volcano_face_without_fire():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30)
    _location_cata(gs, 47, 1, pos=1, ready=True, powered_up=False)
    from hdt_python.location_board import get_location_def
    defn = get_location_def("CATA_584")
    loc = gs.get_entity(47)
    res, _, _ = apply_spell_sequence_with_meta(
        [], [], [(defn, 0, loc)], gs=gs, player_id=1, enemy_shield=False,
    )
    assert res.direct_face_damage == 3, res.direct_face_damage
    print("OK volcano 3 face without fire", res.direct_face_damage)


def test_erupting_volcano_powered_up_six():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30)
    _location_cata(gs, 47, 1, pos=1, ready=True, powered_up=True)
    from hdt_python.location_board import get_location_def
    defn = get_location_def("CATA_584")
    loc = gs.get_entity(47)
    res, _, _ = apply_spell_sequence_with_meta(
        [], [], [(defn, 0, loc)], gs=gs, player_id=1, enemy_shield=False,
    )
    assert res.direct_face_damage == 6, res.direct_face_damage
    print("OK volcano 6 face powered up", res.direct_face_damage)


def test_erupting_volcano_after_fire_spell_in_sequence():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30)
    _location_cata(gs, 47, 1, pos=1, ready=True, powered_up=False)
    _hand_spell(gs, 20, 1, "CATA_582", cost=2)
    from hdt_python.location_board import get_location_def
    fire_defn = get_board_spell_def("CATA_582")
    vol_defn = get_location_def("CATA_584")
    fire_card = gs.get_entity(20)
    vol = gs.get_entity(47)
    res, _, _ = apply_spell_sequence_with_meta(
        [], [],
        [(fire_defn, 2, fire_card), (vol_defn, 0, vol)],
        gs=gs, player_id=1, enemy_shield=False, mana_budget=10,
    )
    assert res.direct_face_damage >= 6, res.direct_face_damage
    print("OK volcano 6 after fire spell in seq", res.direct_face_damage)


def _hand_location(gs, eid, pid, card_id="REV_290", cost=3):
    loc = gs.get_entity(eid)
    loc.cardtype = "LOCATION"
    loc.controller = pid
    loc.zone = "HAND"
    loc.card_id = card_id
    loc.health = 3
    loc.tags.update({
        "ZONE": "HAND",
        "CARDTYPE": "LOCATION",
        "COST": cost,
        "HEALTH": 3,
        "ZONE_POSITION": 1,
    })
    return loc


def _hand_silence(gs, eid, pid, card_id="JAM_022", cost=1):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.tags.update({
        "ZONE": "HAND",
        "CARDTYPE": "SPELL",
        "COST": cost,
        "ZONE_POSITION": 2,
    })
    return s


def test_hand_cathedral_offered_in_plays():
    from hdt_python.battlecry_board import hand_all_board_plays
    from hdt_python.location_board import hand_location_plays

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5, pos=1, can_attack=True)
    _hand_location(gs, 40, 1)
    plays = hand_location_plays(gs, 1, 10)
    assert len(plays) == 1 and plays[0][0].card_id == "REV_290" and plays[0][2] == 3, plays
    all_plays = hand_all_board_plays(gs, 1, 10)
    assert any(c.card_id == "REV_290" and cost == 3 for c, _d, cost in all_plays), all_plays
    print("OK hand cathedral in plays", plays[0][2])


def test_hand_cathedral_plus_silence_lethal():
    """复盘：邪鬼皇后嘲讽挡脸，场攻 14 vs 15 血；致聋术解嘲 + 手牌赎罪教堂 +2 → 16 斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30)
    opp = gs.get_entity(2)
    opp.damage = 14
    opp.tags["DAMAGE"] = 14  # 16 血：仅沉默场攻 14 不够，需教堂 +2
    # 避免空牌库把疲劳算进斩杀，掩盖地标贡献
    for i, eid in enumerate(range(100, 105), start=1):
        d = gs.get_entity(eid)
        d.controller = 1
        d.zone = "DECK"
        d.tags["ZONE"] = "DECK"
        d.card_id = f"CS2_0{i}"
    for i, eid in enumerate(range(110, 115), start=1):
        d = gs.get_entity(eid)
        d.controller = 2
        d.zone = "DECK"
        d.tags["ZONE"] = "DECK"
        d.card_id = f"CS2_1{i}"
    # 场攻 3+4+2+5=14
    _minion(gs, 10, 1, 3, 3, pos=1, card_id="ETC_543", can_attack=True)
    _minion(gs, 11, 1, 4, 7, pos=2, card_id="ETC_334", can_attack=True)
    _minion(gs, 12, 1, 2, 4, pos=3, card_id="JAIL_303", can_attack=True)
    _minion(gs, 13, 1, 5, 5, pos=4, card_id="TSC_943", can_attack=True)
    # 嘲讽挡脸
    t = gs.get_entity(20)
    t.cardtype = "MINION"
    t.controller = 2
    t.zone = "PLAY"
    t.card_id = "TOY_914"
    t.atk = 4
    t.health = 4
    t.damage = 0
    t.tags.update({
        "ZONE": "PLAY", "ATK": 4, "HEALTH": 4, "TAUNT": 1,
        "ZONE_POSITION": 1, "NUM_TURNS_IN_PLAY": 1,
    })
    gs.board_slots.setdefault(2, {})[1] = 20
    _hand_location(gs, 40, 1)
    _hand_silence(gs, 41, 1)

    checker = LethalChecker(gs)
    total, sources, is_lethal = checker.calculate_lethal_potential()
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note() or ""
    assert is_lethal, (total, sources, note, face)
    assert face >= 16, (total, face, note)
    assert "赎罪" in note or "教堂" in note, note
    print("OK hand cathedral + silence lethal", total, face, note)


if __name__ == "__main__":
    test_location_ready_and_plays()
    test_location_cooldown_not_offered()
    test_cathedral_prefers_windfury_lowest_atk()
    test_cathedral_lowest_atk_without_windfury()
    test_cathedral_skips_non_attackable()
    test_cathedral_buff_increases_face_damage()
    test_erupting_volcano_damage_tiers()
    test_erupting_volcano_face_without_fire()
    test_erupting_volcano_powered_up_six()
    test_erupting_volcano_after_fire_spell_in_sequence()
    test_hand_cathedral_offered_in_plays()
    test_hand_cathedral_plus_silence_lethal()
    print("all passed")
