#!/usr/bin/env python3
"""可疑交易未连击时不应虚增场攻（Power.log 265855 局面）。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_25_10_30_49\Power.log"
)
START = 202685
TARGET = 265855


def test_dubious_without_combo_does_not_inflate_face_to_21():
    if not LOG.is_file():
        print("SKIP missing Power.log")
        return

    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[START:TARGET]:
            if line.strip():
                parser.process_line(line.rstrip())

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    pure, minion_board, _, _, _ = lc.overlay_board_breakdown()
    note = lc.overlay_spell_note()

    board_ids = {m.card_id for m in gs.get_board(gs.local_player_id)}
    assert board_ids >= {"CATA_201", "YOG_403", "EDR_260"}, board_ids
    assert face < 21, (face, pure, minion_board, note)
    assert face <= 17, (face, pure, minion_board, note)
    print("OK dubious no combo face", face, pure, minion_board, note)


if __name__ == "__main__":
    test_dubious_without_combo_does_not_inflate_face_to_21()
