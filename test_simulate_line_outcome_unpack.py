#!/usr/bin/env python3
"""回归：_simulate_line_outcome 返回 9 元组时 _simulate_line_face_total 不崩溃。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker

LOG_MOONWELL = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_24_12_01_30\Power.log"
)
LOG_MALT = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_24_18_18_38\Power.log"
)


def _replay_to_line(log: Path, line_no: int) -> GameState:
    if not log.is_file():
        return None
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[: line_no + 1]:
            if line.strip():
                parser.process_line(line.rstrip())
    return gs


def _replay_to_line_legacy(line_no: int) -> GameState:
    return _replay_to_line(LOG_MOONWELL, line_no)


def test_overlay_face_no_unpack_error_on_moonwell_board():
    """Power.log 15:18:55：月亮井+龙息+沉默问题学生；不应误报斩杀。"""
    gs = _replay_to_line_legacy(409430)
    if gs is None:
        print("SKIP moonwell unpack log replay (log missing)")
        return

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face == 18, (face, lc.overlay_board_breakdown(), lc.overlay_battlecry_face())
    assert not has, (face, has)
    assert lc.overlay_battlecry_face() == 0
    best = getattr(lc, "_overlay_best_seq", []) or []
    card_ids = [getattr(step[2], "card_id", "") or "" for step in best]
    assert "RLK_915" not in card_ids, card_ids
    assert sum(step[1] for step in best) <= 10, best
    print("OK overlay unpack regression", face, has)


def test_monte_carlo_line_stats_no_unpack_on_malt_board():
    """麦芽岩浆+随机回合结束场面：_monte_carlo_line_stats 不崩溃。"""
    gs = _replay_to_line(LOG_MALT, 71740)
    if gs is None:
        print("SKIP malt MC unpack log replay (log missing)")
        return

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face >= 0, face
    assert isinstance(has, bool)
    print("OK malt MC unpack regression", face, has)


if __name__ == "__main__":
    test_overlay_face_no_unpack_error_on_moonwell_board()
    test_monte_carlo_line_stats_no_unpack_on_malt_board()
