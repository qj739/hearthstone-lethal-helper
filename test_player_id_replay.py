#!/usr/bin/env python3
"""回归：新局不沿用上一局 PlayerID 映射；回放含 CREATE_GAME 前 DebugPrintGame 前缀。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, find_last_game_replay_start, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_22_15_41_10\Power.log"
)
LETHAL_LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_29_13_25_16\Power.log"
)
FALSE_LETHAL_LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_29_17_41_41\Power.log"
)


def test_begin_new_game_clears_stale_player_names():
    gs = GameState()
    gs.player_names = {2: "鸡哥在线#5240"}
    gs.local_player_id = 2
    gs.begin_new_game()
    assert gs.player_names == {}
    assert gs.local_player_id is None


def test_replay_preamble_includes_debug_print_game():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = find_last_game_replay_start(lines)
    assert start >= 0
    preamble = "\n".join(lines[start : start + 80])
    assert "DebugPrintGame() - PlayerID=" in preamble
    create_idx = next(
        i for i in range(start, min(start + 120, len(lines))) if "CREATE_GAME" in lines[i]
    )
    game_block = "\n".join(lines[start : create_idx + 1])
    assert "CREATE_GAME" in game_block
    assert "鸡哥在线#5240" in game_block


def test_stale_names_not_used_after_new_game():
    import os

    os.environ["HS_PLAYER_NAME"] = "鸡哥在线#5240"
    gs = GameState()
    gs.player_names = {2: "鸡哥在线#5240"}
    gs.begin_new_game()
    p = PowerLogParser("dummy", gs)
    p.reconcile_local_player()
    assert gs.local_player_id is None
    assert gs.player_names == {}


def test_replay_with_preamble_locks_correct_player():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    import os

    os.environ["HS_PLAYER_NAME"] = "鸡哥在线#5240"
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = find_last_game_replay_start(lines)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for raw in lines[start : start + 250]:
            p.process_line(raw)
    # 最新一局日志里鸡哥为 Player 1
    assert gs.local_player_id == 1, (gs.local_player_id, gs.player_names)
    print("OK player replay", gs.local_player_id, gs.player_names)


def test_lethal_game_player2_and_lethal_mid_turn():
    """6/29 对局：鸡哥为 Player 2；回合中段应算出斩杀。"""
    if not LETHAL_LOG.is_file():
        print("SKIP lethal log (missing)")
        return
    import os

    from hdt_python.lethal_checker import LethalChecker

    os.environ["HS_PLAYER_NAME"] = "鸡哥在线#5240"
    lines = LETHAL_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    # 仅第一局（第二局 CREATE_GAME 前）
    g1_end = next(i for i, ln in enumerate(lines) if i > 20000 and "CREATE_GAME" in ln)
    g1_lines = lines[:g1_end]
    start = find_last_game_replay_start(g1_lines)
    assert start >= 0

    gs = GameState()
    p = PowerLogParser(str(LETHAL_LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for raw in g1_lines[start:19710]:
            p.process_line(raw)
    assert gs.local_player_id == 2, (gs.local_player_id, gs.player_names)
    lc = LethalChecker(gs)
    _, _, lethal_turn_start = lc.calculate_lethal_potential()
    assert lethal_turn_start is False

    gs2 = GameState()
    p2 = PowerLogParser(str(LETHAL_LOG), gs2)
    with contextlib.redirect_stdout(io.StringIO()):
        for raw in g1_lines[start:21800]:
            p2.process_line(raw)
    assert gs2.local_player_id == 2
    assert len(gs2.get_hand(2)) >= 5
    lc2 = LethalChecker(gs2)
    _, _, lethal_mid = lc2.calculate_lethal_potential()
    assert lethal_mid is True, "mid-turn lethal should be detected"
    print("OK lethal game pid=2 lethal_mid", lethal_mid)


def test_penultimate_turn_cataclysm_lethal_line():
    """6/29 雄鹿对局：火球后/喷吐后均可走大灾变清场斩杀线。"""
    if not FALSE_LETHAL_LOG.is_file():
        print("SKIP cataclysm lethal log (missing)")
        return
    import os

    from hdt_python.lethal_checker import LethalChecker

    os.environ["HS_PLAYER_NAME"] = "繁忙的雄鹿#59725"
    lines = FALSE_LETHAL_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line_no in (19382, 19520):
        gs = GameState()
        p = PowerLogParser(str(FALSE_LETHAL_LOG), gs)
        with contextlib.redirect_stdout(io.StringIO()):
            for raw in lines[:line_no]:
                p.process_line(raw)
        lc = LethalChecker(gs)
        lc.overlay_board_face_damage()
        face = lc.cached_overlay_face()
        _, _, lethal = lc.calculate_lethal_potential()
        seq_names = [d.name for d, _, _ in lc._overlay_best_seq]
        assert lethal and face >= 10, (line_no, face, lethal, seq_names)
        assert "大灾变" in seq_names, seq_names
    print("OK cataclysm lethal lines 19382/19520")


def test_cataclysm_lethal_after_flame_breath():
    """喷吐火焰后：大灾变清场 + 法术 + 冲锋龙可斩杀 10 血。"""
    if not FALSE_LETHAL_LOG.is_file():
        print("SKIP cataclysm lethal log (missing)")
        return
    import os

    from hdt_python.lethal_checker import LethalChecker

    os.environ["HS_PLAYER_NAME"] = "繁忙的雄鹿#59725"
    lines = FALSE_LETHAL_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    p = PowerLogParser(str(FALSE_LETHAL_LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for raw in lines[:19520]:
            p.process_line(raw)
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    face = lc.cached_overlay_face()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 10, f"cataclysm line should reach 10 face, got {face}"
    assert lethal is True
    seq_names = [d.name for d, _, _ in lc._overlay_best_seq]
    assert "大灾变" in seq_names, seq_names
    print("OK cataclysm lethal", face, seq_names)


if __name__ == "__main__":
    test_begin_new_game_clears_stale_player_names()
    test_replay_preamble_includes_debug_print_game()
    test_stale_names_not_used_after_new_game()
    test_replay_with_preamble_locks_correct_player()
    test_lethal_game_player2_and_lethal_mid_turn()
    test_penultimate_turn_cataclysm_lethal_line()
    test_cataclysm_lethal_after_flame_breath()
