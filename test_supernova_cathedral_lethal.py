#!/usr/bin/env python3
"""回归：超新星填手后，赎罪教堂 buff + 场面 + 地狱烈焰 应识别 20 血斩杀。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_22_15_41_10\Power.log"
)
TARGET = 56120


def test_supernova_cathedral_lethal_at_56120():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < TARGET), default=starts[0])
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, TARGET):
            p.process_line(lines[i].rstrip())
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert gs.get_hero(2).health - gs.get_hero(2).damage == 20
    assert face >= 20, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert has, (face, has, lc.overlay_spell_note(), lc.overlay_combo_display_lines())
    print("OK supernova cathedral lethal", face, lc.overlay_spell_note())


if __name__ == "__main__":
    test_supernova_cathedral_lethal_at_56120()
