#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PowerTaskList 滞后 DAMAGE 不得覆盖 GameState 已结算血量（假斩杀回归）。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_08_06_21_14_42\Power.log"
)
# 我方回合可选牌时（绒绒虎吸血后对手应为 20 血）
TURN_OPTIONS = 432960


def test_tasklist_damage_does_not_overwrite_gamestate():
    gs = GameState()
    gs.in_game = True
    p = PowerLogParser("x", gs)
    p._live_mode = False
    hero = gs.get_entity(68)
    hero.cardtype = "HERO"
    hero.controller = 2
    hero.health = 30
    hero.damage = 0
    gs.hero_entity_ids[2] = 68

    # GameState 终态：吸血后 DAMAGE=10（20 血）
    p.process_line(
        "D 00:00:00.0 GameState.DebugPrintPower() - "
        "TAG_CHANGE Entity=[entityName=h id=68 zone=PLAY zonePos=0 "
        "cardId=HERO_04 player=2] tag=DAMAGE value=10"
    )
    assert hero.damage == 10

    # PowerTaskList 重放中间态 DAMAGE=11，必须忽略
    p.process_line(
        "D 00:00:01.0 PowerTaskList.DebugPrintPower() - "
        "TAG_CHANGE Entity=[entityName=h id=68 zone=PLAY zonePos=0 "
        "cardId=HERO_04 player=2] tag=DAMAGE value=11"
    )
    assert hero.damage == 10, f"stale tasklist overwrote damage to {hero.damage}"


def test_last_wave_needs_call_of_the_wild_not_beetle_only():
    """
    复盘：对手绒绒虎吸血后 20 血；场攻+技能+甲虫冲锋=19 不够，
    须兽群呼唤才斩。修复前 TaskList 把血盖回 19 → 误报甲虫线可斩。
    """
    if not LOG.is_file():
        print("SKIP (log missing)")
        return

    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < TURN_OPTIONS)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, TURN_OPTIONS):
            p.process_line(lines[i].rstrip())
    gs.in_game = True

    oh = gs.get_hero(gs.opponent_player_id)
    assert oh.damage == 10, f"expected DAMAGE=10 got {oh.damage}"
    assert oh.health - oh.damage == 20

    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _total, _src, lethal = lc.calculate_lethal_potential()
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")

    assert face >= 20, (face, note)
    assert lethal, (face, note)
    assert "兽群呼唤" in note, note
    # 不应再走「仅技能+甲虫」假斩杀线
    assert not (
        "稳固射击" in note and "兽群呼唤" not in note
    ), note


if __name__ == "__main__":
    test_tasklist_damage_does_not_overwrite_gamestate()
    print("OK unit")
    test_last_wave_needs_call_of_the_wild_not_beetle_only()
    print("OK log replay")
