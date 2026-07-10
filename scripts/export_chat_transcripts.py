#!/usr/bin/env python3
"""Export Cursor agent transcripts to readable Markdown."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

TRANSCRIPT_ROOT = Path(
    r"C:\Users\hp\.cursor\projects\c-Users-hp-Desktop-HS\agent-transcripts"
)
OUT_DIR = Path(__file__).resolve().parents[1] / "exports" / "chat_last_3_days"
DAYS = 3


def extract_text(message_obj: dict) -> str:
    content = message_obj.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = block.get("text", "")
            if text:
                parts.append(text)
    return "\n".join(parts)


def clean_user_text(text: str) -> str:
    text = re.sub(r"</?user_query>", "", text)
    return text.strip()


def parse_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                rows.append({
                    "line": line_no,
                    "role": "parse_error",
                    "text": line[:500],
                })
                continue
            role = obj.get("role", "unknown")
            msg = obj.get("message") or {}
            text = extract_text(msg)
            if role == "user":
                text = clean_user_text(text)
            if not text.strip():
                continue
            rows.append({"line": line_no, "role": role, "text": text})
    return rows


def session_title(path: Path) -> str:
    return path.parent.name if path.parent.name != "agent-transcripts" else path.stem


def export_session(path: Path, out_dir: Path) -> Path:
    rows = parse_jsonl(path)
    sid = session_title(path)
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    out_name = f"{mtime.strftime('%Y%m%d_%H%M')}_{sid}.md"
    out_path = out_dir / out_name

    lines = [
        f"# Cursor 聊天记录导出",
        "",
        f"- **会话 ID**: `{sid}`",
        f"- **源文件**: `{path}`",
        f"- **文件修改时间**: {mtime.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **消息条数**: {len(rows)}",
        "",
        "---",
        "",
    ]

    msg_idx = 0
    for row in rows:
        role = row["role"]
        if role not in ("user", "assistant"):
            continue
        msg_idx += 1
        label = "用户" if role == "user" else "助手"
        lines.append(f"## [{msg_idx}] {label} (jsonl 行 {row['line']})")
        lines.append("")
        lines.append(row["text"])
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    cutoff = datetime.now() - timedelta(days=DAYS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 只导出主会话（不含 subagents 子目录）
    candidates: list[Path] = []
    for path in TRANSCRIPT_ROOT.rglob("*.jsonl"):
        if "subagents" in path.parts:
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime >= cutoff:
            candidates.append(path)

    candidates.sort(key=lambda p: p.stat().st_mtime)

    index_lines = [
        f"# 最近 {DAYS} 天聊天记录导出",
        "",
        f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"筛选: 文件修改时间 >= {cutoff.strftime('%Y-%m-%d %H:%M:%S')}",
        f"目录: `{OUT_DIR}`",
        "",
        "## 会话列表",
        "",
    ]

    exported: list[tuple[Path, Path]] = []
    for path in candidates:
        out = export_session(path, OUT_DIR)
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        size_kb = path.stat().st_size / 1024
        index_lines.append(
            f"- [{out.name}]({out.name}) — 修改 {mtime.strftime('%Y-%m-%d %H:%M')}, "
            f"源 {size_kb:.0f} KB, id `{session_title(path)}`"
        )
        exported.append((path, out))

    index_path = OUT_DIR / "INDEX.md"
    index_lines.extend(["", f"共 {len(exported)} 个主会话。", ""])
    index_path.write_text("\n".join(index_lines), encoding="utf-8")

    print(f"Exported {len(exported)} sessions to {OUT_DIR}")
    for _, out in exported:
        print(f"  - {out.name}")


if __name__ == "__main__":
    main()
