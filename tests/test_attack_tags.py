#!/usr/bin/env python3
"""测试 BUFF 后攻击力读取（ATK / 479 / 4472）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.board_damage import effective_attack_from_tags, _std_attack
from hdt_python.power_parser import Entity


def test_atk_over_stale_479():
    """发现等场景：479 滞后时仍以 ATK 为准。"""
    tags = {"ATK": 6, "4472": 6, "479": 1}
    assert effective_attack_from_tags(tags) == 6


def test_spawn_before_479_set():
    """479 尚未写入时，回退 ATK。"""
    tags = {"ATK": 5, "4472": 0}
    assert effective_attack_from_tags(tags) == 5


def test_zero_attack_deathrattle_stale_4472():
    """0 攻随从（亡语召唤 5/5）：ATK=0 时不应被 4472=5 覆盖。"""
    tags = {"ATK": 0, "4472": 5, "479": 0, "TAG_SCRIPT_DATA_NUM_1": 5}
    assert effective_attack_from_tags(tags) == 0


def test_zero_attack_from_479_only():
    """无 ATK 时仍可用 479=0 表示 0 攻。"""
    tags = {"479": 0, "4472": 5}
    assert effective_attack_from_tags(tags) == 0


def test_fallback_to_479_when_atk_missing():
    """仅写 479 的旧测试/日志片段仍能读到攻。"""
    tags = {"479": 8, "4472": 1}
    assert effective_attack_from_tags(tags) == 8


def test_buffed_weapon_479_over_stale_atk():
    """BUFF 武器：479=6 已更新但 ATK 仍为牌面 4 时应读 6。"""
    tags = {"ATK": 4, "479": 6, "4472": 4}
    assert effective_attack_from_tags(tags) == 6


def test_entity_sync_after_tag_change():
    e = Entity(entity_id=1, cardtype="MINION")
    e.tags = {"ATK": 6, "4472": 6, "479": 6}
    e.sync_attack_from_tags()
    assert e.atk == 6
    e.tags["479"] = 1
    e.sync_attack_from_tags()
    assert e.atk == 6
    assert _std_attack(e) == 6


if __name__ == "__main__":
    test_atk_over_stale_479()
    test_spawn_before_479_set()
    test_zero_attack_deathrattle_stale_4472()
    test_zero_attack_from_479_only()
    test_fallback_to_479_when_atk_missing()
    test_buffed_weapon_479_over_stale_atk()
    test_entity_sync_after_tag_change()
    print("all passed")
