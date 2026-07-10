#!/usr/bin/env python3
"""HERO_11bpt 等英雄技能衍生物不应被当成英雄/武器场攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import Entity, PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker


def test_hero_power_token_not_hero():
    ghoul = Entity(entity_id=115, card_id="HERO_11bpt")
    ghoul.cardtype = "MINION"
    ghoul.atk = 1
    ghoul.health = 1
    ghoul.tags = {"ZONE": "PLAY", "CONTROLLER": 1}
    assert not ghoul.is_hero

    power = Entity(entity_id=65, card_id="HERO_11bp")
    power.cardtype = "HERO_POWER"
    assert not power.is_hero

    hero = Entity(entity_id=64, card_id="HERO_11")
    hero.cardtype = "HERO"
    assert hero.is_hero

    alt = Entity(entity_id=66, card_id="HERO_03a")
    alt.cardtype = "HERO"
    assert alt.is_hero


def test_overlay_no_false_weapon_from_ghoul_token():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_10_00_09_22\Power.log"
    )
    if not log.is_file():
        print("skip replay: log missing")
        return

    with open(log, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    end = next(
        i for i, line in enumerate(lines)
        if i > 100 and "00:24:35" in line and "CREATE_GAME" in line
    )
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    p._live_mode = False
    for raw in lines[:end]:
        if raw.strip():
            p.process_line(raw.rstrip("\n\r"))
        pid = gs.local_player_id
        if pid is None:
            continue
        board = gs.get_board(pid)
        if "HERO_11bpt" not in [m.card_id for m in board]:
            continue
        bv = gs.get_overlay_board(pid)
        assert gs.get_weapon(pid) is None
        assert bv.hero_damage == 0, f"expected 0 hero_damage got {bv.hero_damage}"
        assert not (bv.hero and bv.hero.has_weapon)
        # 食尸鬼应计入随从场攻，不应算武器
        assert bv.minion_damage >= 1
        return
    raise AssertionError("did not find HERO_11bpt board state in log")


if __name__ == "__main__":
    test_hero_power_token_not_hero()
    test_overlay_no_false_weapon_from_ghoul_token()
    print("test_hero_token_board: OK")
