#!/usr/bin/env python3
"""抹除存在被回溯撤销后，赛拉辛等应回场，场攻含其攻击力。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import entity_zone

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_09_19_10_54_15\Power.log"
)
# 对局：CREATE_GAME → 投降前下一局 CREATE_GAME
START = 658665
END = 731717


def test_cease_exist_rewind_restores_serathsin_face_13():
    if not LOG.is_file():
        print("SKIP missing log", LOG)
        return
    lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    p._live_mode = False
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(START, END):
            if lines[i].strip():
                p.process_line(lines[i].rstrip())

    e418 = gs.entities.get(418)
    assert e418 is not None, "missing entity 418"
    assert entity_zone(e418) == "PLAY", f"418 zone={entity_zone(e418)}"
    assert e418.card_id == "AV_403"

    board = gs.get_board(gs.local_player_id)
    ids = {m.entity_id for m in board}
    assert 418 in ids, f"Serathsin not on board: {[(m.entity_id, m.card_id, m.atk) for m in board]}"
    assert 364 in ids and 366 in ids

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, mn, _, _, _ = lc.overlay_board_breakdown()
    detail = [(m.entity_id, m.card_id, m.atk) for m in board]
    # TLC_401(6) + AV_403(5) + TLC_102(2) = 13；旧逻辑漏赛拉辛显示 9
    assert mn == 13, f"expected mn=13 got {mn} face={face} board={detail}"
    assert face == 13, f"expected face=13 got {face} board={detail}"
    print("OK cease-exist rewind face", face, detail)


def test_full_entity_gamestate_play_beats_graveyard_bracket():
    """GameState FULL_ENTITY：括号 GRAVEYARD + 行内 ZONE=PLAY 应回场。"""
    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    p._live_mode = False
    lines = [
        "D 00:00:00.0 GameState.DebugPrintPower() - FULL_ENTITY - Updating "
        "[entityName=X id=418 zone=GRAVEYARD zonePos=0 cardId=AV_403 player=2] CardID=AV_403",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=CARDTYPE value=MINION",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ATK value=5",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=HEALTH value=5",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ZONE value=PLAY",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=CONTROLLER value=2",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ZONE_POSITION value=1",
        "D 00:00:00.0 GameState.DebugPrintPower() - BLOCK_END",
    ]
    # 预置本地玩家与 controller 映射
    gs.local_player_id = 2
    gs.player_ids[2] = 2
    with contextlib.redirect_stdout(io.StringIO()):
        for ln in lines:
            p.process_line(ln)
    e = gs.entities[418]
    assert entity_zone(e) == "PLAY", entity_zone(e)
    assert e.tags.get("ZONE_POSITION") == 1


def test_powertasklist_reset_game_does_not_clear_board():
    """PowerTaskList 滞后 RESET_GAME 不得清掉 GameState 已恢复的场面。"""
    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    p._live_mode = False
    gs.local_player_id = 2
    gs.player_ids[2] = 2
    setup = [
        "D 00:00:00.0 GameState.DebugPrintPower() - FULL_ENTITY - Updating "
        "[entityName=X id=418 zone=GRAVEYARD zonePos=0 cardId=AV_403 player=2] CardID=AV_403",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=CARDTYPE value=MINION",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ATK value=5",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=HEALTH value=5",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ZONE value=PLAY",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=CONTROLLER value=2",
        "D 00:00:00.0 GameState.DebugPrintPower() -         tag=ZONE_POSITION value=1",
        "D 00:00:00.0 GameState.DebugPrintPower() - BLOCK_END",
        "D 00:00:00.0 PowerTaskList.DebugPrintPower() -     RESET_GAME",
    ]
    with contextlib.redirect_stdout(io.StringIO()):
        for ln in setup:
            p.process_line(ln)
    assert entity_zone(gs.entities[418]) == "PLAY"
    print("OK PTL RESET_GAME skipped")


if __name__ == "__main__":
    test_full_entity_gamestate_play_beats_graveyard_bracket()
    test_powertasklist_reset_game_does_not_clear_board()
    test_cease_exist_rewind_restores_serathsin_face_13()
