"""缺口报告中的卡应已注册到各 BOARD 表。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hdt_python import spell_board  # noqa: F401 — 触发 spell P0/P1/P2
from hdt_python.arena_season_bulk import register_arena_season_gap, _parse_gap_sections

register_arena_season_gap()
from hdt_python.battlecry_board import BOARD_BATTLECRY
from hdt_python.combo_board import BOARD_COMBO
from hdt_python.deathrattle import DEATHRATTLE_BY_CARD
from hdt_python.end_turn_board import END_TURN_BY_CARD
from hdt_python.rush_board import BOARD_RUSH
from hdt_python.spell_board import BOARD_CLEAR_SPELLS
from hdt_python.weapon_board import BOARD_WEAPON


def _in_board(cid: str, board: dict) -> bool:
    if cid in board:
        return True
    base = cid[5:] if cid.startswith("CORE_") else cid
    return base in board or f"CORE_{base}" in board


def _parse_spell_ids() -> list[str]:
    sections = _parse_gap_sections()
    return sections.get("spell", [])


def test_gap_spells_registered():
    missing = [cid for cid in _parse_spell_ids() if not _in_board(cid, BOARD_CLEAR_SPELLS)]
    assert not missing, f"法术未注册: {missing[:10]}... ({len(missing)} total)"


def test_gap_battlecries_registered():
    sections = _parse_gap_sections()
    missing = [
        cid for cid in sections.get("battlecry", [])
        if not _in_board(cid, BOARD_BATTLECRY)
    ]
    assert not missing, f"战吼未注册: {missing}"


def test_gap_rush_registered():
    sections = _parse_gap_sections()
    missing = [
        cid for cid in sections.get("rush", [])
        if not _in_board(cid, BOARD_RUSH) and not _in_board(cid, BOARD_BATTLECRY)
    ]
    assert not missing, f"突袭未注册: {missing[:10]}... ({len(missing)} total)"


def test_gap_weapons_registered():
    sections = _parse_gap_sections()
    missing = [cid for cid in sections.get("weapon", []) if not _in_board(cid, BOARD_WEAPON)]
    assert not missing, f"武器未注册: {missing}"


def test_gap_combo_registered():
    sections = _parse_gap_sections()
    missing = [
        cid for cid in sections.get("combo", [])
        if not _in_board(cid, BOARD_COMBO) and not _in_board(cid, BOARD_RUSH)
    ]
    # TOY_516 等可能仅在 rush
    assert len(missing) <= 1, f"连击未注册: {missing}"


def test_gap_deathrattle_registered():
    sections = _parse_gap_sections()
    missing = [cid for cid in sections.get("deathrattle", []) if cid not in DEATHRATTLE_BY_CARD]
    assert not missing, f"亡语未注册: {missing}"


def test_gap_end_turn_registered():
    sections = _parse_gap_sections()
    missing = [cid for cid in sections.get("end_turn", []) if cid not in END_TURN_BY_CARD]
    assert not missing, f"回合结束未注册: {missing}"


if __name__ == "__main__":
    test_gap_spells_registered()
    test_gap_battlecries_registered()
    test_gap_rush_registered()
    test_gap_weapons_registered()
    test_gap_combo_registered()
    test_gap_deathrattle_registered()
    test_gap_end_turn_registered()
    print("OK")
