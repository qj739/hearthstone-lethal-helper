#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""间接伤害 REV_369：随机三随从 $6，溢出打脸（概率斩杀）。"""

import contextlib
import io
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker, MIN_LETHAL_PROMPT_PROB
from hdt_python.spell_board import get_board_spell_def, hand_board_spells
from hdt_python.spell_p0_aoe import _apply_collateral_damage

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_08_06_21_14_42\Power.log"
)
# 打出间接伤害前（PLAY 块开始）
TARGET = 470566


def _minion(hp, *, shield=False, eid=1):
    return {
        "kind": "minion",
        "entity_id": eid,
        "atk": 1,
        "health": hp,
        "shield": shield,
        "taunt": False,
    }


def test_registered():
    for cid in ("REV_369", "CORE_REV_369"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name == "间接伤害"
        assert defn.uses_random
        assert defn.base_cost == 8


def test_excess_face_damage():
    """1+1+1 血各吃 6 → 溢出 15 打脸。"""
    taunts = [_minion(1, eid=i) for i in (1, 2, 3)]
    res = _apply_collateral_damage(
        taunts, [], mult=1, enemy_shield=False, rng=random.Random(0),
    )
    assert res.direct_face_damage == 15, res.direct_face_damage
    assert all(t.get("health", 0) <= 0 for t in taunts)


def test_shield_no_excess():
    taunts = [_minion(1, shield=True, eid=1), _minion(1, eid=2), _minion(1, eid=3)]
    res = _apply_collateral_damage(
        taunts, [], mult=1, enemy_shield=False, rng=random.Random(1),
    )
    # 圣盾目标无溢出，另两只各 +5 → 10
    assert res.direct_face_damage == 10, res.direct_face_damage
    assert taunts[0].get("shield") is False
    assert taunts[0].get("health") == 1


def test_log_probabilistic_lethal():
    """
    复盘：场攻 13，对手 26；间接伤害溢出 11~15。
    约 40% 组合可斩（溢出≥13），应报概率斩杀。
    """
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
    local = gs.local_player_id
    assert any(c.card_id == "REV_369" for c in gs.get_hand(local)), [
        c.card_id for c in gs.get_hand(local)
    ]
    assert get_board_spell_def("REV_369") is not None
    assert any(c.card_id == "REV_369" for c, _, _ in hand_board_spells(gs, local, 10))

    lc = LethalChecker(gs)
    with contextlib.redirect_stdout(io.StringIO()):
        face = lc.overlay_board_face_damage()
        mc_max, prob, uses_random, _top = lc.overlay_face_stats()
        _total, _src, lethal = lc.calculate_lethal_potential()
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert uses_random, note
    assert "间接伤害" in note, note
    assert mc_max >= 26, (mc_max, face, note)
    assert prob >= MIN_LETHAL_PROMPT_PROB, (prob, note)
    # 非保斩：部分随机结果不够
    assert prob < 1.0, prob
    assert lethal or prob >= MIN_LETHAL_PROMPT_PROB


if __name__ == "__main__":
    test_registered()
    test_excess_face_damage()
    test_shield_no_excess()
    print("OK unit")
    test_log_probabilistic_lethal()
    print("OK log")
