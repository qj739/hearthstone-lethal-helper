#!/usr/bin/env python3
"""零配置识别：DebugPrintGame / FRIENDLY_PLAYER。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, PowerLogParser


def test_debug_print_game_locks_local_client():
    gs = GameState()
    p = PowerLogParser("dummy", gs)
    lines = [
        "CREATE_GAME",
        "D 00:00:00 GameState.DebugPrintGame() - PlayerID=1, PlayerName=能干的英雄#510408",
        "D 00:00:00 GameState.DebugPrintGame() - PlayerID=2, PlayerName=UNKNOWN HUMAN PLAYER",
        "D 00:00:00 GameState.DebugPrintEntityChoices() - id=2 Player=醉卧沙场君莫笑#53133 TaskList=6 ChoiceType=MULLIGAN CountMin=0 CountMax=3",
    ]
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines:
            p.process_line(line)
    assert gs.local_player_id == 1, (gs.local_player_id, gs.player_names, gs.local_player_identity_source)
    assert "DebugPrintGame" in (gs.local_player_identity_source or "")


def test_opponent_mulligan_does_not_override():
    gs = GameState()
    p = PowerLogParser("dummy", gs)
    with contextlib.redirect_stdout(io.StringIO()):
        p.process_line("CREATE_GAME")
        p.process_line(
            "D 00:00:00 GameState.DebugPrintGame() - PlayerID=1, PlayerName=能干的英雄#510408"
        )
        p.process_line(
            "D 00:00:00 GameState.DebugPrintGame() - PlayerID=2, PlayerName=UNKNOWN HUMAN PLAYER"
        )
        p.process_line(
            "D 00:00:00 GameState.DebugPrintEntityChoices() - id=1 Player=能干的英雄#510408 TaskList=5 ChoiceType=MULLIGAN CountMin=0 CountMax=5"
        )
        p.process_line(
            "TAG_CHANGE Entity=醉卧沙场君莫笑#53133 tag=MULLIGAN_STATE value=INPUT"
        )
        p.process_line(
            "D 00:00:00 GameState.DebugPrintEntityChoices() - id=2 Player=醉卧沙场君莫笑#53133 TaskList=6 ChoiceType=MULLIGAN CountMin=0 CountMax=3"
        )
    assert gs.local_player_id == 1


if __name__ == "__main__":
    test_debug_print_game_locks_local_client()
    test_opponent_mulligan_does_not_override()
    print("OK zero-config identity")
