#!/usr/bin/env python3
"""回归：回合初 EXHAUSTED=0 但 NUM_ATTACKS 仍残留时，场攻应计入全部可攻随从。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.board_damage import build_board_card
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, mana=9, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", exhausted=0, attacks=1):
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
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = attacks
    m.tags["EXHAUSTED"] = exhausted
    m.tags["NUM_TURNS_IN_PLAY"] = 2
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_turn_refresh_stale_num_attacks_counts_all_minions():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=9, used=0)
    _hero(gs, 2, 2)
    # 模拟回合初：EXHAUSTED 已刷新为 0，NUM_ATTACKS 仍为上回合 1
    _minion(gs, 10, 1, 1, 1, card_id="TOY_006", exhausted=0, attacks=1)
    _minion(gs, 11, 1, 6, 8, card_id="TSC_069", exhausted=0, attacks=1)
    _minion(gs, 12, 1, 3, 5, card_id="VAC_432", exhausted=0, attacks=1)
    _minion(gs, 13, 1, 6, 8, card_id="TSC_069", exhausted=0, attacks=1)

    for eid, cid, cost in ((20, "CORE_CS2_062", 3), (21, "GDB_305", 3), (22, "CATA_785", 2)):
        s = gs.get_entity(eid)
        s.cardtype = "SPELL"
        s.controller = 1
        s.zone = "HAND"
        s.card_id = cid
        s.cost = cost
        s.tags["ZONE"] = "HAND"
        s.tags["COST"] = cost

    views = [
        build_board_card(m, True, gs)
        for m in gs.get_board(1)
    ]
    assert all(v.can_attack_hero for v in views), [
        (v.entity.card_id, v.can_attack_hero, v.entity.tags.get("NUM_ATTACKS_THIS_TURN"))
        for v in views
    ]

    board_view = gs.get_player_board(1, active_turn=True)
    assert board_view.face_attack_damage_no_taunt(False) == 16

    lc = LethalChecker(gs)
    gs.get_hero(2).health = 7
    face = lc.overlay_board_face_damage()
    pure, min_bd, _, spell_bd, _ = lc.overlay_board_breakdown()
    assert pure == 16, pure
    assert min_bd >= 16, (min_bd, face, lc.overlay_spell_note())
    assert face >= 23, (face, min_bd, spell_bd, lc.overlay_spell_note())
    assert lc.calculate_lethal_potential()[2] is True


if __name__ == "__main__":
    test_turn_refresh_stale_num_attacks_counts_all_minions()
    print("OK turn refresh stale attacks")
