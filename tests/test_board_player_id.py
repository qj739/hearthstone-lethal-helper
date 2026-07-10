#!/usr/bin/env python3
"""玩家 ID 识别：避免把对手场面当成我方（YOG_519 7攻 vs TTN+TOY）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_10_22_53_33\Power.log"
)


def _terminal_snapshot(gs):
    h1 = gs.get_hero(1)
    h2 = gs.get_hero(2)
    if not h1 or not h2:
        return None
    mana2 = h2.tags.get("RESOURCES", 0) - h2.tags.get("RESOURCES_USED", 0)
    if h2.current_health == 19 and h1.current_health == 17 and mana2 == 1:
        return gs
    return None


def test_full_replay_local_is_player1_with_yog():
    if not LOG.is_file():
        return
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    create = next(
        i
        for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "DebugPrintPower" in l
    )
    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    snap = None
    for raw in lines[create:37586]:
        if raw.strip():
            p.process_line(raw.rstrip("\n\r"))
        if _terminal_snapshot(gs):
            snap = gs
            break
    assert snap is not None, "未在日志中找到终端对应时刻"
    assert snap.local_player_id == 1, f"expected local=1, got {snap.local_player_id}"
    assert snap.local_player_id_locked

    my_board = snap.get_board(snap.local_player_id)
    assert len(my_board) == 1, f"我方应只有 1 个随从，实际 {[(m.card_id, m.atk) for m in my_board]}"
    assert my_board[0].card_id == "YOG_519"
    assert my_board[0].atk == 7


def test_mid_game_tail_does_not_flip_to_player2():
    """对手打出 TTN/TOY 时，不应把 local 识别成 2"""
    if not LOG.is_file():
        return
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    create = next(
        i
        for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "DebugPrintPower" in l
    )
    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    p._live_mode = True
    for raw in lines[create:25700]:
        if raw.strip():
            p.process_line(raw.rstrip("\n\r"))
    assert gs.local_player_id == 1, f"pre-tail should be local=1, got {gs.local_player_id}"
    for raw in lines[25700:27000]:
        if raw.strip():
            p.process_line(raw.rstrip("\n\r"))
    assert gs.local_player_id == 1, f"mid-game tail should stay local=1, got {gs.local_player_id}"


def test_get_board_removes_invalid_slots_without_keyerror():
    """无效槽位（实体缺失/已离场）清理时不应抛 KeyError。"""
    gs = GameState()
    gs.board_slots[1] = {6: 999}
    board = gs.get_board(1)
    assert board == []
    assert 6 not in gs.board_slots.get(1, {})
    print("OK get_board invalid slot cleanup")


if __name__ == "__main__":
    test_get_board_removes_invalid_slots_without_keyerror()
    test_full_replay_local_is_player1_with_yog()
    test_mid_game_tail_does_not_flip_to_player2()
    print("ok")
