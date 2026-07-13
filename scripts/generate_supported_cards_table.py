#!/usr/bin/env python3
"""导出致死模拟已支持卡牌总表（中英名、费用、描述、模拟说明）。"""
from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CARDS_EN = ROOT / "json" / "cards.json"
CARDS_ZH = ROOT / "json" / "cards_zhCN.json"
OUT_MD = ROOT / "docs" / "SUPPORTED_CARDS.md"

MODULE_LABELS = {
    "spell": "法术",
    "battlecry": "战吼随从",
    "rush": "突袭随从",
    "weapon": "武器",
    "combo": "连击",
    "hero_power": "英雄技能",
    "location": "地标",
    "end_turn_hand": "手牌回合结束",
    "damaged_spell_power": "受伤法强",
    "end_turn": "场面回合结束",
    "deathrattle": "亡语",
    "spell_fast": "法术快速估算",
    "charge_fast": "冲锋快速估算",
}

SECTION_ORDER = [
    "spell",
    "battlecry",
    "rush",
    "weapon",
    "combo",
    "hero_power",
    "location",
    "end_turn_hand",
    "damaged_spell_power",
    "end_turn",
    "deathrattle",
    "spell_fast",
    "charge_fast",
]


def normalize_id(cid: str) -> str:
    return cid[5:] if cid.startswith("CORE_") else cid


def _load_json_cards(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return {
        c["id"]: c
        for c in json.loads(path.read_text(encoding="utf-8"))
        if c.get("id")
    }


def _lookup_card(cid: str, en: dict[str, dict], zh: dict[str, dict]) -> tuple[dict, dict]:
    keys = [cid]
    base = normalize_id(cid)
    if base != cid:
        keys.append(base)
    if not cid.startswith("CORE_"):
        keys.append(f"CORE_{base}")
    for key in keys:
        ce = en.get(key) or {}
        cz = zh.get(key) or {}
        if ce or cz:
            return ce, cz
    return {}, {}


def _md_cell(text: str) -> str:
    return (text or "").replace("\n", " ").replace("|", "/").strip()


def _apply_note(defn: Any) -> str:
    doc = (inspect.getdoc(getattr(defn, "apply", None)) or "").strip()
    if doc:
        return _md_cell(doc.split("\n")[0])
    name = getattr(defn, "name", "") or ""
    return _md_cell(name)


def _stat_line(c: dict) -> str:
    ctype = (c.get("type") or "").upper()
    if ctype == "MINION":
        return f"{c.get('attack', '-')}/{c.get('health', '-')}"
    if ctype == "WEAPON":
        atk = c.get("attack", "-")
        dur = c.get("durability", c.get("health", "-"))
        return f"{atk}/{dur}"
    if ctype == "HERO_POWER":
        return "-"
    return "-"


def _deathrattle_note(defn: Any) -> str:
    parts = [f"亡语:{getattr(defn.kind, 'value', defn.kind)}"]
    if getattr(defn, "amount", 0):
        parts.append(f"数值{defn.amount}")
    if getattr(defn, "summon_atk", 0) or getattr(defn, "summon_health", 0):
        parts.append(f"召唤{defn.summon_atk}/{defn.summon_health}")
    if getattr(defn, "summon_taunt", False):
        parts.append("嘲讽")
    if getattr(defn, "summon_charge", False):
        parts.append("冲锋")
    return _md_cell("，".join(parts))


def _end_turn_note(defn: Any) -> str:
    if getattr(defn, "name", ""):
        base = defn.name
    else:
        base = getattr(defn.kind, "value", defn.kind)
    parts = [f"回合结束:{base}"]
    if getattr(defn, "amount", 0):
        parts.append(f"数值{defn.amount}")
    if getattr(defn, "summon_atk", 0) or getattr(defn, "summon_health", 0):
        parts.append(f"召唤{defn.summon_atk}/{defn.summon_health}")
    if getattr(defn, "uses_self_atk", False):
        parts.append("用自身攻击力")
    if getattr(defn, "requires_dormant", False):
        parts.append("休眠")
    return _md_cell("，".join(parts))


def _import_all_modules() -> None:
    mods = (
        "hdt_python.spell_board",
        "hdt_python.spell_p0_direct",
        "hdt_python.spell_p0_aoe",
        "hdt_python.spell_p0_remove",
        "hdt_python.spell_p0_buff",
        "hdt_python.spell_p0_other",
        "hdt_python.spell_p0_minion",
        "hdt_python.spell_p0_dream",
        "hdt_python.spell_p0_concoction",
        "hdt_python.spell_p1_direct",
        "hdt_python.spell_p1_aoe",
        "hdt_python.spell_p1_buff",
        "hdt_python.spell_p1_minion",
        "hdt_python.spell_p1_other",
        "hdt_python.spell_p2_direct",
        "hdt_python.battlecry_p0",
        "hdt_python.rush_p0",
        "hdt_python.weapon_p0",
        "hdt_python.combo_p0",
        "hdt_python.hero_power_p0",
        "hdt_python.location_p0",
        "hdt_python.end_turn_hand_board",
        "hdt_python.damaged_spell_power",
        "hdt_python.eudora_loot",
    )
    for mod in mods:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            pass
    import hdt_python.spell_board  # noqa: F401
    from hdt_python.arena_season_bulk import register_arena_season_gap

    register_arena_season_gap()


def _board_rows(
    module: str,
    mapping: dict,
    en: dict[str, dict],
    zh: dict[str, dict],
    *,
    get_defn: Callable[[str, Any], Any],
    note_fn: Callable[[Any], str],
    random_fn: Optional[Callable[[Any], bool]] = None,
) -> list[dict]:
    rows: list[dict] = []
    for cid in sorted(mapping.keys()):
        entry = mapping[cid]
        defn = get_defn(cid, entry)
        ce, cz = _lookup_card(cid, en, zh)
        cost = getattr(defn, "base_cost", None)
        if cost is None:
            cost = ce.get("cost", cz.get("cost", "-"))
        name_zh = (
            cz.get("name")
            or getattr(defn, "name", None)
            or ce.get("name")
            or cid
        )
        name_en = ce.get("name") or cid
        ctype = ce.get("type") or cz.get("type") or "-"
        rnd = random_fn(defn) if random_fn else getattr(defn, "uses_random", False)
        rows.append({
            "module": module,
            "card_id": cid,
            "name_zh": _md_cell(str(name_zh)),
            "name_en": _md_cell(str(name_en)),
            "cost": cost if cost is not None else "-",
            "stats": _stat_line(ce) if ce else _stat_line(cz),
            "type": _md_cell(str(ctype)),
            "random": "是" if rnd else "否",
            "sim_note": note_fn(defn),
            "text_zh": _md_cell(cz.get("text") or ""),
            "text_en": _md_cell(ce.get("text") or ""),
        })
    return rows


def collect_rows() -> list[dict]:
    _import_all_modules()
    en = _load_json_cards(CARDS_EN)
    zh = _load_json_cards(CARDS_ZH)

    from hdt_python.spell_board import BOARD_CLEAR_SPELLS
    from hdt_python.battlecry_board import BOARD_BATTLECRY
    from hdt_python.rush_board import BOARD_RUSH
    from hdt_python.weapon_board import BOARD_WEAPON
    from hdt_python.combo_board import BOARD_COMBO
    from hdt_python.hero_power_board import BOARD_HERO_POWER
    from hdt_python.location_board import BOARD_LOCATION
    from hdt_python.end_turn_hand_board import BOARD_END_TURN_HAND
    from hdt_python.damaged_spell_power import BOARD_DAMAGED_SPELL_POWER
    from hdt_python.end_turn_board import END_TURN_BY_CARD
    from hdt_python.deathrattle import DEATHRATTLE_BY_CARD
    from hdt_python.lethal_checker import SPELL_DAMAGE_DB, CHARGE_MINIONS_DB

    rows: list[dict] = []

    board_maps = [
        ("spell", BOARD_CLEAR_SPELLS, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("battlecry", BOARD_BATTLECRY, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("rush", BOARD_RUSH, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("weapon", BOARD_WEAPON, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("combo", BOARD_COMBO, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("hero_power", BOARD_HERO_POWER, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("location", BOARD_LOCATION, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("end_turn_hand", BOARD_END_TURN_HAND, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
        ("damaged_spell_power", BOARD_DAMAGED_SPELL_POWER, lambda _cid, d: d, _apply_note, lambda d: d.uses_random),
    ]
    for module, mapping, get_defn, note_fn, random_fn in board_maps:
        rows.extend(_board_rows(module, mapping, en, zh, get_defn=get_defn, note_fn=note_fn, random_fn=random_fn))

    rows.extend(_board_rows(
        "end_turn", END_TURN_BY_CARD, en, zh,
        get_defn=lambda _cid, d: d,
        note_fn=_end_turn_note,
        random_fn=lambda d: d.uses_random,
    ))
    rows.extend(_board_rows(
        "deathrattle", DEATHRATTLE_BY_CARD, en, zh,
        get_defn=lambda _cid, d: d,
        note_fn=_deathrattle_note,
        random_fn=lambda _d: False,
    ))

    spell_board_ids = set(BOARD_CLEAR_SPELLS.keys())
    for cid, (cost, dmg, face) in sorted(SPELL_DAMAGE_DB.items()):
        if cid in spell_board_ids:
            continue
        ce, cz = _lookup_card(cid, en, zh)
        rows.append({
            "module": "spell_fast",
            "card_id": cid,
            "name_zh": _md_cell(cz.get("name") or ce.get("name") or cid),
            "name_en": _md_cell(ce.get("name") or cid),
            "cost": cost,
            "stats": "-",
            "type": _md_cell(str(ce.get("type") or "SPELL")),
            "random": "否",
            "sim_note": _md_cell(f"快速估算直伤{dmg}，可打脸={'是' if face else '否'}"),
            "text_zh": _md_cell(cz.get("text") or ""),
            "text_en": _md_cell(ce.get("text") or ""),
        })

    for cid, (cost, dmg) in sorted(CHARGE_MINIONS_DB.items()):
        ce, cz = _lookup_card(cid, en, zh)
        rows.append({
            "module": "charge_fast",
            "card_id": cid,
            "name_zh": _md_cell(cz.get("name") or ce.get("name") or cid),
            "name_en": _md_cell(ce.get("name") or cid),
            "cost": cost,
            "stats": _stat_line(ce) if ce else _stat_line(cz),
            "type": _md_cell(str(ce.get("type") or "MINION")),
            "random": "否",
            "sim_note": _md_cell(f"快速估算冲锋打脸{dmg}"),
            "text_zh": _md_cell(cz.get("text") or ""),
            "text_en": _md_cell(ce.get("text") or ""),
        })

    def sort_key(r: dict) -> tuple:
        mod_order = SECTION_ORDER.index(r["module"]) if r["module"] in SECTION_ORDER else 99
        cost = r["cost"]
        cost_key = cost if isinstance(cost, (int, float)) else 999
        return (mod_order, cost_key, r["name_zh"], r["card_id"])

    rows.sort(key=sort_key)
    return rows


def render_markdown(rows: list[dict]) -> str:
    from datetime import datetime, timezone

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["module"]] = counts.get(r["module"], 0) + 1

    lines = [
        "# 致死模拟已支持卡牌总表",
        "",
        "> 自动生成：运行 `python scripts/generate_supported_cards_table.py` 可更新本文件。",
        "",
        f"> 生成时间（UTC）：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        "| 模块 | 数量 |",
        "|------|------|",
    ]
    total = 0
    for key in SECTION_ORDER:
        n = counts.get(key, 0)
        if n:
            lines.append(f"| {MODULE_LABELS[key]} | {n} |")
            total += n
    lines.append(f"| **合计** | **{total}** |")
    lines.append("")
    lines.append("## 字段说明")
    lines.append("")
    lines.append("| 列 | 含义 |")
    lines.append("|----|------|")
    lines.append("| card_id | 炉石卡牌 ID（含 CORE_ 变体） |")
    lines.append("| 中文名 / 英文名 | 来自 `json/cards_zhCN.json` / `json/cards.json` |")
    lines.append("| 费用 | 注册表 `base_cost` 优先，否则 JSON `cost` |")
    lines.append("| 攻/血 | 随从攻击/生命；武器为攻击/耐久 |")
    lines.append("| 类型 | MINION / SPELL / WEAPON / HERO_POWER 等 |")
    lines.append("| 随机 | 模拟是否含随机结算 |")
    lines.append("| 模拟说明 | 代码内效果摘要（docstring 或注册名） |")
    lines.append("| 中文描述 / 英文描述 | 官方卡牌文本 |")
    lines.append("")

    current_module: Optional[str] = None
    for r in rows:
        if r["module"] != current_module:
            current_module = r["module"]
            label = MODULE_LABELS.get(current_module, current_module)
            lines.extend([
                f"## {label}",
                "",
                "| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |",
                "|---------|--------|--------|------|------|------|------|----------|----------|----------|",
            ])
        lines.append(
            f"| {r['card_id']} | {r['name_zh']} | {r['name_en']} | {r['cost']} | {r['stats']} | "
            f"{r['type']} | {r['random']} | {r['sim_note']} | {r['text_zh']} | {r['text_en']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = collect_rows()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_markdown(rows), encoding="utf-8")
    print(f"Wrote {OUT_MD} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
