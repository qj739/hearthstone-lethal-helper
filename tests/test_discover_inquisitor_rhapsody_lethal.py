#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""橱窗看客发现的审判官（6/5）+ 动情狂想曲：应识别斩杀。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import hand_minion_attack, hand_minion_health
from hdt_python.rush_p0 import _apply_illidari_inquisitor

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_08_08_15_10_30\Power.log"
)
# 打出动情狂想曲前的可选牌状态
TARGET = 366814


def test_hand_inquisitor_uses_discover_stats():
    """发现变身材后召唤应是 6/5，不是牌面 8/8。"""
    from hdt_python.power_parser import Entity

    card = Entity(entity_id=1, cardtype="MINION")
    card.card_id = "CS3_020"
    card.zone = "HAND"
    card.tags = {
        "ZONE": "HAND", "ATK": 6, "479": 8, "HEALTH": 5, "COST": 5, "RUSH": 1,
    }
    card.atk = 8
    card.health = 5
    assert hand_minion_attack(card) == 6
    assert hand_minion_health(card) == 5
    fighters = []
    _apply_illidari_inquisitor([], fighters, mult=1, card=card)
    assert fighters[0]["atk"] == 6
    assert fighters[0]["health"] == 5
    assert fighters[0].get("mirrors_hero_attack")


def test_rhapsody_inquisitor_lethal_from_log():
    if not LOG.is_file():
        print("SKIP log")
        return
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < TARGET)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, TARGET):
            p.process_line(lines[i].rstrip())
    gs.in_game = True

    card = next(c for c in gs.get_hand(1) if c.card_id == "CS3_020")
    assert hand_minion_attack(card) == 6, (
        hand_minion_attack(card), card.tags.get("ATK"), card.tags.get("479")
    )
    assert "JAM_018t3" in [c.card_id for c in gs.get_hand(1)]

    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        _total, _src, lethal = lc.calculate_lethal_potential()
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert face >= 9, (face, note)
    assert lethal, (face, note)
    # 正确线：动情狂想曲（+5 英雄攻）+ 审判官跟刀；爪+6 不够 9
    assert "混搭狂想曲" in note or "动情" in note, note
    assert "审判官" in note, note
    print("OK rhapsody+inquisitor lethal", face, note)


if __name__ == "__main__":
    test_hand_inquisitor_uses_discover_stats()
    print("OK unit")
    test_rhapsody_inquisitor_lethal_from_log()
    print("OK log")
