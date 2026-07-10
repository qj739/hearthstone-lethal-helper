#!/usr/bin/env python3
"""神圣新星 + 拦住他们！：清嘲后 buff 再打脸应识别斩杀。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_09_16_03_26\Power.log"
)
TARGET = 365388


def _parse_to_line(target: int) -> GameState:
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[-1])
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    return gs


def test_holy_nova_hold_lethal_from_power_log():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _parse_to_line(TARGET)
    lc = LethalChecker(gs)
    opp = gs.get_hero(2)
    opp_hp = opp.health - opp.damage
    total, _, lethal = lc.calculate_lethal_potential()
    face = lc.overlay_board_face_damage()
    assert opp_hp == 14, opp_hp
    assert face >= 14, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert lethal, (total, face, lc.overlay_spell_note())


def test_rush_veteran_can_face_after_clear():
    """上场已满一回合的突袭不应被强制先去解场。"""
    from hdt_python.combat_sim import exhaust_rush_on_enemy_minions

    fighters = [
        {
            "kind": "minion", "entity_id": 1, "atk": 3, "health": 2,
            "attacks_left": 1, "rush": True, "can_face": True,
        },
        {
            "kind": "minion", "entity_id": 2, "atk": 7, "health": 7,
            "attacks_left": 1, "rush": False, "can_face": True,
        },
    ]
    enemy = [
        {"kind": "minion", "entity_id": 10, "health": 3, "atk": 4, "taunt": False},
    ]
    fs, board = exhaust_rush_on_enemy_minions(fighters, enemy)
    assert fs[0]["attacks_left"] == 1
    assert fs[0]["atk"] == 3


if __name__ == "__main__":
    test_rush_veteran_can_face_after_clear()
    test_holy_nova_hold_lethal_from_power_log()
    print("OK holy nova + hold them off lethal")
