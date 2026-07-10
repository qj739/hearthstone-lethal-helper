#!/usr/bin/env python3
"""十字军光环：随从攻击时 +2 攻，应计入斩杀/场攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", can_attack=True):
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
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if not can_attack:
        m.tags["EXHAUSTED"] = 1
    return m


def _secret_aura(gs, eid, pid):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "SECRET"
    s.card_id = "LEG_TTN_908"
    s.health = 1
    s.tags["ZONE"] = "SECRET"
    return s


def test_crusader_aura_3_atk_lethal_4_hp():
    """3 攻随从 + 十字军光环 → 攻击时 5 伤，对手 4 血应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 26
    opp.damage = 26
    _minion(gs, 30, 1, 3, 3, card_id="VAC_509t")
    _secret_aura(gs, 40, 1)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 4, f"expected face>=4 got {face}"
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"should detect lethal total={total} face={face}"


if __name__ == "__main__":
    test_crusader_aura_3_atk_lethal_4_hp()
    print("ok")
