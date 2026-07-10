#!/usr/bin/env python3
"""卡德加魔法智慧之球（TOY_373t）0 攻武器不应计入武伤分项。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_weapon_board import _hero, _weapon
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import _weapon_std_attack, _std_attack


def test_wisdomball_zero_weapon_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    gs.player_ids[1] = 1
    _hero(gs, 1, 1, atk479=3)
    w = _weapon(gs, 40, 1, "TOY_373t", atk=0, dur=3)
    w.tags.pop("ATK", None)
    w.tags.pop("479", None)
    w.tags["479"] = 3  # 模拟日志误把耐久写入 479

    assert _weapon_std_attack(w) == 0
    assert _std_attack(w) == 0

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    _, _, weapon_board, _, _ = lc.overlay_board_breakdown()
    assert weapon_board == 0, f"expected 武0, got weapon_board={weapon_board}"


if __name__ == "__main__":
    test_wisdomball_zero_weapon_face()
    print("all passed")
