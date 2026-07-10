#!/usr/bin/env python3
"""斩杀步骤：overlay 模拟无步骤时回退快速斩杀来源。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.lethal_checker import DamageSource, LethalChecker
from hdt_python.overlay_combo_format import build_combo_lines_for_display
from hdt_python.power_parser import GameState


def test_quick_sources_fallback_when_no_overlay_seq():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    lc = LethalChecker(gs)
    lc._overlay_best_seq = []
    lc._overlay_best_hp_name = None
    lc._last_quick_lethal_sources = [
        DamageSource("spell", 3, "法术 CORE_CS2_029", 3),
        DamageSource("board", 5, "场面攻击 [随从A]"),
    ]
    # 仅标题、无编号步骤时走快速斩杀回退
    from hdt_python import overlay_combo_format as ocf

    def _empty_steps(_checker):
        return ["⚔ 斩杀步骤"]

    orig = ocf.build_lethal_combo_lines
    ocf.build_lethal_combo_lines = _empty_steps
    try:
        lines = ocf.build_combo_lines_for_display(lc)
    finally:
        ocf.build_lethal_combo_lines = orig
    assert any("法术 CORE_CS2_029" in ln for ln in lines)
    assert any("场面攻击" in ln for ln in lines)
    print("OK quick sources combo fallback", lines)


if __name__ == "__main__":
    test_quick_sources_fallback_when_no_overlay_seq()
