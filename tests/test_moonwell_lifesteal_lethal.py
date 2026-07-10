#!/usr/bin/env python3
"""回归：清场触发吸血时不应选月亮井线抬高有效血而漏判斩杀。"""
import contextlib
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_25_10_30_49\Power.log"
)
TARGET = 14811


def _replay(target: int) -> GameState:
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i
        for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    start = max((s for s in starts if s < target), default=starts[0])
    gs = GameState()
    parser = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[start:target]:
            if line.strip():
                parser.process_line(line.rstrip())
    return gs


def test_moonwell_lifesteal_does_not_suppress_pre_weapon_lethal():
    """挂刀前：对手 5 血，应识别斩杀，而非月亮井清吸血龙抬高有效血。"""
    if not LOG.is_file():
        print("SKIP (log missing)")
        return

    os.environ["HS_PLAYER_NAME"] = "鸡哥在线#5240"
    gs = _replay(TARGET)
    opp = gs.opponent_player_id
    hero = gs.get_hero(opp)
    opp_hp = hero.current_health if hero else 0

    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _, _, lethal = lc.calculate_lethal_potential()

    ls = getattr(lc, "_overlay_lifesteal_heal", 0)
    note = lc.overlay_spell_note()

    assert opp_hp == 5, opp_hp
    assert face >= opp_hp, (face, opp_hp, note)
    assert ls == 0, (face, ls, note)
    assert "月亮井" not in note, note
    assert lethal, (face, opp_hp, ls, lethal, note)
    print("OK pre-weapon lethal", face, note, "ls", ls)


if __name__ == "__main__":
    test_moonwell_lifesteal_does_not_suppress_pre_weapon_lethal()
