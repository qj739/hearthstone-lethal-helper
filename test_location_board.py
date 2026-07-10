#!/usr/bin/env python3
"""地标：赎罪教堂 +2/+1 目标选择与可用性。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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
    print("all passed")
