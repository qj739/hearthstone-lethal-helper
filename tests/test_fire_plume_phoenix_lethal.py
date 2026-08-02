#!/usr/bin/env python3
"""火羽凤凰 CORE_UNG_084：战吼 3 伤应参与斩杀枚举。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def, hand_battlecry_minions
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_minion(gs, eid, pid, card_id, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({"ZONE": "HAND", "ATK": atk, "HEALTH": hp, "COST": cost})
    return m


def test_fire_plume_phoenix_registered():
    assert get_battlecry_def("CORE_UNG_084") is not None
    assert get_battlecry_def("UNG_084") is not None


def test_fire_plume_phoenix_in_hand_plays():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, mana=4, used=0)
    _hand_minion(gs, 11, 1, "CORE_UNG_084", 4, 3, 4)
    plays = hand_battlecry_minions(gs, 1, 4)
    assert any(c.card_id == "CORE_UNG_084" for c, _, _ in plays)


def test_fire_plume_phoenix_battlecry_lethal():
    """对手 2 血：战吼 3 点打脸应斩（对齐 2026-07-30 对局）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=4, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.damage = 28  # 2 血
    _hand_minion(gs, 11, 1, "CORE_UNG_084", 4, 3, 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note() or ""
    assert face >= 2, (face, note, lc.overlay_board_breakdown())
    assert has, (face, has, note)
    assert "火羽凤凰" in note, note


if __name__ == "__main__":
    test_fire_plume_phoenix_registered()
    test_fire_plume_phoenix_in_hand_plays()
    test_fire_plume_phoenix_battlecry_lethal()
    print("OK fire plume phoenix lethal")
