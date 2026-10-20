#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黑帝国王朝（BE_）新卡接入冒烟测试。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _be_collectible_ids() -> list[str]:
    cards = json.loads((ROOT / "json" / "cards.json").read_text(encoding="utf-8"))
    return sorted(
        c["id"]
        for c in cards
        if c.get("set") == "BE" and c.get("collectible") and c.get("id")
    )


def test_be_cards_in_local_json():
    ids = _be_collectible_ids()
    assert len(ids) == 135, f"expected 135 BE collectibles, got {len(ids)}"


def test_be_lethal_modules_registered():
    from hdt_python.arena_season_bulk import register_arena_season_gap
    from hdt_python.spell_board import BOARD_CLEAR_SPELLS, get_board_spell_def
    from hdt_python.battlecry_board import BOARD_BATTLECRY
    from hdt_python.rush_board import BOARD_RUSH
    from hdt_python.weapon_board import BOARD_WEAPON
    from hdt_python.location_board import BOARD_LOCATION

    register_arena_season_gap()

    # 关键法术
    for cid in ("BE_071", "BE_086", "BE_153", "BE_183", "BE_223", "BE_258",
                "BE_284", "BE_302", "BE_325", "BE_554", "BE_730", "BE_877"):
        assert get_board_spell_def(cid) is not None, cid

    # 战吼 / 突袭 / 武器 / 地标
    assert "BE_994" in BOARD_BATTLECRY or get_board_spell_def("BE_994")
    assert "BE_732" in BOARD_BATTLECRY
    assert "BE_733" in BOARD_RUSH
    assert "BE_560" in BOARD_RUSH or "BE_560" in BOARD_BATTLECRY
    assert "BE_000" in BOARD_WEAPON
    assert "BE_251" in BOARD_LOCATION

    be_ids = set(_be_collectible_ids())
    spell_hits = sum(1 for c in be_ids if c in BOARD_CLEAR_SPELLS)
    bc_hits = sum(1 for c in be_ids if c in BOARD_BATTLECRY)
    # 43 法术应全部进法术表；战吼大量在 BOARD_BATTLECRY
    assert spell_hits >= 40, spell_hits
    assert bc_hits >= 50, bc_hits


def test_be_clockwork_boars_summon_charge():
    from hdt_python.arena_season_bulk import register_arena_season_gap
    from hdt_python.spell_board import get_board_spell_def

    register_arena_season_gap()
    defn = get_board_spell_def("BE_730")
    assert defn is not None
    taunts: list = [{"kind": "hero", "health": 30, "armor": 0}]
    fighters: list = []
    defn.apply(taunts, fighters, mult=1, enemy_shield=False)
    mins = [u for u in fighters if u.get("kind") == "minion"]
    assert len(mins) == 2
    assert all(u.get("can_face") for u in mins)
    assert sum(u.get("atk", 0) for u in mins) == 2


def test_be_astral_rain_minion_only():
    from hdt_python.arena_season_bulk import register_arena_season_gap
    from hdt_python.spell_board import get_board_spell_def

    register_arena_season_gap()
    defn = get_board_spell_def("BE_258")
    assert defn is not None
    taunts = [
        {"kind": "hero", "health": 30, "armor": 0, "entity_id": 1},
        {"kind": "minion", "health": 10, "atk": 1, "entity_id": 2},
    ]
    fighters: list = []
    res = defn.apply(taunts, fighters, mult=1, enemy_shield=False, rng=__import__("random").Random(0))
    # 5×2=10 全打在随从上，英雄仍满血
    assert taunts[0]["health"] == 30
    assert taunts[1]["health"] <= 0 or int(getattr(res, "face_damage", 0) or 0) == 0
