#!/usr/bin/env python3
"""回归：18 血假斩杀 — 加尔手臂 ATK 不应重复叠附魔。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker

LOG = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_21_11_17_49\Power.log")
CREATE = 272981
TARGET = 288981


def test_chogall_turn_start_not_lethal_on_18():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(CREATE - 1, TARGET):
            p.process_line(lines[i].rstrip())
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face < 18, face
    assert not has, (face, has, lc.overlay_spell_note())
    print("OK chogall turn start no false lethal on 18", face)


if __name__ == "__main__":
    test_chogall_turn_start_not_lethal_on_18()
