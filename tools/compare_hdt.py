#!/usr/bin/env python3
"""
与 Hearthstone Deck Tracker 实时对比场面解析结果。

用法:
  1. 编译并启用 HDT 插件（见 HDT_Plugin_Code.cs / hdt_plugin/README.md）
  2. 同时打开 HDT + 炉石
  3. 本终端: python tools/compare_hdt.py
  4. 另一终端可继续跑 python hdt_tracker.py

差异会打印到控制台，便于逐项修复 power_parser / board_damage。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.log_watcher import LogWatcherManager, find_power_log_path, install_log_config
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.state_snapshot import export_game_state
from hdt_python.hdt_compare import (
    find_hdt_state_file,
    load_hdt_state,
    compare_states,
    format_compare_report,
    default_hdt_state_paths,
)

def main():
    parser = argparse.ArgumentParser(description="对比 Power.log 解析与 HDT 场面")
    parser.add_argument("--hdt-file", help="HDT 导出的 hdt_state.json 路径")
    parser.add_argument("--interval", type=float, default=1.0, help="对比间隔（秒）")
    parser.add_argument("--verbose", action="store_true", help="无差异时也打印 OK")
    args = parser.parse_args()

    install_log_config()

    hdt_path = Path(args.hdt_file) if args.hdt_file else find_hdt_state_file()
    if not hdt_path:
        print("未找到 HDT 状态文件。请先安装 CompareExporter 插件，预期路径:")
        for p in default_hdt_state_paths():
            print(f"  - {p}")
        print("\n仍可仅监控 Power.log，但无法与 HDT 对比。")
    else:
        print(f"HDT 状态文件: {hdt_path}")

    power_log = find_power_log_path()
    if not power_log:
        print("找不到 Power.log（请确认炉石已通过 Battle.net 安装）")
        return 1

    log_dir = os.path.dirname(power_log)
    gs = GameState()
    power_parser = PowerLogParser(power_log, gs)
    lethal = LethalChecker(gs)
    manager = LogWatcherManager(log_dir)
    manager.register_watcher("Power", power_parser)

    print("=" * 60)
    print("HDT 对比模式 — 同时开着 HDT 打一局即可看到差异")
    print("按 Ctrl+C 停止")
    print("=" * 60)

    manager.start()
    last_compare = 0.0
    last_issues: tuple = ()
    last_hdt_mtime = 0.0

    try:
        while True:
            now = time.time()
            if now - last_compare < args.interval:
                time.sleep(0.1)
                continue
            last_compare = now

            power_parser.reconcile_local_player()
            ours = export_game_state(gs, lethal)

            hdt = None
            if hdt_path and hdt_path.is_file():
                mtime = hdt_path.stat().st_mtime
                if mtime != last_hdt_mtime:
                    last_hdt_mtime = mtime
                hdt = load_hdt_state(hdt_path)
            elif args.hdt_file:
                hdt = load_hdt_state(Path(args.hdt_file))

            if not gs.in_game:
                if args.verbose:
                    print("[等待对局…]")
                continue

            if not hdt:
                if args.verbose:
                    print("[对局中] 等待 HDT 插件写入状态…")
                continue

            issues = compare_states(ours, hdt)
            key = tuple(issues)
            if key != last_issues or args.verbose:
                print("\n" + format_compare_report(issues, ours, hdt))
                if issues:
                    op = ours.get("player") or {}
                    print("  我方场面:", ", ".join(
                        f"{m.get('cardId')} {m.get('attack')}/{m.get('health')}"
                        for m in (op.get("board") or [])
                    ) or "(空)")
                    hp = hdt.get("player") or {}
                    print("  HDT场面:", ", ".join(
                        f"{m.get('cardId')} {m.get('attack')}/{m.get('health')}"
                        for m in (hp.get("board") or [])
                    ) or "(空)")
                last_issues = key

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n已停止")
        manager.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
