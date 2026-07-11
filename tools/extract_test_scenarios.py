#!/usr/bin/env python3
"""从 tests/ 提取每个用例的场面/手牌/血量，生成审核用 Markdown。"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CARDS_PATH = ROOT / "json" / "cards.json"
CARDS_ZH_PATH = ROOT / "json" / "cards_zhCN.json"


@dataclass
class MinionRow:
    side: str  # 我方 / 对手
    atk: int
    hp: int
    card_id: str = ""
    name: str = ""
    extra: str = ""


@dataclass
class HandRow:
    card_id: str
    cost: int = 0
    name: str = ""


@dataclass
class Scenario:
    file: str
    func: str
    doc: str
    local_pid: Optional[int] = None
    opp_pid: Optional[int] = None
    active_pid: Optional[int] = None
    my_hp: str = "30+0"
    opp_hp: str = "30+0"
    my_mana: str = ""
    my_board: list[MinionRow] = field(default_factory=list)
    opp_board: list[MinionRow] = field(default_factory=list)
    my_hand: list[HandRow] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    is_replay: bool = False
    is_registry: bool = False
    is_parser_only: bool = False


def _load_names() -> dict[str, str]:
    names: dict[str, str] = {}
    if CARDS_ZH_PATH.exists():
        try:
            data = json.loads(CARDS_ZH_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for c in data:
                    cid = c.get("id")
                    if cid:
                        names[cid] = c.get("name", cid)
        except Exception:
            pass
    if CARDS_PATH.exists():
        try:
            data = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for c in data:
                    cid = c.get("id")
                    if cid and cid not in names:
                        names[cid] = c.get("name", cid)
        except Exception:
            pass
    return names


CARD_NAMES = _load_names()


def _card_label(cid: str) -> str:
    if not cid:
        return "?"
    nm = CARD_NAMES.get(cid, cid)
    if nm == cid:
        return cid
    return f"{nm}·{cid}"


def _parse_minion_call(text: str, local: int, opp: int) -> Optional[MinionRow]:
    # _minion(gs, eid, pid, atk, hp, ...)
    m = re.search(
        r"_minion\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
        text,
    )
    if m:
        pid, atk, hp = int(m.group(1)), int(m.group(2)), int(m.group(3))
        side = "我方" if pid == local else ("对手" if pid == opp else f"P{pid}")
        cid_m = re.search(r"card_id\s*=\s*[\"']([^\"']+)[\"']", text[m.start() : m.end() + 80])
        cid = cid_m.group(1) if cid_m else ""
        extra_parts = []
        if "taunt" in text.lower() or "TAUNT" in text:
            extra_parts.append("嘲")
        if "dormant" in text.lower() or "DORMANT" in text:
            extra_parts.append("休眠")
        if "rush" in text.lower() or "RUSH" in text:
            extra_parts.append("突袭")
        if "charge" in text.lower() or "CHARGE" in text:
            extra_parts.append("冲锋")
        return MinionRow(side, atk, hp, cid, _card_label(cid) if cid else "", "+".join(extra_parts))

    # gs.get_entity + atk/health manual
    return None


def _extract_from_source(src: str, func_name: str, file_name: str) -> Scenario:
    doc = ast.get_docstring(ast.parse(src).body[0]) if False else ""
    try:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                doc = ast.get_docstring(node) or ""
                body_src = ast.get_source_segment(src, node) or ""
                break
        else:
            body_src = src
    except SyntaxError:
        body_src = src
        doc = ""

    sc = Scenario(file=file_name, func=func_name, doc=doc.split("\n")[0].strip())

    low = body_src.lower()
    if any(k in low for k in ("parse_to_line", "power.log", "read_text", "splitlines", "replay", "from_log")):
        sc.is_replay = True
        sc.notes.append("依赖 Power.log 回放")
    if "registered" in func_name or "assert get_board_spell_def" in body_src:
        sc.is_registry = True
        sc.notes.append("注册/存在性检查")
    if func_name.startswith("test_import") or "assert " in body_src and "_minion" not in body_src and "_hero" not in body_src:
        if not sc.is_replay and len(body_src) < 400:
            sc.is_parser_only = True

    m = re.search(r"gs\.local_player_id\s*=\s*(\d+)", body_src)
    if m:
        sc.local_pid = int(m.group(1))
    m = re.search(r"gs\.opponent_player_id\s*=\s*(\d+)", body_src)
    if m:
        sc.opp_pid = int(m.group(1))
    m = re.search(r"gs\.active_player_id\s*=\s*(\d+)", body_src)
    if m:
        sc.active_pid = int(m.group(1))

    local = sc.local_pid or 1
    opp = sc.opp_pid or 2

    hero_hp: dict[int, tuple[int, int]] = {local: (30, 0), opp: (30, 0)}
    hero_mana: dict[int, tuple[int, int]] = {}

    for hm in re.finditer(
        r"_hero\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)([^)]*)\)",
        body_src,
    ):
        pid = int(hm.group(1))
        tail = hm.group(2)
        hp, armor = 30, 0
        dmg_m = re.search(r"dmg\s*=\s*(\d+)", tail)
        if dmg_m:
            hp = max(0, 30 - int(dmg_m.group(1)))
        hero_hp[pid] = (hp, armor)
        mana_m = re.search(r"mana\s*=\s*(\d+)", tail)
        used_m = re.search(r"used\s*=\s*(\d+)", tail)
        if mana_m:
            used = int(used_m.group(1)) if used_m else 0
            hero_mana[pid] = (int(mana_m.group(1)), used)

    for om in re.finditer(r"opp\.health\s*=\s*(\d+)", body_src):
        hero_hp[opp] = (int(om.group(1)), hero_hp.get(opp, (30, 0))[1])
    for om in re.finditer(r"opp\.damage\s*=\s*(\d+)", body_src):
        d = int(om.group(1))
        prev = hero_hp.get(opp, (30, 0))[0]
        hero_hp[opp] = (max(0, prev - d), hero_hp.get(opp, (30, 0))[1])

    my_hp_val, my_armor = hero_hp.get(local, (30, 0))
    opp_hp_val, opp_armor = hero_hp.get(opp, (30, 0))
    sc.my_hp = f"{my_hp_val}+{my_armor}" if my_armor else str(my_hp_val)
    sc.opp_hp = f"{opp_hp_val}+{opp_armor}" if opp_armor else str(opp_hp_val)

    if local in hero_mana:
        mana, used = hero_mana[local]
        sc.my_mana = f"{mana - used}/{mana}"

    # minions - all _minion calls
    for m in re.finditer(
        r"_minion\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)([^)]*)\)",
        body_src,
    ):
        pid, atk, hp = int(m.group(1)), int(m.group(2)), int(m.group(3))
        tail = m.group(4)
        cid_m = re.search(r"card_id\s*=\s*[\"']([^\"']+)[\"']", tail)
        cid = cid_m.group(1) if cid_m else ""
        extra = []
        if re.search(r"taunt\s*=\s*True|TAUNT[\"']?\s*[,:\]]", tail + body_src[m.start() : m.end() + 40]):
            extra.append("嘲")
        if "dormant=True" in tail:
            extra.append("休眠")
        row = MinionRow(
            "我方" if pid == local else ("对手" if pid == opp else f"P{pid}"),
            atk,
            hp,
            cid,
            _card_label(cid) if cid else f"{atk}/{hp}",
            "+".join(extra),
        )
        if row.side == "我方":
            sc.my_board.append(row)
        else:
            sc.opp_board.append(row)

    # manual minion setup (taunt = gs.get_entity)
    if "taunt.cardtype" in body_src or "taunt.atk" in body_src:
        atk_m = re.search(r"taunt\.atk\s*=\s*(\d+)", body_src)
        hp_m = re.search(r"taunt\.health\s*=\s*(\d+)", body_src)
        cid_m = re.search(r"taunt\.card_id\s*=\s*[\"']([^\"']+)[\"']", body_src)
        if atk_m and hp_m:
            sc.opp_board.append(
                MinionRow(
                    "对手",
                    int(atk_m.group(1)),
                    int(hp_m.group(1)),
                    cid_m.group(1) if cid_m else "",
                    _card_label(cid_m.group(1)) if cid_m else "",
                    "嘲",
                )
            )

    # hand spells
    for m in re.finditer(
        r"_hand_spell\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)\s*,\s*[\"']([^\"']+)[\"']\s*,\s*(\d+)",
        body_src,
    ):
        pid, cid, cost = int(m.group(1)), m.group(2), int(m.group(3))
        if pid == local:
            sc.my_hand.append(HandRow(cid, cost, f"{_card_label(cid)}({cost}费)"))

    # hand minions / weapons
    for m in re.finditer(
        r"_hand_minion\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)([^)]*)\)",
        body_src,
    ):
        pid, atk, hp, cost = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        tail = m.group(5)
        cid_m = re.search(r"card_id\s*=\s*[\"']([^\"']+)[\"']", tail)
        cid = cid_m.group(1) if cid_m else "随从"
        extra = []
        if "charge=True" in tail:
            extra.append("冲锋")
        if "rush=True" in tail:
            extra.append("突袭")
        label = f"{_card_label(cid)} {atk}/{hp}({cost}费)"
        if extra:
            label += f"[{'+'.join(extra)}]"
        if pid == local:
            sc.my_hand.append(HandRow(cid, cost, label))

    for m in re.finditer(
        r"_hand_weapon\s*\(\s*gs\s*,\s*\d+\s*,\s*(\d+)\s*,\s*[\"']([^\"']+)[\"']\s*,\s*(\d+)",
        body_src,
    ):
        pid, cid, cost = int(m.group(1)), m.group(2), int(m.group(3))
        if pid == local:
            sc.my_hand.append(HandRow(cid, cost, f"{_card_label(cid)}({cost}费)武器"))

    # expectations from asserts / doc
    exp_m = re.search(r"assert\s+face\s*>=\s*(\d+)", body_src)
    if exp_m:
        sc.notes.append(f"期望场攻≥{exp_m.group(1)}")
    if "assert has" in body_src or "assert lethal" in body_src:
        if "not has" in body_src or "is False" in body_src:
            sc.notes.append("期望：无斩杀")
        else:
            sc.notes.append("期望：有斩杀")
    if sc.active_pid and sc.local_pid:
        if sc.active_pid == sc.local_pid:
            sc.notes.append("我方回合")
        elif sc.active_pid == sc.opp_pid:
            sc.notes.append("对方回合(下回合预览)")

    return sc


def _format_minion(r: MinionRow) -> str:
    stats = f"{r.atk}/{r.hp}"
    if r.card_id and r.name:
        base = r.name
        if stats not in base:
            base = f"{base} {stats}"
    elif r.name:
        base = f"{r.name} {stats}" if stats not in r.name else r.name
    else:
        base = stats
    if r.extra:
        base += f" [{r.extra}]"
    return base


def _format_board(rows: list[MinionRow]) -> str:
    if not rows:
        return "空"
    return " · ".join(_format_minion(r) for r in rows)


def _format_hand(rows: list[HandRow]) -> str:
    if not rows:
        return "（无/未构造）"
    return " · ".join(h.name or f"{h.card_id}({h.cost}费)" for h in rows)


def collect_scenarios() -> list[Scenario]:
    out: list[Scenario] = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        mod_doc = ast.get_docstring(tree) or ""
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            body_src = ast.get_source_segment(src, node) or ""
            sc = _extract_from_source(body_src, node.name, path.name)
            if not sc.doc:
                sc.doc = mod_doc.split("\n")[0].strip()
            out.append(sc)
    return out


def _category(file: str) -> str:
    if "lethal" in file or "taunt" in file or "overlay" in file:
        return "斩杀/Overlay"
    if "spell_board" in file or "spell" in file:
        return "法术模拟"
    if "end_turn" in file:
        return "回合结束"
    if "deathrattle" in file:
        return "亡语"
    if "potion" in file or "rush" in file or "weapon" in file:
        return "场面机制"
    if "player" in file or "attack" in file or "power_log" in file or "hdt" in file:
        return "解析/身份"
    if "arena" in file or "registered" in file:
        return "注册门禁"
    return "其他"


def render_markdown(scenarios: list[Scenario]) -> str:
    lines = [
        "# 测试用例场面明细（审核版）",
        "",
        "> 从 `tests/test_*.py` 自动提取：对手血量、双方场面、手牌。",
        "> 回放用例、纯注册用例会标注；复杂构造可能不完整，以源码为准。",
        "",
        f"**合计**：{len(scenarios)} 个用例",
        "",
        "---",
        "",
    ]

    by_file: dict[str, list[Scenario]] = {}
    for sc in scenarios:
        by_file.setdefault(sc.file, []).append(sc)

    cat_order = [
        "斩杀/Overlay",
        "法术模拟",
        "回合结束",
        "亡语",
        "场面机制",
        "解析/身份",
        "注册门禁",
        "其他",
    ]
    files_by_cat: dict[str, list[str]] = {c: [] for c in cat_order}
    for f in by_file:
        files_by_cat.setdefault(_category(f), []).append(f)

    idx = 0
    for cat in cat_order:
        files = sorted(files_by_cat.get(cat, []))
        if not files:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for fname in files:
            lines.append(f"### `{fname}`")
            lines.append("")
            for sc in by_file[fname]:
                idx += 1
                lines.append(f"#### {idx}. `{sc.func}`")
                if sc.doc:
                    lines.append(f"- **说明**：{sc.doc}")
                if sc.is_replay:
                    lines.append("- **类型**：回放 log（场面以日志为准，下表可能为空）")
                elif sc.is_registry:
                    lines.append("- **类型**：卡牌注册/存在性（无完整场面）")
                elif sc.is_parser_only:
                    lines.append("- **类型**：单元/解析（无场面构造）")
                lines.append("")
                lines.append("| 项目 | 内容 |")
                lines.append("|------|------|")
                lines.append(f"| 对手血量 | {sc.opp_hp} |")
                lines.append(f"| 我方血量 | {sc.my_hp} |")
                if sc.my_mana:
                    lines.append(f"| 我方法力 | {sc.my_mana} |")
                lines.append(f"| 我方场面 | {_format_board(sc.my_board)} |")
                lines.append(f"| 对手场面 | {_format_board(sc.opp_board)} |")
                lines.append(f"| 我方手牌 | {_format_hand(sc.my_hand)} |")
                if sc.notes:
                    lines.append(f"| 备注 | {'；'.join(sc.notes)} |")
                lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    scenarios = collect_scenarios()
    md = render_markdown(scenarios)
    out_path = ROOT / "docs" / "TEST_CASES_SCENARIOS.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {len(scenarios)} scenarios -> {out_path}")


if __name__ == "__main__":
    main()
