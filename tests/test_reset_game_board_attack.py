#!/usr/bin/env python3
"""时光回溯后不应把坟场复生尸与幽灵随从算进场攻。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import _std_attack

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_22_12_18_28\Power.log"
)
START = 223093
# 回溯后、对手回合预览：应为 10（3+1+4+2），不是 14（多算坟场 178 + 复生 182）
TARGET = 250001


def test_rewind_board_attack_not_inflated():
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(START, TARGET):
            if lines[i].strip():
                p.process_line(lines[i].rstrip())

    assert gs.in_game
    board_ids = [m.entity_id for m in gs.get_board(gs.local_player_id)]
    assert 178 not in board_ids, f"graveyard zombie 178 still on board: {board_ids}"
    assert 182 not in board_ids, f"pre-rewind reborn 182 still on board: {board_ids}"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, mn, wp, _, _ = lc.overlay_board_breakdown()
    detail = [
        f"{m.card_id}:{_std_attack(m, gs)}"
        for m in gs.get_board(gs.local_player_id)
    ]
    # 回溯后场面：黏土巢母3 + 吵吵歌迷1 + 雏龙4 + 僵尸2 = 10
    # 旧逻辑会把坟场 178 与回溯前复生的 182 一并算上 → 14
    assert mn == 10, f"expected mn=10 got {mn} face={face} board={detail}"
    assert face == 10, f"expected face=10 got {face} board={detail}"
    print("OK rewind board attack", face, mn, detail)


if __name__ == "__main__":
    test_rewind_board_attack_not_inflated()
