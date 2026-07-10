# hdt_compare.py - 对比 Power.log 解析结果与 HDT 导出 JSON

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def default_hdt_state_paths() -> List[Path]:
    """HDT 插件默认写入路径 + 项目目录兜底。"""
    paths: List[Path] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        paths.append(Path(local) / "HSCompare" / "hdt_state.json")
    project = Path(__file__).resolve().parent.parent
    paths.append(project / "hdt_state.json")
    return paths


def find_hdt_state_file(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    for p in default_hdt_state_paths():
        if p.is_file():
            return p
    return None


def load_hdt_state(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    p = path or find_hdt_state_file()
    if not p:
        return None
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _minion_key(m: Dict[str, Any]) -> Tuple:
    return (
        m.get("cardId") or "",
        int(m.get("attack", 0) or 0),
        int(m.get("health", 0) or 0),
        int(m.get("zonePos", 0) or 0),
    )


def _minion_attack_key(m: Dict[str, Any]) -> Tuple:
    return (
        m.get("cardId") or "",
        int(m.get("attack", 0) or 0),
        bool(m.get("canAttackHero", m.get("canAttack", False))),
    )


def _board_counter(board: List[Dict[str, Any]]) -> Counter:
    return Counter(_minion_key(m) for m in (board or []))


def _format_minion(m: Dict[str, Any]) -> str:
    cid = m.get("cardId") or "?"
    atk = m.get("attack", 0)
    hp = m.get("health", 0)
    pos = m.get("zonePos", 0)
    flags = []
    if m.get("canAttackHero"):
        flags.append("可攻")
    elif m.get("canAttack"):
        flags.append("可攻随从")
    if m.get("taunt"):
        flags.append("嘲讽")
    if m.get("exhausted"):
        flags.append("疲劳")
    extra = f" [{','.join(flags)}]" if flags else ""
    return f"{cid} {atk}/{hp} @pos{pos}{extra}"


def compare_states(ours: Dict[str, Any], hdt: Dict[str, Any]) -> List[str]:
    """返回差异描述列表；空列表表示关键字段一致。"""
    issues: List[str] = []

    if not hdt:
        issues.append("未读到 HDT 状态文件（请安装并启用 CompareExporter 插件）")
        return issues

    if bool(ours.get("inGame")) != bool(hdt.get("inGame")):
        issues.append(f"对局状态: 我们={ours.get('inGame')} HDT={hdt.get('inGame')}")

    op = ours.get("player") or {}
    oo = ours.get("opponent") or {}
    hp = hdt.get("player") or {}
    ho = hdt.get("opponent") or {}

    for label, o_side, h_side in (
        ("我方英雄", op.get("hero"), hp.get("hero")),
        ("对手英雄", oo.get("hero"), ho.get("hero")),
    ):
        if not o_side or not h_side:
            continue
        oh, oa = o_side.get("health"), o_side.get("armor", 0)
        hh, ha = h_side.get("health"), h_side.get("armor", 0)
        if oh != hh or oa != ha:
            issues.append(f"{label}: 我们 {oh}+{oa} vs HDT {hh}+{ha}")

    if op.get("mana") != hp.get("mana"):
        issues.append(f"法力: 我们 {op.get('mana')} vs HDT {hp.get('mana')}")

    if op.get("handCount") != hp.get("handCount"):
        issues.append(f"我方手牌数: 我们 {op.get('handCount')} vs HDT {hp.get('handCount')}")

    if oo.get("handCount") != ho.get("handCount"):
        issues.append(f"对手手牌数: 我们 {oo.get('handCount')} vs HDT {ho.get('handCount')}")

    our_face = op.get("boardFaceDamage")
    hdt_face = hp.get("boardFaceDamage")
    if our_face is not None and hdt_face is not None and our_face != hdt_face:
        issues.append(
            f"纯场攻(随从+武器): 我们 {our_face} vs HDT {hdt_face} "
            f"(随 {op.get('boardMinionAttack')} + 武 {op.get('boardWeaponAttack')})"
        )

    for label, ob, hb in (
        ("我方场面", op.get("board"), hp.get("board")),
        ("对手场面", oo.get("board"), ho.get("board")),
    ):
        ob = ob or []
        hb = hb or []
        if len(ob) != len(hb):
            issues.append(f"{label}数量: 我们 {len(ob)} vs HDT {len(hb)}")

        oc = _board_counter(ob)
        hc = _board_counter(hb)
        only_ours = list((oc - hc).elements())
        only_hdt = list((hc - oc).elements())
        if only_ours:
            issues.append(f"{label} 我们多: " + ", ".join(
                _format_minion({"cardId": k[0], "attack": k[1], "health": k[2], "zonePos": k[3]})
                for k in only_ours[:5]
            ))
        if only_hdt:
            issues.append(f"{label} HDT多: " + ", ".join(
                _format_minion({"cardId": k[0], "attack": k[1], "health": k[2], "zonePos": k[3]})
                for k in only_hdt[:5]
            ))

        # 同名同属性随从，对比能否攻击
        hdt_by_id = {m.get("entityId"): m for m in hb if m.get("entityId")}
        for m in ob:
            eid = m.get("entityId")
            if eid and eid in hdt_by_id:
                hm = hdt_by_id[eid]
                if bool(m.get("canAttackHero")) != bool(hm.get("canAttackHero", hm.get("canAttack"))):
                    issues.append(
                        f"可攻不一致 {m.get('cardId')} entity={eid}: "
                        f"我们={'是' if m.get('canAttackHero') else '否'} "
                        f"HDT={'是' if hm.get('canAttackHero', hm.get('canAttack')) else '否'}"
                    )

    return issues


def format_compare_report(issues: List[str], ours: Dict[str, Any], hdt: Optional[Dict[str, Any]]) -> str:
    if not issues:
        op = ours.get("player") or {}
        return (
            f"✓ 与 HDT 一致 | 场攻 {op.get('boardFaceDamage')} | "
            f"我方 {len(op.get('board') or [])} 随从 | "
            f"对手 {len((ours.get('opponent') or {}).get('board') or [])} 随从"
        )
    lines = ["✗ 与 HDT 存在差异:"]
    lines.extend(f"  - {x}" for x in issues)
    if hdt:
        lines.append(f"  (HDT 文件时间戳: {hdt.get('timestamp', '?')})")
    return "\n".join(lines)
