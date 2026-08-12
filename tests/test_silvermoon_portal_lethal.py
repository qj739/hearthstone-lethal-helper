#!/usr/bin/env python3
"""银月城传送门 KAR_077：友方 +2/+2，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells
from hdt_python.spell_p0_buff import _apply_silvermoon_portal


def _hero(gs, eid, pid, *, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
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


def test_registered():
    for cid in ("KAR_077", "CORE_KAR_077", "WON_309"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name == "银月城传送门"
        assert defn.base_cost == 3


def test_buffs_friendly_plus_2_2():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=20)
    _minion(gs, 30, 1, 8, 8, card_id="CS2_088")
    _hand_spell(gs, 40, 1, "CORE_KAR_077", 3)

    lc = LethalChecker(gs)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    _apply_silvermoon_portal([], fighters, mult=1, enemy_shield=False, gs=gs, player_id=1)
    assert fighters[0]["atk"] == 10
    assert fighters[0]["health"] == 10
    assert any(s.card_id == "CORE_KAR_077" for s, _, _ in hand_board_spells(gs, 1, 10))


def test_enables_lethal():
    """8 攻场面 + 银月城传送门 +2 = 10，对手 10 血可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 10, 1)
    hero.tags["RESOURCES"] = 10
    hero.tags["RESOURCES_USED"] = 0
    _hero(gs, 20, 2, dmg=20)  # 10 血
    _minion(gs, 30, 1, 8, 8, card_id="CS2_088")
    _hand_spell(gs, 40, 1, "KAR_077", 3)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _src, lethal = lc.calculate_lethal_potential()
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert face >= 10, f"face={face} note={note}"
    assert lethal, f"total={total} face={face} note={note}"
    assert "银月城传送门" in note, note


if __name__ == "__main__":
    test_registered()
    test_buffs_friendly_plus_2_2()
    test_enables_lethal()
    print("ok")
