#!/usr/bin/env python3
"""一串香蕉 ETC_201：友方 +1/+1，同回合可连打 3 次。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.spell_board import (
    apply_spell_sequence,
    get_board_spell_def,
    spell_sequence_mana_left,
)
from hdt_python.combat_sim import project_board_face_after_spell


def _fighter(fighters, eid, atk, hp, *, attacks_left=1):
    fighters.append({
        "kind": "minion", "entity_id": eid, "atk": atk, "health": hp,
        "attacks_left": attacks_left, "can_face": True, "rush": False,
    })


def _hand_spell(gs, eid, pid, card_id):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = 1
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 1
    return s


def test_registered():
    defn = get_board_spell_def("ETC_201")
    assert defn is not None
    assert defn.name == "一串香蕉"
    assert get_board_spell_def("ETC_201t") is defn


def test_triple_banana_buff_same_turn():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    _fighter(fighters, 20, 3, 5, attacks_left=1)
    seq = [(defn, 1, card)]
    apply_spell_sequence([], fighters, seq, gs=gs, player_id=1, mana_budget=3)
    assert fighters[0]["atk"] == 6
    assert fighters[0]["health"] == 8
    assert project_board_face_after_spell([], fighters, False) == 6


def test_mana_budget_counts_three_bananas():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    seq = [(defn, 1, card)]
    left = spell_sequence_mana_left(seq, 3)
    assert left == 0


def test_single_banana_with_1_mana():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    _fighter(fighters, 20, 2, 4, attacks_left=1)
    apply_spell_sequence([], fighters, seq := [(defn, 1, card)], gs=gs, player_id=1, mana_budget=1)
    assert fighters[0]["atk"] == 3


def test_from_power_log():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_10_10_22_36\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 335358
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
    touch = next(c for c in gs.get_hand(1) if c.card_id == "ETC_201")
    assert get_board_spell_def(touch.card_id) is not None


if __name__ == "__main__":
    test_registered()
    test_triple_banana_buff_same_turn()
    test_mana_budget_counts_three_bananas()
    test_single_banana_with_1_mana()
    test_from_power_log()
    print("OK banana bunch")
