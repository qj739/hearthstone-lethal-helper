#!/usr/bin/env python3
"""休眠玛瑟里顿：场攻展示不含 +3 回合结束，斩杀仍计入。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_spell_board import _hero, _minion
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def test_dormant_magtheridon_overlay_display():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2  # 对方回合 → 下回合场攻视角
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    _minion(gs, 10, 1, 1, 2, card_id="WW_816t")
    _minion(gs, 11, 1, 3, 4, card_id="CATA_304")
    mag = _minion(gs, 12, 1, 12, 12, card_id="TOY_647")
    mag.tags["DORMANT"] = 1
    _minion(gs, 13, 1, 1, 2, card_id="WW_816t")

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()

    assert minion == 5, f"minion breakdown should be 5, got {minion}"
    assert display == 5, f"display face should exclude dormant ET, got {display}"
    assert lethal == 8, f"lethal total should include dormant ET +3, got {lethal}"
    assert pure == 5, f"pure immediate should be 5, got {pure}"
    print("OK dormant magtheridon overlay", display, lethal)


if __name__ == "__main__":
    test_dormant_magtheridon_overlay_display()
    print("all passed")
