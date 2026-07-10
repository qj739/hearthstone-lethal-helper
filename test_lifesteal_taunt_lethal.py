#!/usr/bin/env python3
"""回归：对手吸血嘲讽抬高有效血量，场攻不足时不应误报斩杀。"""
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
TARGET = 199720


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


def test_lifesteal_taunt_gdb_320_not_false_lethal():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(TARGET)
    opp = gs.opponent_player_id
    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _, _, lethal = lc.calculate_lethal_potential()
    opp_hp = gs.get_hero(opp).health - gs.get_hero(opp).damage
    ls = getattr(lc, "_overlay_lifesteal_heal", 0)
    assert opp_hp == 7, opp_hp
    assert ls >= 8, (face, ls, lc.overlay_spell_note())
    assert face < opp_hp + ls, (face, opp_hp, ls)
    assert not lethal, (face, opp_hp, ls, lethal, lc.overlay_spell_note())
    print("OK lifesteal taunt GDB_320 no false lethal", face, "eff", opp_hp + ls, "ls", ls)


if __name__ == "__main__":
    test_lifesteal_taunt_gdb_320_not_false_lethal()
