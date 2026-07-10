#!/usr/bin/env python3
"""月亮井打出动画期间应保持红色斩杀 Overlay，不应因场攻暂为 0 变黑。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_29_17_41_41\Power.log"
)
TARGET_BEFORE_PLAY = 204349


def _replay(target: int) -> GameState:
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i
        for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    start = max((s for s in starts if s < target), default=starts[0])
    gs = GameState()
    gs.player_names[2] = "繁忙的雄鹿#59725"
    gs.local_player_id = 2
    parser = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[start:target]:
            if line.strip():
                parser.process_line(line.rstrip())
    gs.in_game = True
    gs.active_player_id = 2
    return gs


def test_moonwell_play_animation_keeps_lethal_overlay():
    """第 20 回合：先算出斩杀，再模拟月亮井进入 PLAY 结算，Overlay 仍应提示斩杀。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return

    gs = _replay(TARGET_BEFORE_PLAY)
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face_before = lc.overlay_board_face_damage()
        _, _, lethal_before = lc.calculate_lethal_potential()

    assert lethal_before is True, (face_before, lc.get_opponent_effective_hp())
    assert lc.overlay_lethal_prompt_ok(lethal_before)
    assert face_before >= lc.get_opponent_effective_hp()

    moonwell = next(
        e for e in gs.get_hand(2) if e.card_id in ("EDR_476", "CORE_EDR_476")
    )
    moonwell.zone = "PLAY"

    with contextlib.redirect_stdout(io.StringIO()):
        face_mid = lc.overlay_board_face_damage()
        _, _, lethal_mid = lc.calculate_lethal_potential()

    assert lc.overlay_spell_resolving(), "test setup: moonwell should be resolving"
    assert face_mid >= lc.get_opponent_effective_hp(), (
        face_mid,
        lc.get_opponent_effective_hp(),
        lc.overlay_combo_display_lines(),
    )
    assert lethal_mid is True, (face_mid, lc.overlay_combo_display_lines())
    assert lc.overlay_lethal_prompt_ok(lethal_mid)
    print("OK moonwell resolving keeps lethal overlay", face_before, "->", face_mid)


def test_moonwell_log_play_frame_no_false_zero_without_prior_lethal():
    """无斩杀时月亮井结算帧场攻为 0 属正常，且不应误恢复斩杀。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return

    gs = _replay(198303)
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _, _, lethal = lc.calculate_lethal_potential()
    assert lethal is False
    assert face == 0 or not lc.overlay_spell_resolving()
    print("OK moonwell mid-play no prior lethal", face)


if __name__ == "__main__":
    test_moonwell_play_animation_keeps_lethal_overlay()
    test_moonwell_log_play_frame_no_false_zero_without_prior_lethal()
