#!/usr/bin/env python3
"""重新生成 concede 报告（UTF-8），避免 Windows 重定向乱码。

用法:
  python tools/regenerate_concede_reports.py
  python tools/regenerate_concede_reports.py --split-root Logs/split_games
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "_list_concede_no_lethal.py"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--split-root",
        action="append",
        default=[],
        help="split_games 目录，可多次指定",
    )
    ap.add_argument(
        "--out-full",
        type=Path,
        default=ROOT / "concede_no_lethal_full.txt",
    )
    args = ap.parse_args()

    cmd = [sys.executable, str(SCRIPT)]
    for p in args.split_root:
        cmd.extend(["--split-root", p])

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        return proc.returncode
    text = proc.stdout
    args.out_full.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out_full} ({len(text)} chars, UTF-8)")
    if not text.strip():
        print("警告: 输出为空。请确认 Logs/split_games 下有 game_*.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
