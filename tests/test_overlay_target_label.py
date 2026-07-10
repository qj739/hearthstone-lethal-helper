#!/usr/bin/env python3
"""斩杀步骤目标文案：被击杀的非嘲讽随从不应显示「嘲讽」。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.overlay_combo_format import _infer_target_label, _snapshot_enemy


def test_killed_non_taunt_label_has_no_taunt_tag():
    before_units = [
        {
            "kind": "minion",
            "entity_id": 99,
            "atk": 1,
            "health": 1,
            "shield": False,
            "taunt": False,
        },
    ]
    before = _snapshot_enemy(before_units)
    after = [
        {
            "kind": "minion",
            "entity_id": 99,
            "atk": 1,
            "health": 0,
            "shield": False,
            "taunt": False,
        },
    ]
    label = _infer_target_label(before, after, uses_random=False, direct_face=0)
    assert label == "1/1", f"expected plain 1/1, got {label!r}"
    assert "嘲讽" not in label


def test_killed_taunt_label_keeps_taunt_tag():
    before_units = [
        {
            "kind": "minion",
            "entity_id": 1,
            "atk": 2,
            "health": 5,
            "shield": False,
            "taunt": True,
        },
    ]
    before = _snapshot_enemy(before_units)
    after = [{"kind": "minion", "entity_id": 1, "atk": 2, "health": 0, "taunt": True}]
    label = _infer_target_label(before, after, uses_random=False, direct_face=0)
    assert label == "2/5·嘲讽"


if __name__ == "__main__":
    test_killed_non_taunt_label_has_no_taunt_tag()
    test_killed_taunt_label_keeps_taunt_tag()
    print("ok")
