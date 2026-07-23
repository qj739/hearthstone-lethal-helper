#!/usr/bin/env python3
"""对手英雄圣盾：火冲破盾后火球/场面应按无盾计入斩杀。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import hero_has_divine_shield
from hdt_python.spell_board import (
    SpellApplyResult,
    _apply_direct_face,
    apply_spell_sequence,
    get_board_spell_def,
)
from hdt_python.hero_power_p0 import _apply_mage_fireblast


LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_22_12_18_28\Power.log"
)
# 我方回合、火冲破盾之前（对手阿尔萨斯有圣盾，约 10 有效血 + 嘲讽幼龙）
LINE_BEFORE_FIREBLAST = 571993


def test_direct_face_marks_shield_break():
    res = _apply_direct_face(1, True)
    assert res.direct_face_damage == 0
    assert res.broke_enemy_hero_shield is True
    res2 = _apply_direct_face(6, False)
    assert res2.direct_face_damage == 6
    assert res2.broke_enemy_hero_shield is False


def test_fireblast_then_fireball_sequence_breaks_shield():
    """序列内：火冲破盾后火球应打满 6。"""
    fireball = get_board_spell_def("CORE_CS2_029")
    assert fireball is not None

    class _Card:
        entity_id = 1
        card_id = "CORE_CS2_029"
        tags: dict = {}

    # 仅火球、有盾 → 0
    alone = apply_spell_sequence(
        [], [], [(fireball, 4, _Card())], enemy_shield=True,
    )
    assert alone.direct_face_damage == 0
    assert alone.broke_enemy_hero_shield is True

    # 火冲结果并入后，第二段火球应无盾
    hp = _apply_mage_fireblast([], [], mult=1, enemy_shield=True)
    assert hp.direct_face_damage == 0
    assert hp.broke_enemy_hero_shield is True
    after = apply_spell_sequence(
        [], [], [(fireball, 4, _Card())], enemy_shield=False,
    )
    assert after.direct_face_damage == 6


def test_log_before_fireblast_finds_lethal():
    """日志回放：破盾前应识别火冲+火球(+解嘲打脸)斩杀。"""
    if not LOG.is_file():
        print("SKIP missing power log")
        return
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i for i, l in enumerate(lines[:LINE_BEFORE_FIREBLAST])
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    assert starts, "no CREATE_GAME"
    start = starts[-1]
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, LINE_BEFORE_FIREBLAST):
            if lines[i].strip():
                p.process_line(lines[i].rstrip())
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    opp = gs.get_hero(2)
    assert hero_has_divine_shield(opp), "expected enemy hero divine shield"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _sources, has_lethal = lc.calculate_lethal()
    red = lc.overlay_red_prompt_ok()
    note = lc.overlay_spell_note()
    hp_name = getattr(lc, "_overlay_best_hp_name", None)
    assert face >= 10, f"expected face>=10 got {face} note={note!r} hp={hp_name}"
    assert has_lethal or red, (
        f"expected lethal/red face={face} lethal={has_lethal} red={red} "
        f"total={total} note={note!r} hp={hp_name}"
    )
    print("OK hero shield lethal", face, note, hp_name)


if __name__ == "__main__":
    test_direct_face_marks_shield_break()
    test_fireblast_then_fireball_sequence_breaks_shield()
    test_log_before_fireblast_finds_lethal()
    print("all ok")
