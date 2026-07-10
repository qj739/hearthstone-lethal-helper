#!/usr/bin/env python3
"""列出已注册法术的模拟分层（清场 / 清场+打脸 / 直伤 / 功能）。"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hdt_python.spell_board import (  # noqa: E402
    BOARD_CLEAR_SPELLS,
    SPELL_SIM_TIER_LABELS,
    SpellSimTier,
    spell_sim_tier,
)


def main() -> None:
    seen: set[str] = set()
    by_tier: dict[SpellSimTier, list[tuple[str, str, bool]]] = defaultdict(list)
    for cid, defn in sorted(BOARD_CLEAR_SPELLS.items()):
        if defn.name in seen:
            continue
        seen.add(defn.name)
        tier = spell_sim_tier(defn)
        by_tier[tier].append((defn.name, defn.card_ids[0], defn.uses_random))

    for tier in SpellSimTier:
        items = by_tier[tier]
        print(f"\n## {SPELL_SIM_TIER_LABELS[tier]} ({len(items)})")
        for name, cid, ur in sorted(items, key=lambda x: x[0]):
            flag = " [随机]" if ur else ""
            print(f"  {name} ({cid}){flag}")


if __name__ == "__main__":
    main()
