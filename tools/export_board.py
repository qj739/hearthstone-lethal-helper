#!/usr/bin/env python3
"""
纯 Python 导出场面 JSON（读 Power.log，与 HDT 同源，无需编译 C# 插件）。

用法:
  python tools/export_board.py
  python tools/export_board.py -o board_state.json --interval 0.5

输出字段与 hdt_plugin 的 hdt_state.json 结构对齐，便于对比或其它脚本读取。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.log_watcher import LogWatcherManager, find_power_log_path, install_log_config
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.state_snapshot import export_game_state


def _default_output_path() -> Path:
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        return Path(local) / "HSCompare" / "power_log_state.json"
    return Path(__file__).resolve().parent.parent / "power_log_state.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="从 Power.log 导出场面 JSON")
    parser.add_argument("-o", "--output", help="输出 JSON 路径")
    parser.add_argument("--interval", type=float, default=0.5, help="写入间隔（秒）")
    parser.add_argument("--pretty", action="store_true", help="缩进格式化 JSON")
    args = parser.parse_args()

    install_log_config()

    out_path = Path(args.output) if args.output else _default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

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
    print("Power.log 场面导出")
    print(f"输出: {out_path}")
    print("按 Ctrl+C 停止")
    print("=" * 60)

    manager.start()
    last_write = 0.0

    try:
        while True:
            now = time.time()
            if now - last_write < args.interval:
                time.sleep(0.05)
                continue

            power_parser.reconcile_local_player()
            snapshot = export_game_state(gs, lethal)
            snapshot["source"] = "power_log"
            snapshot["timestamp"] = datetime.now(timezone.utc).astimezone().isoformat()

            indent = 2 if args.pretty else None
            tmp = out_path.with_suffix(out_path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=indent)
            tmp.replace(out_path)

            last_write = now
            if gs.in_game:
                pb = snapshot.get("player") or {}
                ob = snapshot.get("opponent") or {}
                print(
                    f"\r[对局中] 场攻={pb.get('boardFaceDamage')} "
                    f"我方{len(pb.get('board') or [])}随从 "
                    f"对手{len(ob.get('board') or [])}随从",
                    end="",
                    flush=True,
                )
            else:
                print("\r[等待对局…]          ", end="", flush=True)

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n已停止")
        manager.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
