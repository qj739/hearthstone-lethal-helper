#!/usr/bin/env python3
"""回归：敌方场攻足以斩杀时应识别威胁，而非误报「我能斩」。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_22_15_41_10\Power.log"
)
TARGET = 230800


def _replay(target: int) -> GameState:
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[0])
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    return gs


def test_opponent_imps_threat_when_player_id_swapped():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(TARGET)
    assert gs.local_player_id == 1
    # 模拟 ID 错位：敌方 3 小鬼被当成己方场面
    gs.local_player_id, gs.opponent_player_id = 2, 1
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        my_face = lc.overlay_board_face_damage()
        _, _, my_lethal = lc.calculate_lethal_potential()
        opp_threat = lc.opponent_overlay_face_damage()
    # 错位后：己方显示 30 血，敌方显示 15 血，场攻 9 来自敌方小鬼
    wrong_my_hp = gs.get_hero(2).health - gs.get_hero(2).damage
    wrong_opp_hp = gs.get_hero(1).health - gs.get_hero(1).damage
    assert my_face == 9, my_face
    assert opp_threat == 3, opp_threat
    assert wrong_my_hp == 30 and wrong_opp_hp == 15
    # 若我方真实只剩 9 血（Player1），错位后会显示敌 9 血且场攻 9 → 误报斩杀
    false_lethal_at_9 = my_face >= 9
    assert false_lethal_at_9
    print("OK swapped id", my_face, "wrong display", wrong_my_hp, wrong_opp_hp)


def test_opponent_threat_on_correct_perspective():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(TARGET)
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        opp_threat = lc.opponent_overlay_face_damage()
        my_face = lc.overlay_board_face_damage()
    assert opp_threat == 9, opp_threat
    assert my_face == 3, my_face
    print("OK correct perspective", my_face, opp_threat)


if __name__ == "__main__":
    test_opponent_threat_on_correct_perspective()
    test_opponent_imps_threat_when_player_id_swapped()
