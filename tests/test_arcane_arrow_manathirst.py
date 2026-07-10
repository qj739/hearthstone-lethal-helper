#!/usr/bin/env python3
"""奥术箭 RLK_843：法力渴求(8 水晶) 2→3 伤。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_spell_board import _hand_spell, _hero
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import (
    get_board_spell_def,
    manathirst_spell_face_damage,
    max_mana_crystals_for_spells,
    spell_script_damage,
)


def _setup(max_mana: int, *, opp_turn: bool = False):
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2 if opp_turn else 1
    _hero(gs, 1, 1, mana=max_mana, used=0)
    hero = gs.get_hero(1)
    hero.tags["MAXRESOURCES"] = max_mana
    hero.tags["RESOURCES"] = max_mana
    return gs


def test_arcane_arrow_manathirst_threshold():
    gs = _setup(7)
    card = _hand_spell(gs, 30, 1, "RLK_843", 1)
    assert manathirst_spell_face_damage("RLK_843", gs, 1, card=card) == 2
    assert spell_script_damage(card, gs=gs, player_id=1) == 2

    gs = _setup(8)
    card = _hand_spell(gs, 30, 1, "RLK_843", 1)
    assert manathirst_spell_face_damage("RLK_843", gs, 1, card=card) == 3
    assert spell_script_damage(card, gs=gs, player_id=1) == 3
    print("OK manathirst threshold 7/8", max_mana_crystals_for_spells(gs, 1))


def test_arcane_arrow_opp_turn_next_crystal():
    """对方回合 7 水晶：下回合 8，奥术箭应按 3 伤。"""
    gs = _setup(7, opp_turn=True)
    card = _hand_spell(gs, 30, 1, "RLK_843", 1)
    assert max_mana_crystals_for_spells(gs, 1) == 8
    assert manathirst_spell_face_damage("RLK_843", gs, 1, card=card) == 3
    print("OK opp turn 7 crystals -> next 8", spell_script_damage(card, gs=gs, player_id=1))


def test_arcane_arrow_overlay_face():
    gs = _setup(10)
    _hand_spell(gs, 30, 1, "RLK_843", 1)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 3, face
    defn = get_board_spell_def("RLK_843")
    assert defn is not None
    print("OK overlay includes arcane arrow", face, lc.overlay_spell_note())


if __name__ == "__main__":
    test_arcane_arrow_manathirst_threshold()
    test_arcane_arrow_opp_turn_next_crystal()
    test_arcane_arrow_overlay_face()
    print("all passed")
