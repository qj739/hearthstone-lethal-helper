#!/usr/bin/env python3
"""导出 ARENA_NEW_CARDS_ADDED.md（需先完成 arena_season_bulk 注册）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hdt_python import spell_board  # noqa: F401
from hdt_python.arena_season_bulk import register_arena_season_gap

register_arena_season_gap()
from hdt_python.arena_season_bulk import write_new_cards_md

if __name__ == "__main__":
    out = write_new_cards_md()
    print(f"Wrote {out}")
