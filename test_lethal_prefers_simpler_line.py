#!/usr/bin/env python3
"""斩杀已够时，overlay 应优先更短打法，而非叠更多法术冲场攻。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker


def _replay_to_line(line_no: int) -> GameState:
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_23_13_05_13\Power.log"
    )
    if not log.is_file():
        return None
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:line_no]:
            if line.strip():
                parser.process_line(line.rstrip())
    return gs


def test_dubious_purchase_alone_not_stacked_with_natural_causes():
    """可疑交易单独可斩时，不应再推荐叠自然死亡。"""
    gs = _replay_to_line(77700)
    if gs is None:
        print("SKIP dubious lethal log replay (log missing)")
        return

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    combo = lc.overlay_combo_display_lines()
    _, _, has_lethal = lc.calculate_lethal_potential()

    assert has_lethal, (face, note, combo)
    assert face >= 14, face
    assert "自然死亡" not in note, note
    assert not any("自然死亡" in ln for ln in combo), combo
    assert "可疑交易" in note or any("可疑交易" in ln for ln in combo), (note, combo)
    print("OK simpler dubious lethal", face, note)


if __name__ == "__main__":
    test_dubious_purchase_alone_not_stacked_with_natural_causes()
