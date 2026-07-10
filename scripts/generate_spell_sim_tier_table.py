#!/usr/bin/env python3
"""生成法术模拟分层对照表（清场 / 清场+打脸 / 直伤 / 功能）。"""
from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for mod in (
    "hdt_python.spell_p0_direct",
    "hdt_python.spell_p0_aoe",
    "hdt_python.spell_p0_remove",
    "hdt_python.spell_p0_buff",
    "hdt_python.spell_p0_other",
    "hdt_python.spell_p0_minion",
    "hdt_python.spell_p0_dream",
    "hdt_python.spell_p1_direct",
    "hdt_python.spell_p1_aoe",
    "hdt_python.spell_p1_buff",
    "hdt_python.spell_p1_minion",
    "hdt_python.spell_p1_other",
    "hdt_python.spell_p2_direct",
    "hdt_python.battlecry_p0",
    "hdt_python.eudora_loot",
):
    try:
        importlib.import_module(mod)
    except ModuleNotFoundError:
        pass

from hdt_python.spell_board import (  # noqa: E402
    BOARD_CLEAR_SPELLS,
    SPELL_SIM_TIER_LABELS,
    spell_sim_tier,
)


def _load_card_text() -> dict[str, str]:
    path = ROOT / "json" / "cards_zhCN.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for c in data:
        cid = c.get("id")
        if cid:
            out[cid] = (c.get("text") or "").replace("\n", " ").strip()
    return out


def _effect(defn, card_text: dict[str, str]) -> str:
    doc = (inspect.getdoc(defn.apply) or "").strip()
    if doc:
        first = doc.split("\n")[0].strip()
        if first:
            return first.replace("|", "/")
    for cid in defn.card_ids:
        t = card_text.get(cid, "")
        if t:
            return t.replace("|", "/")
    return "（见卡牌描述）"


def main() -> None:
    card_text = _load_card_text()
    seen: set[str] = set()
    rows: list[tuple[str, str, str, str, str]] = []

    for _cid, defn in sorted(
        BOARD_CLEAR_SPELLS.items(),
        key=lambda x: (spell_sim_tier(x[1]).value, x[1].name, x[0]),
    ):
        if defn.name in seen:
            continue
        seen.add(defn.name)
        tier = SPELL_SIM_TIER_LABELS[spell_sim_tier(defn)]
        rows.append((
            tier,
            defn.name,
            defn.card_ids[0],
            "是" if defn.uses_random else "否",
            _effect(defn, card_text),
        ))

    out = ROOT / "SPELL_SIM_TIER_TABLE.md"
    lines = [
        "# 法术模拟分层对照表",
        "",
        "用于 combo 搜索出牌优先级与无嘲讽直伤剥离。",
        "",
        "| 分类 | 名称 | card_id | 随机 | 法术效果（模拟说明） |",
        "|------|------|---------|------|----------------------|",
    ]
    for tier, name, cid, rnd, effect in rows:
        lines.append(f"| {tier} | {name} | {cid} | {rnd} | {effect} |")
    lines.append("")
    lines.append(f"共 **{len(rows)}** 张（按中文名去重）。")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
