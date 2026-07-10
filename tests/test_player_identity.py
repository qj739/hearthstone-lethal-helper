#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.player_identity import (
    battle_tag_matches,
    is_real_battle_tag,
    name_matches_env_override,
    optional_env_player_names,
)


def test_is_real_battle_tag():
    assert is_real_battle_tag("能干的英雄#510408")
    assert not is_real_battle_tag("UNKNOWN HUMAN PLAYER")
    assert not is_real_battle_tag("无井号")


def test_battle_tag_prefix_match():
    assert battle_tag_matches("能干的英雄#510408", "能干的英雄")
    assert battle_tag_matches("鸡哥在线#5240", "鸡哥在线#9999")


def test_env_override(monkeypatch):
    monkeypatch.setenv("HS_PLAYER_NAMES", "鸡哥在线#5240,能干的英雄")
    monkeypatch.delenv("HS_PLAYER_NAME", raising=False)
    assert name_matches_env_override("能干的英雄#510408")
    assert len(optional_env_player_names()) == 2


if __name__ == "__main__":
    test_is_real_battle_tag()
    test_battle_tag_prefix_match()
    print("OK")
