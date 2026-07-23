#!/usr/bin/env python3
"""永世裂痕 TIME_441：随机打脸不得按乐观上限误报敌斩。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import register_arena_season_gap
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker, MIN_LETHAL_PROMPT_PROB

register_arena_season_gap()

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_22_12_18_28\Power.log"
)
# 敌手有永世裂痕、我方 4 血且有嘲讽；乐观场攻曾 ≥4 但 MC 斩杀概率为 0
TARGET = 1223000


def _replay(target: int) -> GameState:
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[0])
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    return gs


def test_aeon_rend_random_not_certain_opp_lethal():
    if not LOG.is_file():
        print("SKIP (log missing)")
        return
    gs = _replay(TARGET)
    lc = LethalChecker(gs)
    assert lc.is_opponent_turn()
    my_h, my_a, my_t = lc.get_my_health()
    assert my_t == 4, (my_h, my_a, my_t)
    opp_hand = [c.card_id for c in gs.get_hand(gs.opponent_player_id)]
    assert "TIME_441" in opp_hand, opp_hand

    with contextlib.redirect_stdout(io.StringIO()):
        threat, lethal_prob, uses_random = lc.opponent_overlay_threat_stats()

    assert uses_random, (threat, lethal_prob, uses_random)
    # 随机线可偶然打出 ≥4，但概率低于提示阈值时不得报敌斩
    assert lethal_prob < MIN_LETHAL_PROMPT_PROB, lethal_prob
    assert not lc.opponent_lethal_now(my_t)
    print(
        "OK aeon rend no false opp lethal",
        f"threat={threat} prob={lethal_prob:.2f}",
    )


def test_random_split_enemies_can_hit_hero():
    """永世裂痕等 random_split_enemies 目标含敌方英雄。"""
    from hdt_python.spell_board import get_board_spell_def
    import random

    defn = get_board_spell_def("TIME_441")
    assert defn is not None and defn.uses_random
    res = defn.apply([], [], mult=1, enemy_shield=False, rng=random.Random(0))
    assert res.direct_face_damage > 0, res.direct_face_damage
    print("OK TIME_441 can hit hero", res.direct_face_damage)


if __name__ == "__main__":
    test_random_split_enemies_can_hit_hero()
    test_aeon_rend_random_not_certain_opp_lethal()
