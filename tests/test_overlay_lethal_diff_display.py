#!/usr/bin/env python3
"""未确认斩杀时 Overlay 差值不应显示差0却不亮红。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker, MIN_LETHAL_PROMPT_PROB
from hdt_python.power_parser import GameState


class _FakeChecker(LethalChecker):
    """最小桩：模拟 overlay 已算完、MC 抬高 total 但 has_lethal=False。"""

    def __init__(self):
        super().__init__(GameState())
        self._overlay_face_computed = True
        self._overlay_total_face = 8
        self._overlay_mc_max = 11
        self._overlay_lethal_prob = 0.15
        self._overlay_uses_random = True


def test_overlay_diff_damage_not_inflated_when_not_lethal():
    lc = _FakeChecker()
    assert lc.overlay_diff_damage(11, False) == 8
    assert lc.overlay_diff_damage(11, True) == 11


def test_overlay_lethal_diff_note_for_low_random_prob():
    lc = _FakeChecker()
    note = lc.overlay_lethal_diff_note(
        11, 11, has_lethal=False, prompt_lethal=False,
    )
    assert note is not None
    assert "20%" in note or "随机" in note
    assert MIN_LETHAL_PROMPT_PROB == 0.2


def test_apply_overlay_board_lethal_does_not_inflate_total_when_mana_fails(monkeypatch):
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    lc = LethalChecker(gs)
    lc._overlay_face_computed = True
    lc._overlay_incomplete = False
    lc._overlay_total_face = 11
    lc._overlay_mc_max = 11
    lc._overlay_lethal_prob = 1.0
    lc._overlay_uses_random = False
    lc._overlay_mana_spent = 10
    lc._overlay_best_seq = [("fake",)]

    monkeypatch.setattr(lc, "get_opponent_effective_hp", lambda: 11)
    monkeypatch.setattr(lc, "_lethal_threshold_hp", lambda **kw: 11)
    monkeypatch.setattr(lc, "_available_mana", lambda _pid: 4)
    monkeypatch.setattr(
        "hdt_python.overlay_combo_format.overlay_combo_mana_affordable",
        lambda _c: True,
    )

    has, total = lc._apply_overlay_board_lethal(5, [])
    assert has is False
    assert total == 5, "mana 不足时不应把 total 抬到 11 导致 UI 差0"


def test_overlay_red_prompt_ok_on_opponent_turn():
    """对方回合下回合斩预览也应变红（总伤≥对手血）。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    lc = LethalChecker(gs)
    lc._overlay_face_computed = True
    lc._overlay_incomplete = False
    lc._overlay_total_face = 13
    lc._overlay_mc_max = 13
    lc._overlay_lethal_prob = 1.0
    lc._overlay_uses_random = False
    lc.get_opponent_effective_hp = lambda: 13

    assert lc.is_opponent_turn()
    assert not lc.is_local_turn()
    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is True


def test_overlay_red_blocked_when_opp_lethal_now():
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    lc = LethalChecker(gs)
    lc._overlay_face_computed = True
    lc._overlay_total_face = 13
    assert lc.overlay_red_prompt_ok(opp_lethal_now=True) is False


def test_random_optimistic_max_not_red_when_prob_near_zero():
    """夕阳漫射类：MC 上限刚好斩杀但概率≈0 时不应红字（实际常差1）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    lc = LethalChecker(gs)
    lc._overlay_face_computed = True
    lc._overlay_incomplete = False
    lc._overlay_total_face = 20  # 乐观上限
    lc._overlay_mc_max = 20
    lc._overlay_lethal_prob = 0.04
    lc._overlay_uses_random = True
    lc._overlay_top_outcomes = [(20, 0.04), (19, 0.96)]
    lc.get_opponent_effective_hp = lambda: 20

    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is False
    has, _ = lc._apply_overlay_board_lethal(0, [])
    assert has is False


if __name__ == "__main__":
    test_overlay_diff_damage_not_inflated_when_not_lethal()
    test_overlay_lethal_diff_note_for_low_random_prob()
    test_overlay_red_prompt_ok_on_opponent_turn()
    test_overlay_red_blocked_when_opp_lethal_now()
    test_random_optimistic_max_not_red_when_prob_near_zero()
    print("OK overlay diff display (unit)")
