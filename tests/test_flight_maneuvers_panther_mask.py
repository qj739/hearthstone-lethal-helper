#!/usr/bin/env python3
"""飞龙机动裂变半张 / 奔行豹面具：场攻增益回归。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hdt_python.spell_p0_remove  # noqa: F401
import hdt_python.spell_p0_buff  # noqa: F401
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    spell_sim_tier_for_card,
    SpellSimTier,
)


def _fighter(atk: int, *, eid: int = 1, health: int = 3, attacks_left: int = 1) -> dict:
    return {
        "kind": "minion",
        "entity_id": eid,
        "card_id": "CS2_121",
        "atk": atk,
        "health": health,
        "attacks_left": attacks_left,
        "can_face": True,
    }


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


def _minion(gs, eid, pid, atk, hp, card_id="m", *, exhausted=0, ntp=2):
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
    m.tags["NUM_ATTACKS_THIS_TURN"] = 1 if exhausted else 0
    m.tags["EXHAUSTED"] = exhausted
    m.tags["NUM_TURNS_IN_PLAY"] = ntp
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost, *, shattered=False):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    if shattered:
        s.tags["SHATTERED"] = 1
    return s


def test_flight_maneuvers_halves_registered():
    full = get_board_spell_def("CATA_479")
    summon = get_board_spell_def("CATA_479t")
    buff = get_board_spell_def("CATA_479t2")
    assert full and summon and buff
    spell_sim_tier_for_card.cache_clear()
    assert spell_sim_tier_for_card("CATA_479t2") == SpellSimTier.UTILITY

    board = [_fighter(3)]
    buff.apply([], board, mult=1, enemy_shield=False)
    assert board[0]["atk"] == 4
    assert board[0].get("shield") is True

    empty: list = []
    summon.apply([], empty, mult=1, enemy_shield=False)
    assert len([f for f in empty if f.get("kind") == "minion"]) == 2
    assert all(f.get("atk") == 4 and f.get("health") == 2 for f in empty)
    assert all(int(f.get("attacks_left", 0) or 0) == 0 for f in empty)


def test_flight_maneuvers_buff_half_needs_shattered_tag():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=4)
    _hero(gs, 20, 2, dmg=10)
    _minion(gs, 30, 1, 3, 3, "CS2_121")
    plain = _hand_spell(gs, 40, 1, "CATA_479t2", 4, shattered=False)
    assert hand_board_spells(gs, 1, 4) == []
    plain.tags["SHATTERED"] = 1
    plays = hand_board_spells(gs, 1, 4)
    assert any(c.card_id == "CATA_479t2" for c, _, _ in plays)


def test_flight_maneuvers_buff_half_raises_overlay_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=4)
    _hero(gs, 20, 2, dmg=20)  # 10 血
    _minion(gs, 30, 1, 3, 3, "CS2_121")
    _minion(gs, 31, 1, 2, 2, "CS2_120")
    _hand_spell(gs, 40, 1, "CATA_479t2", 4, shattered=True)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    assert face >= 7, (face, note)  # (3+1)+(2+1)
    assert "飞龙机动" in note


def test_panther_mask_sets_ready_minion_to_5():
    defn = get_board_spell_def("DINO_432")
    assert defn is not None
    fighters = [_fighter(1, eid=1), _fighter(4, eid=2, attacks_left=0)]
    defn.apply([], fighters, mult=1, enemy_shield=False)
    ready = next(f for f in fighters if f.get("entity_id") == 1)
    assert ready["atk"] == 5 and ready["health"] == 4
    rested = next(f for f in fighters if f.get("entity_id") == 2)
    assert rested["atk"] == 4  # 未出手者不优先


def test_panther_mask_enables_lethal():
    """对手 5 血；1 攻可出手随从 + 奔行豹面具 → 5 打脸斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=4)
    _hero(gs, 20, 2, dmg=25)  # 5 血
    _minion(gs, 30, 1, 1, 2, "GIL_816")
    _hand_spell(gs, 40, 1, "DINO_432", 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, lethal = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note()
    assert face >= 5, (face, note)
    assert lethal, (face, note)
    assert "奔行豹面具" in note


if __name__ == "__main__":
    test_flight_maneuvers_halves_registered()
    test_flight_maneuvers_buff_half_needs_shattered_tag()
    test_flight_maneuvers_buff_half_raises_overlay_face()
    test_panther_mask_sets_ready_minion_to_5()
    test_panther_mask_enables_lethal()
    print("ok")
