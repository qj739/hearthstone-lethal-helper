#!/usr/bin/env python3
"""扫描 lethal_misses/ 待修复报告，打印诊断；供 Agent /loop 调用。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hdt_python.lethal_miss_audit import miss_reports_dir


def main() -> int:
    d = miss_reports_dir()
    pending = sorted(d.glob("miss_*.json"))
    todo = []
    for p in pending:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"BAD {p.name}: {e}")
            continue
        if data.get("status") != "pending":
            continue
        todo.append((p, data))

    if not todo:
        print(f"[miss] 无 pending 报告 ({d})")
        return 0

    print(f"[miss] {len(todo)} 条待修复 @ {d}")
    for p, data in todo:
        print("-" * 60)
        print(f"file: {p.name}")
        print(f"verdict: {data.get('verdict')}")
        print(f"diagnosis: {data.get('diagnosis')}")
        print(f"game_log: {data.get('game_log')}")
        print(f"pre_kill: {data.get('pre_kill')}")
        print(f"turn_start: {data.get('kill_turn_start')}")
        print(
            "Agent 任务: 用 game_log 回放到斩杀前 STOP，"
            "对比 has_lethal=False 的原因，修代码 + 补 tests，"
            f"再把 {p.name} 的 status 改为 fixed。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
