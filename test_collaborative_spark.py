#!/usr/bin/env python3
"""协作火花 END_014：3 伤；消灭随从则友方 +3/+3。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence
from hdt_python.spell_p0_other import _apply_collaborative_spark
from hdt_python.combat_sim import project_board_face_after_spell


def _minion(taunts, eid, hp, *, atk=1, taunt=False):
    taunts.append({
        "kind": "minion", "entity_id": eid, "atk": atk, "health": hp,
        "taunt": taunt, "shield": False,
    })


def _fighter(fighters, eid, atk, hp, *, attacks_left=1):
    fighters.append({
        "kind": "minion", "entity_id": eid, "atk": atk, "health": hp,
        "attacks_left": attacks_left, "can_face": True, "rush": False,
    })


def test_registered():
    defn = get_board_spell_def("END_014")
    assert defn is not None
    assert defn.name == "协作火花"
    assert defn.base_cost == 4


def test_kill_minion_buffs_friendly():
    taunts, fighters = [], []
    _minion(taunts, 10, 3, taunt=True)
    _fighter(fighters, 20, 2, 4, attacks_left=1)
    res = _apply_collaborative_spark(
        taunts, fighters, mult=1, enemy_shield=False,
    )
    assert not any(m.get("entity_id") == 10 for m in taunts)
    assert fighters[0]["atk"] == 5
    assert fighters[0]["health"] == 7
    assert res.direct_face_damage == 0
    assert project_board_face_after_spell(taunts, fighters, False) == 5


def test_face_when_no_kill_buff():
    taunts, fighters = [], []
    _fighter(fighters, 20, 4, 4, attacks_left=1)
    res = _apply_collaborative_spark(
        taunts, fighters, mult=1, enemy_shield=False,
    )
    assert res.direct_face_damage == 3
    assert fighters[0]["atk"] == 4


def test_from_power_log_kill_and_buff():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_09_23_18_21\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 84228
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[-1])
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    assert get_board_spell_def("END_014") is not None


if __name__ == "__main__":
    test_registered()
    test_kill_minion_buffs_friendly()
    test_face_when_no_kill_buff()
    test_from_power_log_kill_and_buff()
    print("OK collaborative spark")
