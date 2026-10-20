#!/usr/bin/env python3
"""漏斩审计：回合初 / 打一半才亮。"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_miss_audit import (
    LethalMissAuditor,
    _judge_miss,
    miss_reports_dir,
)


def test_note_overlay_latches_prompt():
    aud = LethalMissAuditor()
    aud.note_overlay(
        prompt_lethal=False, show_lethal=False, has_lethal=False,
        face=0, opp_hp=10,
    )
    assert aud._had_prompt is False
    aud.note_overlay(
        prompt_lethal=True, show_lethal=True, has_lethal=True,
        face=10, opp_hp=4, note="x",
    )
    assert aud._had_prompt is True
    assert aud._prompted_before_action is True
    aud.reset_game()
    assert aud._had_prompt is False
    print("OK latch")


def test_late_prompt_not_counted_as_early():
    aud = LethalMissAuditor()
    aud.on_local_turn_start()
    aud.note_overlay(
        prompt_lethal=False, show_lethal=False, has_lethal=False,
        face=5, opp_hp=4,
    )
    aud.on_local_action()
    aud.note_overlay(
        prompt_lethal=True, show_lethal=True, has_lethal=True,
        face=5, opp_hp=4,
    )
    assert aud._had_prompt is True
    assert aud._prompted_before_action is False
    print("OK late prompt")


def test_judge_turn_start_late_prompt():
    ts = SimpleNamespace(overlay=5, lethal=True, opp_hp=4, prob=1.0, note="嚼嚼怪")
    pk = SimpleNamespace(overlay=5, lethal=True, opp_hp=4, prob=1.0, note="")
    rep = SimpleNamespace(
        kill_turn_start=ts, pre_kill=pk, end_type="英雄击杀", note="",
    )
    v, _ = _judge_miss(rep, runtime_prompted=True, prompted_before_action=False)
    assert v and "打一半才亮" in v, v
    v2, _ = _judge_miss(rep, runtime_prompted=True, prompted_before_action=True)
    assert v2 is None
    print("OK judge late")


def test_judge_face_enough_not_lethal():
    ts = SimpleNamespace(overlay=5, lethal=False, opp_hp=4, prob=0.0, note="x")
    rep = SimpleNamespace(
        kill_turn_start=ts, pre_kill=None, end_type="英雄击杀", note="",
    )
    v, _ = _judge_miss(rep, runtime_prompted=False, prompted_before_action=False)
    assert v and "场攻够" in v, v
    print("OK judge suppress")


def test_miss_dir_writable():
    d = miss_reports_dir()
    assert d.is_dir()
    p = d / "_write_test.json"
    p.write_text(json.dumps({"ok": True}), encoding="utf-8")
    assert p.is_file()
    p.unlink()
    print("OK miss dir", d)


if __name__ == "__main__":
    test_note_overlay_latches_prompt()
    test_late_prompt_not_counted_as_early()
    test_judge_turn_start_late_prompt()
    test_judge_face_enough_not_lethal()
    test_miss_dir_writable()
    print("OK lethal_miss_audit")
