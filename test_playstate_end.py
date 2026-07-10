#!/usr/bin/env python3
"""PLAYSTATE 终局判定：LOSING 不应结束对局。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState


def test_playstate_losing_not_game_over():
    assert not PowerLogParser._is_game_over_playstate("LOSING")
    assert not PowerLogParser._is_game_over_playstate(3)
    assert not PowerLogParser._is_game_over_playstate("PLAYING")
    assert not PowerLogParser._is_game_over_playstate(1)
    assert PowerLogParser._is_game_over_playstate("WON")
    assert PowerLogParser._is_game_over_playstate(4)
    assert PowerLogParser._is_game_over_playstate("LOST")
    assert PowerLogParser._is_game_over_playstate(5)
    assert PowerLogParser._is_game_over_playstate("CONCEDED")
    assert PowerLogParser._is_game_over_playstate(8)


def test_losing_playstate_does_not_end_live_game():
    gs = GameState()
    p = PowerLogParser("dummy", gs)
    p._live_mode = True
    gs.begin_new_game()
    gs.game_entity_id = 1
    gs.player_ids[10] = 1
    gs.entities[10] = type("E", (), {"tags": {}, "is_hero": False, "cardtype": "PLAYER"})()
    p._apply_tag(10, "PLAYSTATE", "LOSING")
    assert gs.in_game


if __name__ == "__main__":
    test_playstate_losing_not_game_over()
    test_losing_playstate_does_not_end_live_game()
    print("test_playstate_end: OK")
