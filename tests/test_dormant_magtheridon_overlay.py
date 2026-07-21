#!/usr/bin/env python3
"""休眠玛瑟里顿：场攻展示不含 +3；对手回合若下回合会苏醒则斩杀也不计「回」。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_spell_board import _hero, _minion
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _attach_mag_dormant_enchant(gs, mag_eid: int, *, progress: int, total: int = 2):
    """挂上 TOY_647e2 清扫倒计时（SCORE_VALUE_2 / SCORE_VALUE_1）。"""
    enc = gs.get_entity(mag_eid + 1000)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "TOY_647e2"
    enc.zone = "PLAY"
    enc.controller = gs.entities[mag_eid].controller
    enc.tags["ZONE"] = "PLAY"
    enc.tags["ATTACHED"] = mag_eid
    enc.tags["DORMANT_AWAKEN_CONDITION_ENCHANT"] = 1
    enc.tags["SCORE_VALUE_1"] = total
    enc.tags["SCORE_VALUE_2"] = progress
    return enc


def test_dormant_magtheridon_overlay_display_wakes_next_turn():
    """对手回合、倒计时已满一拍：下回合开局苏醒 → 斩杀不计 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2  # 对方回合 → 下回合场攻视角
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    _minion(gs, 10, 1, 1, 2, card_id="WW_816t")
    _minion(gs, 11, 1, 3, 4, card_id="CATA_304")
    mag = _minion(gs, 12, 1, 12, 12, card_id="TOY_647")
    mag.tags["DORMANT"] = 1
    _attach_mag_dormant_enchant(gs, 12, progress=1, total=2)
    _minion(gs, 13, 1, 1, 2, card_id="WW_816t")

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()
    dormant_et = lc.overlay_dormant_end_turn_face()

    assert minion == 5, f"minion breakdown should be 5, got {minion}"
    assert display == 5, f"display face should exclude dormant ET, got {display}"
    assert dormant_et == 0, f"waking Mag should not count ET, got {dormant_et}"
    assert lethal == 5, f"lethal should exclude waking Mag ET, got {lethal}"
    assert pure == 5, f"pure immediate should be 5, got {pure}"
    print("OK dormant magtheridon wakes next turn", display, lethal)


def test_dormant_magtheridon_overlay_still_dormant_next_turn():
    """对手回合、倒计时未到：下回合仍休眠 → 斩杀计 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    _minion(gs, 10, 1, 1, 2, card_id="WW_816t")
    _minion(gs, 11, 1, 3, 4, card_id="CATA_304")
    mag = _minion(gs, 12, 1, 12, 12, card_id="TOY_647")
    mag.tags["DORMANT"] = 1
    _attach_mag_dormant_enchant(gs, 12, progress=0, total=2)
    _minion(gs, 13, 1, 1, 2, card_id="WW_816t")

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    display = lc.overlay_display_face()
    lethal = lc.cached_overlay_face()
    dormant_et = lc.overlay_dormant_end_turn_face()

    assert display == 5, f"display should still be 5, got {display}"
    assert dormant_et == 3, f"still-dormant Mag ET should be 3, got {dormant_et}"
    assert lethal == 8, f"lethal should include Mag ET +3, got {lethal}"
    print("OK dormant magtheridon still dormant next turn", display, lethal)


def test_dormant_magtheridon_local_turn_counts_et():
    """我方回合休眠中：本回合结束仍触发 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    mag = _minion(gs, 12, 1, 12, 12, card_id="TOY_647")
    mag.tags["DORMANT"] = 1
    _attach_mag_dormant_enchant(gs, 12, progress=0, total=2)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    dormant_et = lc.overlay_dormant_end_turn_face()
    assert dormant_et == 3, f"local-turn Mag ET should be 3, got {dormant_et}"
    assert total == 3, f"expected 3, got {total}"
    print("OK dormant magtheridon local turn ET", total)


if __name__ == "__main__":
    test_dormant_magtheridon_overlay_display_wakes_next_turn()
    test_dormant_magtheridon_overlay_still_dormant_next_turn()
    test_dormant_magtheridon_local_turn_counts_et()
    print("all passed")
