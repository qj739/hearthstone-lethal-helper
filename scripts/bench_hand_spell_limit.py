#!/usr/bin/env python3
"""对比 MAX_HAND_SPELLS_FOR_SEARCH=6 vs 7 的 overlay 耗时（超新星 7 法术用例）。"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hdt_python.battlecry_board import hand_all_board_plays
from hdt_python.lethal_checker import LethalChecker
import hdt_python.lethal_checker as lc
from hdt_python.power_parser import GameState


def build_gs() -> GameState:
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    h1 = gs.get_entity(1)
    h1.cardtype = "HERO"
    h1.controller = 1
    h1.health = 30
    h1.tags.update({"RESOURCES": 10, "RESOURCES_USED": 0})
    gs.hero_entity_ids[1] = 1
    h2 = gs.get_entity(2)
    h2.cardtype = "HERO"
    h2.controller = 2
    h2.health = 30
    gs.hero_entity_ids[2] = 2
    for i in range(5):
        m = gs.get_entity(20 + i)
        m.cardtype = "MINION"
        m.controller = 2
        m.zone = "PLAY"
        m.atk = 2
        m.health = 2
        m.tags["ZONE"] = "PLAY"
        m.tags["NUM_TURNS_IN_PLAY"] = 1
        pos = i + 1
        m.tags["ZONE_POSITION"] = pos
        gs.board_slots.setdefault(2, {})[pos] = 20 + i
    for cid, eid in [
        ("WW_427", 30),
        ("TLC_227", 31),
        ("TOY_500", 32),
        ("CS2_029", 33),
        ("KAR_076", 35),
        ("FIR_910", 36),
        ("WW_405", 37),  # 迅疾连射
    ]:
        s = gs.get_entity(eid)
        s.cardtype = "SPELL"
        s.controller = 1
        s.zone = "HAND"
        s.card_id = cid
        s.cost = 1
        s.tags["ZONE"] = "HAND"
        s.tags["COST"] = 1
    return gs


def bench(limit: int, runs: int = 5, warmup: int = 1) -> dict:
    lc.MAX_HAND_SPELLS_FOR_SEARCH = limit
    times: list[float] = []
    total = note = None
    kept: list[str] | None = None
    seq_count = None
    for r in range(warmup + runs):
        gs = build_gs()
        plays = hand_all_board_plays(gs, 1, 10)
        trimmed = LethalChecker._trim_hand_spells_for_search(plays, 10)
        if r == warmup:
            kept = sorted(x[1].name for x in trimmed)
            checker = LethalChecker(gs)
            board_view = gs.get_overlay_board(1)
            fighters = checker._build_fighters(board_view, 1)
            enemy = checker._build_enemy_minion_states(1)
            opp = gs.opponent_player_id
            opp_hero = gs.get_hero(opp) if opp else None
            shield = bool(opp_hero and opp_hero.tags.get("DIVINE_SHIELD", 0) == 1)
            from hdt_python.spell_board import spell_effect_multiplier
            combo_hand, _, _, combo_mana, _ = checker._no_taunt_direct_face_setup(
                plays, 10,
                spell_mult=spell_effect_multiplier(gs, 1),
                defender_shield=shield,
                player_id=1,
                opp_taunts=[],
            )
            trimmed_combo = LethalChecker._trim_hand_spells_for_search(combo_hand, combo_mana)
            seq_count = len(checker._enumerate_spells_for_search(
                trimmed_combo, combo_mana,
                enemy_minions=enemy,
                fighters=fighters,
                spell_mult=spell_effect_multiplier(gs, 1),
                defender_shield=shield,
                player_id=1,
            ))
        t0 = time.perf_counter()
        checker = LethalChecker(gs)
        total = checker.overlay_board_face_damage()
        note = checker.overlay_spell_note()
        dt = time.perf_counter() - t0
        if r >= warmup:
            times.append(dt)
    assert kept is not None and total is not None and seq_count is not None
    return {
        "limit": limit,
        "kept": kept,
        "seq_count": seq_count,
        "total": total,
        "note": note,
        "mean_ms": statistics.mean(times) * 1000,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000,
        "runs": runs,
    }


def main() -> None:
    print("用例: 对方5x2/2, 10费, 7张1费法术(超新星+迅疾连射)")
    print("MAX_SPELL_COMBO_LEN = 7")
    print()
    results = [bench(6), bench(7)]
    for r in results:
        print(f"--- MAX_HAND_SPELLS_FOR_SEARCH = {r['limit']} ---")
        print("保留:", ", ".join(r["kept"]))
        print("枚举序列数:", r["seq_count"])
        print("场攻:", r["total"], "|", r["note"])
        print(
            f"耗时 {r['runs']}次: "
            f"mean={r['mean_ms']:.1f}ms "
            f"min={r['min_ms']:.1f}ms "
            f"max={r['max_ms']:.1f}ms"
        )
        print()
    a, b = results[0]["mean_ms"], results[1]["mean_ms"]
    ratio = b / a if a > 0 else 0
    print(f"7张 vs 6张: mean {b:.1f}ms / {a:.1f}ms ≈ {ratio:.2f}x")


if __name__ == "__main__":
    main()
