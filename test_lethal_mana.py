#!/usr/bin/env python3
"""斩杀提示须校验当前剩余法力是否够支付最优线路。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_spell_board import _hero, _minion, _hand_spell
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def test_no_lethal_when_starfire_unaffordable():
    """7 费上限已用 5，剩 2 费：场攻 10 但打不出 6 费星火，对手 12 血不应提示斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=7, used=5)
    _hero(gs, 2, 2)
    _hero(gs, 2, 2).health = 12
    _hero(gs, 2, 2).tags["HEALTH"] = 12
    _minion(gs, 10, 1, 10, 10)
    _hand_spell(gs, 30, 1, "EX1_173", 6)

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert lc._available_mana(1) == 2
    assert total >= 10
    assert has_lethal is False, f"only 2 mana left, starfire unaffordable, got lethal total={total}"


def test_lethal_when_starfire_affordable():
    """剩 7 费：场攻 10 + 星火 6 可斩杀 15 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=7, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 15
    opp.tags["HEALTH"] = 15
    _minion(gs, 10, 1, 10, 10)
    _hand_spell(gs, 30, 1, "EX1_173", 6)

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal is True, f"expected lethal with 7 mana, total={total}"
    assert getattr(lc, "_overlay_mana_spent", 0) <= 7


def test_lethal_turn_start_despite_zero_mc_prob_replay_10656():
    """Power.log 最后一局斩杀回合初：确定性场攻 13 对 13 血，MC 因随机药剂 p=0 仍应提示斩杀。"""
    import os
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        os.environ.get(
            "HS_POWER_LOG",
            r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_28_20_28_04\Power.log",
        )
    )
    if not log.is_file():
        return
    os.environ.setdefault("HS_PLAYER_NAME", "鸡哥在线#5240")
    with open(log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    for i in range(1, 10655):
        p.process_line(lines[i])
    lc = LethalChecker(gs)
    _, _, has = lc.calculate_lethal()
    assert lc.get_opponent_effective_hp() == 13
    assert getattr(lc, "_overlay_total_face", 0) >= 13
    assert getattr(lc, "_overlay_uses_random", False)
    assert getattr(lc, "_overlay_lethal_prob", 1.0) == 0.0
    assert has is True


if __name__ == "__main__":
    test_no_lethal_when_starfire_unaffordable()
    test_lethal_when_starfire_affordable()
    test_lethal_turn_start_despite_zero_mc_prob_replay_10656()
    print("all passed")
