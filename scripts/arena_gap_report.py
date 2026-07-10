#!/usr/bin/env python3
"""拉取 HSReplay 当季竞技场池，对比已注册卡牌，输出待接入清单。"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(__file__).resolve().parent / ".cache"
CARDS_JSON = ROOT / "json" / "cards.json"
CARDS_ZH = ROOT / "json" / "cards_zhCN.json"
DOCS = ROOT / "docs"
OUT_MD = DOCS / "ARENA_GAP_REPORT.md"
API_URL = (
    "https://hsreplay.net/api/v1/arena/card_stats/free/"
    "?ArenaTimestampRangeFilter=LAST_4_DAYS"
)

# 与斩杀/场攻相关的法术文本特征（排除纯发现/过牌）
SPELL_DAMAGE_RE = re.compile(
    r"造成|伤害|Deal \$|deal \$|对所有|each (?:enemy|character|minion)|"
    r"Destroy|消灭|Silence|沉默|Transform|变形|Freeze|冻结",
    re.I,
)
SPELL_SKIP_RE = re.compile(
    r"发现|Discover|抽一张|draw a card|置入.*手牌|add .* to your hand|"
    r"复制|Copy|随机.*牌|random.*card",
    re.I,
)
BATTLECRY_SKIP_RE = re.compile(
    r"发现|Discover|抽一张|draw|置入.*手牌|add .* to your hand|"
    r"复制.*手牌|random.*card|随机.*牌",
    re.I,
)
BATTLECRY_DAMAGE_RE = re.compile(
    r"造成|伤害|Deal \$|destroy|消灭|silence|沉默|transform|变形|"
    r"freeze|冻结|对所有|all (?:other )?(?:enemies|minions|characters)",
    re.I,
)
END_TURN_RE = re.compile(r"在你的回合结束时|At the end of your turn", re.I)
END_TURN_DAMAGE_RE = re.compile(
    r"造成|伤害|Deal \$|attack|攻击|summon.*attack|召唤.*攻击",
    re.I,
)
DEATHRATTLE_DAMAGE_RE = re.compile(
    r"造成|伤害|Deal \$|summon.*taunt|召唤.*嘲讽|summon.*[0-9]/[0-9]",
    re.I,
)

P3_SPELL_IDS = frozenset({
    "BAR_914", "BAR_915", "BAR_916", "BT_300", "CS2_028", "CS2_093",
    "EX1_259", "GDB_301", "ICC_041", "LOOT_417", "RLK_216", "SW_040",
    "TTN_853", "VAC_414", "YOG_502", "CATA_581", "CATA_526",
})


def fetch_arena_stats() -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / "arena_card_stats.json"
    if not cache_path.is_file() or cache_path.stat().st_size < 1000:
        req = urllib.request.Request(
            API_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json",
                "Referer": "https://hsreplay.net/arena/cards/",
            },
        )
        with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as resp:
            cache_path.write_bytes(resp.read())
    return json.loads(cache_path.read_text(encoding="utf-8"))


def load_cards() -> tuple[dict[str, dict], dict[str, str]]:
    cards = {c["id"]: c for c in json.loads(CARDS_JSON.read_text(encoding="utf-8")) if c.get("id")}
    zh = {}
    if CARDS_ZH.is_file():
        for c in json.loads(CARDS_ZH.read_text(encoding="utf-8")):
            if c.get("id") and c.get("name"):
                zh[c["id"]] = c["name"]
    return cards, zh


def normalize_id(cid: str) -> str:
    return cid[5:] if cid.startswith("CORE_") else cid


def expand_ids(cid: str) -> set[str]:
    base = normalize_id(cid)
    return {cid, base, f"CORE_{base}"}


def collect_registered() -> dict[str, set[str]]:
    sys.path.insert(0, str(ROOT))
    import hdt_python.spell_board  # noqa: F401 — trigger spell_p0/p1/p2 registration
    from hdt_python.arena_season_bulk import register_arena_season_gap

    register_arena_season_gap()
    from hdt_python.spell_board import BOARD_CLEAR_SPELLS
    from hdt_python.battlecry_board import BOARD_BATTLECRY
    from hdt_python.rush_board import BOARD_RUSH
    from hdt_python.weapon_board import BOARD_WEAPON
    from hdt_python.combo_board import BOARD_COMBO
    from hdt_python.location_board import BOARD_LOCATION
    from hdt_python.hero_power_board import BOARD_HERO_POWER
    from hdt_python.end_turn_board import END_TURN_BY_CARD
    from hdt_python.deathrattle import DEATHRATTLE_BY_CARD
    from hdt_python.end_turn_hand_board import BOARD_END_TURN_HAND
    from hdt_python.lethal_checker import SPELL_DAMAGE_DB

    spell_ids: set[str] = set(BOARD_CLEAR_SPELLS.keys())
    for defn in BOARD_CLEAR_SPELLS.values():
        spell_ids.update(defn.card_ids)
    spell_ids |= set(SPELL_DAMAGE_DB.keys())

    return {
        "spell": spell_ids,
        "battlecry": set(BOARD_BATTLECRY.keys()),
        "rush": set(BOARD_RUSH.keys()),
        "weapon": set(BOARD_WEAPON.keys()),
        "combo": set(BOARD_COMBO.keys()),
        "location": set(BOARD_LOCATION.keys()),
        "hero_power": set(BOARD_HERO_POWER.keys()),
        "end_turn": set(END_TURN_BY_CARD.keys()),
        "deathrattle": set(DEATHRATTLE_BY_CARD.keys()),
        "end_turn_hand": set(BOARD_END_TURN_HAND.keys()),
    }


def is_registered(cid: str, reg: set[str]) -> bool:
    return bool(expand_ids(cid) & reg)


def arena_rows(payload: dict) -> list[dict]:
    data = payload.get("data") or {}
    rows = data.get("ALL") or []
    by_id: dict[str, dict] = {}
    for row in rows:
        cid = row.get("card_id")
        if cid:
            by_id[cid] = row
    return list(by_id.values())


def card_meta(cards: dict[str, dict], zh: dict[str, str], cid: str) -> dict:
    c = cards.get(cid) or cards.get(normalize_id(cid)) or cards.get(f"CORE_{normalize_id(cid)}") or {}
    mech = set(c.get("mechanics") or [])
    refs = set(c.get("referencedTags") or [])
    text = (c.get("text") or "") + " " + (zh.get(cid) or zh.get(normalize_id(cid)) or "")
    return {
        "id": cid,
        "name_zh": zh.get(cid) or zh.get(normalize_id(cid)) or c.get("name") or cid,
        "name_en": c.get("name") or cid,
        "cost": c.get("cost"),
        "type": c.get("type"),
        "mechanics": mech | refs,
        "text": text.strip(),
        "attack": c.get("attack"),
        "health": c.get("health"),
    }


def priority(games: int) -> str:
    if games >= 500:
        return "P0"
    if games >= 100:
        return "P1"
    if games >= 1:
        return "P2"
    return "P3"


def classify_spell(meta: dict) -> bool:
    if meta["type"] != "SPELL":
        return False
    text = meta["text"]
    if not text:
        return False
    if not SPELL_DAMAGE_RE.search(text):
        return False
    if SPELL_SKIP_RE.search(text) and not re.search(r"造成|Deal \$|damage", text, re.I):
        return False
    if meta["id"] in P3_SPELL_IDS:
        return False
    return True


def classify_battlecry(meta: dict) -> bool:
    if meta["type"] != "MINION":
        return False
    if "BATTLECRY" not in meta["mechanics"]:
        return False
    text = meta["text"]
    if BATTLECRY_SKIP_RE.search(text) and not BATTLECRY_DAMAGE_RE.search(text):
        return False
    return bool(BATTLECRY_DAMAGE_RE.search(text))


def classify_rush(meta: dict) -> bool:
    return meta["type"] == "MINION" and "RUSH" in meta["mechanics"]


def classify_weapon(meta: dict) -> bool:
    return meta["type"] == "WEAPON"


def classify_combo(meta: dict) -> bool:
    return meta["type"] == "MINION" and "COMBO" in meta["mechanics"]


def classify_deathrattle(meta: dict) -> bool:
    if meta["type"] != "MINION" or "DEATHRATTLE" not in meta["mechanics"]:
        return False
    return bool(DEATHRATTLE_DAMAGE_RE.search(meta["text"]))


def classify_end_turn(meta: dict) -> bool:
    if meta["type"] != "MINION":
        return False
    text = meta["text"]
    return bool(END_TURN_RE.search(text) and END_TURN_DAMAGE_RE.search(text))


def fmt_row(meta: dict, games: int, pri: str, note: str = "") -> str:
    cost = meta.get("cost")
    cost_s = str(cost) if cost is not None else "?"
    body = meta["text"].replace("\n", " ")[:80]
    extra = f" | {note}" if note else ""
    return (
        f"| `{meta['id']}` | {meta['name_zh']} | {cost_s} | {games} | {pri} | "
        f"{body}{extra} |"
    )


def section_table(title: str, rows: list[tuple[dict, int, str, str]]) -> list[str]:
    lines = [f"## {title}", "", f"**待接入 {len(rows)} 张**", ""]
    if not rows:
        lines.append("_无_")
        lines.append("")
        return lines
    lines.extend([
        "| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |",
        "|---------|--------|----|-------|--------|----------|",
    ])
    for meta, games, pri, note in sorted(rows, key=lambda x: (-x[1], x[0]["id"])):
        lines.append(fmt_row(meta, games, pri, note))
    lines.append("")
    return lines


def main() -> None:
    payload = fetch_arena_stats()
    cards, zh = load_cards()
    registered = collect_registered()
    rows = arena_rows(payload)
    pool_size = len(rows)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    missing: dict[str, list[tuple[dict, int, str, str]]] = defaultdict(list)
    stats = defaultdict(lambda: {"pool": 0, "registered": 0, "missing": 0})

    for row in rows:
        cid = row["card_id"]
        games = int(row.get("num_games") or 0)
        meta = card_meta(cards, zh, cid)
        pri = priority(games)

        checks = [
            ("法术(斩杀相关)", classify_spell, "spell"),
            ("战吼(伤害/解场)", classify_battlecry, "battlecry"),
            ("突袭", classify_rush, "rush"),
            ("武器", classify_weapon, "weapon"),
            ("连击", classify_combo, "combo"),
            ("亡语(伤害/招嘲)", classify_deathrattle, "deathrattle"),
            ("回合结束(打脸)", classify_end_turn, "end_turn"),
        ]
        for _label, fn, key in checks:
            if not fn(meta):
                continue
            stats[key]["pool"] += 1
            if is_registered(cid, registered[key]):
                stats[key]["registered"] += 1
            else:
                stats[key]["missing"] += 1
                note = ""
                if key == "rush" and is_registered(cid, registered["battlecry"]):
                    note = "可能走战吼/穿插"
                if key == "battlecry" and is_registered(cid, registered["rush"]):
                    note = "已注册突袭"
                missing[key].append((meta, games, pri, note))

    # 已知代码内待做（旧清单）
    known_todo = [
        ("spell", "RLK_534", "灵魂弹幕 P2"),
        ("end_turn", "YOP_034", "窜逃的黑翼龙"),
        ("end_turn", "CORE_YOP_034", "窜逃的黑翼龙"),
        ("end_turn", "BAR_063", "沃坎诺斯"),
        ("end_turn", "BAR_064", "亮铜之翼"),
    ]

    md: list[str] = [
        "# 竞技场新赛季待接入卡牌清单",
        "",
        f"> 生成时间: {generated}  ",
        f"> 数据来源: [HSReplay Arena]({API_URL})  ",
        "> 模式: `BGT_UNDERGROUND_ARENA` + `LAST_4_DAYS`  ",
        f"> **当季池规模: {pool_size} 张**（上次文档约 1081–1243 张，以本次 API 为准）  ",
        "> 已注册集: `BOARD_CLEAR_SPELLS` / `SPELL_DAMAGE_DB` / `BOARD_BATTLECRY` / `BOARD_RUSH` / `BOARD_WEAPON` / 等  ",
        "",
        "## 总览",
        "",
        "| 模块 | 池内相关 | 已接入 | 待接入 |",
        "|------|----------|--------|--------|",
    ]
    labels = {
        "spell": "法术",
        "battlecry": "战吼随从",
        "rush": "突袭随从",
        "weapon": "武器",
        "combo": "连击随从",
        "deathrattle": "亡语随从",
        "end_turn": "回合结束随从",
    }
    total_missing = 0
    for key in ("spell", "battlecry", "rush", "weapon", "combo", "deathrattle", "end_turn"):
        s = stats[key]
        total_missing += s["missing"]
        md.append(
            f"| {labels[key]} | {s['pool']} | {s['registered']} | **{s['missing']}** |"
        )
    md.append(f"| **合计** | — | — | **{total_missing}** |")
    md.append("")

    md.extend([
        "## 优先级说明",
        "",
        "| 级别 | HSReplay games | 建议 |",
        "|------|----------------|------|",
        "| **P0** | ≥ 500 | 优先实现 |",
        "| **P1** | 100–499 | 第二批 |",
        "| **P2** | 1–99 | 可暂缓 |",
        "",
        "## 代码内已知待做（旧清单）",
        "",
        "| card_id | 说明 |",
        "|---------|------|",
    ])
    for _k, cid, desc in known_todo:
        md.append(f"| `{cid}` | {desc} |")
    md.append("")

    spell_by_pri: dict[str, list] = defaultdict(list)
    for item in missing["spell"]:
        spell_by_pri[item[2]].append(item)
    md.append("## 法术待接入（按优先级）")
    md.append("")
    for pri in ("P0", "P1", "P2"):
        chunk = spell_by_pri.get(pri, [])
        md.extend(section_table(f"法术 {pri}（{len(chunk)} 张）", chunk))

    md.extend(section_table("战吼待接入", missing["battlecry"]))
    md.extend(section_table("突袭待接入", missing["rush"]))
    md.extend(section_table("武器待接入", missing["weapon"]))
    md.extend(section_table("连击待接入", missing["combo"]))
    md.extend(section_table("亡语待接入", missing["deathrattle"]))
    md.extend(section_table("回合结束待接入", missing["end_turn"]))

    # 新赛季高热度 Top 20 待做法术
    top_spells = sorted(missing["spell"], key=lambda x: -x[1])[:20]
    if top_spells:
        md.extend(section_table("法术 Top20 热度（建议先做）", top_spells))

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    print(f"Pool={pool_size} total_missing={total_missing}")
    for key in labels:
        print(f"  {labels[key]}: missing={stats[key]['missing']} pool={stats[key]['pool']}")


if __name__ == "__main__":
    main()
