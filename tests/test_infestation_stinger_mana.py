#!/usr/bin/env python3
"""虫害侵扰须再付费打出毒刺虫；审判假斩回归。

复盘（2026-09-19 倒数第二回合）：10 费，工具报「私运者+审判+虫害+恶魔之爪」斩 22，
但虫害只是把手牌塞两张 1 费毒刺虫，再打出还需 +2 费 → 实际 11>10。
"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence_with_meta
from hdt_python.spell_p0_other import _apply_infestation


def test_infestation_adds_stingers_not_instant_damage():
    res = _apply_infestation([], [], mult=1, enemy_shield=False)
    assert res.direct_face_damage == 0
    assert len(res.add_hand_pending) == 2
    assert all(sid == "TLC_630t" and cost == 1 for sid, cost, _ in res.add_hand_pending)
    assert get_board_spell_def("TLC_630t") is not None


def test_infestation_two_mana_cannot_fire_stingers():
    """只剩 2 费打出虫害时，毒刺虫无法再付费，不应产生打脸。"""
    defn = get_board_spell_def("TLC_902")
    stinger = get_board_spell_def("TLC_630t")
    assert defn and stinger
    # 仅虫害在序列里；apply 会挂起毒刺虫，但 mana=2 只够虫害本身
    total, _, mana_left = apply_spell_sequence_with_meta(
        [], [], [(defn, 2, None)],
        spell_mult=1, enemy_shield=False, mana_budget=2,
    )
    assert total.direct_face_damage == 0, total
    assert mana_left == 0


def test_infestation_four_mana_plays_both_stingers():
    """4 费：虫害 2 + 两张毒刺虫 1+1，应结算两段 2 伤。"""
    defn = get_board_spell_def("TLC_902")
    total, _, mana_left = apply_spell_sequence_with_meta(
        [], [], [(defn, 2, None)],
        spell_mult=1, enemy_shield=False, mana_budget=4,
    )
    assert total.direct_face_damage == 4, total
    assert mana_left == 0


def test_judgment_infestation_false_lethal_replay():
    """复盘倒数第二回合：10 费不应再报审判+虫害假斩。"""
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_09_19_10_54_15\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    target = 376450
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < target)
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    lc = LethalChecker(gs)
    assert lc._available_mana(2) == 10
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    _, _, lethal = lc.calculate_lethal_potential()
    # 若仍含审判+虫害，法力应计入毒刺虫，不得假斩 22
    if "审判" in note and "虫害" in note:
        assert lc._overlay_mana_spent <= 10
        assert not lethal or face < 22, (face, note, lc._overlay_mana_spent)
    # 核心：不能再用「少计 2 费」把 22 血判成确定斩
    if lethal:
        assert overlay_mana_ok(lc), (face, note, lc._overlay_mana_spent)


def overlay_mana_ok(lc: LethalChecker) -> bool:
    spent = int(getattr(lc, "_overlay_mana_spent", 0) or 0)
    budget = int(getattr(lc, "_overlay_mana_budget", 0) or 0)
    return spent <= budget


if __name__ == "__main__":
    test_infestation_adds_stingers_not_instant_damage()
    test_infestation_two_mana_cannot_fire_stingers()
    test_infestation_four_mana_plays_both_stingers()
    test_judgment_infestation_false_lethal_replay()
    print("ok")
