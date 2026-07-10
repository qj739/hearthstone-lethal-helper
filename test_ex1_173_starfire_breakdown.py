#!/usr/bin/env python3
"""星火术 EX1_173 应计入法术分项，而非随从场攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_spell_board import _hero, _minion, _hand_spell
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def


def test_ex1_173_registered():
    assert get_board_spell_def("EX1_173") is not None
    assert get_board_spell_def("CS2_009") is None


def test_starfire_spell_breakdown_not_minion():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _minion(gs, 11, 1, 2, 2)
    _minion(gs, 12, 1, 2, 2)
    _hand_spell(gs, 30, 1, "EX1_173", 6)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    assert spell >= 5, f"starfire should count as spell, got spell={spell}"
    assert minion == 6, f"board minions only 2+2+2=6, got {minion}"
    assert total == minion + spell + weapon + hp
    assert total == 11, f"expected 6 board + 5 starfire, got {total}"


def test_starfire_stellar_balance_spell_power():
    """星体平衡生成的星火术带 CURRENT_SPELLPOWER_BASE=1 → 6 伤进法术分项。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3)
    _minion(gs, 11, 1, 3, 3)
    s = _hand_spell(gs, 30, 1, "EX1_173", 6)
    s.tags["CURRENT_SPELLPOWER_BASE"] = 1

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    assert spell == 6, f"buffed starfire should be 6 spell face, got {spell}"
    assert minion == 6
    assert total == 12


if __name__ == "__main__":
    test_ex1_173_registered()
    test_starfire_spell_breakdown_not_minion()
    test_starfire_stellar_balance_spell_power()
    print("all passed")
