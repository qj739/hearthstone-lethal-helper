#!/usr/bin/env python3
"""邪能弹幕：先英雄打脸压低血线，再两发打脸斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id=""):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
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


def test_fel_barrage_lethal_after_hero_face():
    """对手 9 血 + 6 血随从；5 攻英雄 + 邪能弹幕 4 直伤可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True

    hero = _hero(gs, 64, 1, mana=10, used=0)
    hero.atk = 5
    hero.tags["ATK"] = 5
    hero.tags["NUM_ATTACKS_THIS_TURN"] = 0
    hero.tags["EXHAUSTED"] = 0

    opp = _hero(gs, 66, 2)
    opp.tags["DAMAGE"] = 21
    opp.damage = 21

    _minion(gs, 48, 2, 4, 6, card_id="TIME_004")
    _hand_spell(gs, 168, 1, "SW_040", 4)

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert face >= 9, f"expected lethal face >=9, got {face} spell={spell}"
    assert spell == 4, f"fel barrage should hit face twice, spell={spell}"

    total, _, has_lethal = checker.calculate_lethal_potential()
    assert has_lethal, f"should detect lethal, total={total} face={face}"
    print("OK fel barrage hero-first lethal", face, spell)


if __name__ == "__main__":
    test_fel_barrage_lethal_after_hero_face()
