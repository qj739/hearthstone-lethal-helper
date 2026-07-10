#!/usr/bin/env python3
"""生成清场指向性 / 指向性可打脸法术对照表。"""
from __future__ import annotations

import importlib
import inspect
import json
import re
import sys
from copy import deepcopy
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
    SpellSimTier,
    SPELL_SIM_TIER_LABELS,
    clear_targeted_pointed_allows_no_taunt_minion,
    spell_sim_tier,
)

_MINION_SRC = (ROOT / "hdt_python" / "spell_p0_minion.py").read_text(encoding="utf-8")
_ALLOW_NO_TAUNT_IDS: set[str] = set()  # legacy; 现由 CLEAR_TARGETED_POINTED_SPELL_IDS 统一判定


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


def _sample_board(n: int = 5) -> list[dict]:
    return [
        {
            "health": 2,
            "shield": False,
            "lifesteal": False,
            "atk": 2,
            "poisonous": False,
            "spell_immune": False,
            "taunt": True,
            "zone_pos": i,
            "entity_id": 100 + i,
        }
        for i in range(1, n + 1)
    ]


def _card_text(defn, card_text: dict[str, str]) -> str:
    for cid in defn.card_ids:
        t = card_text.get(cid, "")
        if t:
            return t
    return ""


def _is_aoe_text(text: str) -> bool:
    markers = (
        "所有敌人", "所有敌方随从", "所有随从", "所有角色", "全场",
        "每个敌人", "每个随从", "随机对两个", "随机对三个", "随机消灭两个",
        "分配到所有", "洗入你的牌库",
    )
    return any(m in text for m in markers)


def _is_pointed_clear_text(text: str) -> bool:
    if not text or _is_aoe_text(text):
        return False
    markers = (
        "对一个随从", "对一个敌方随从", "对一个受伤的随从",
        "消灭一个随从", "消灭一个敌方随从", "消灭一个",
        "消灭攻击力最高的敌方随从",
        "选择一个随从", "随机消灭一个敌方随从", "随机消灭一个",
        "随机对一个敌方随从", "随机对一个敌人",
        "对非龙敌方随从", "移回其拥有者的手牌",
        "对一个随从造成", "对一个敌方随从造成",
    )
    return any(m in text for m in markers)


def _is_face_optional_text(text: str) -> bool:
    if not text or _is_aoe_text(text):
        return False
    if "使一个随从" in text and "造成" not in text:
        return False
    markers = (
        "造成$", "造成{0}", "点伤害", "直伤", "可选目标",
        "对一个角色", "对任意角色", "对生命值最低的敌人",
        "分配到生命值最低",
    )
    return any(m in text for m in markers)


def _is_clear_targeted(defn, card_text: dict[str, str]) -> bool:
    if spell_sim_tier(defn) != SpellSimTier.CLEAR_BOARD:
        return False
    text = _card_text(defn, card_text)
    if _is_pointed_clear_text(text):
        return True
    doc = (inspect.getdoc(defn.apply) or "")
    if _is_pointed_clear_text(doc):
        return True
    # 模拟：5 随从 2 血，恰好 1 个受伤且其余不变
    board = _sample_board(5)
    orig = {t["entity_id"]: t["health"] for t in board}
    board_t = deepcopy(board)
    try:
        defn.apply(board_t, [], mult=1, enemy_shield=False)
    except Exception:
        return False
    changed = 0
    for eid, hp in orig.items():
        cur = next((t for t in board_t if t.get("entity_id") == eid), None)
        cur_hp = max(cur.get("health", 0), 0) if cur else 0
        if cur_hp != hp:
            changed += 1
    removed = sum(1 for eid in orig if not any(t.get("entity_id") == eid for t in board_t))
    return (changed + removed) == 1


def _face_on_empty(defn) -> int:
    try:
        res = defn.apply([], [], mult=1, enemy_shield=False)
        return max(0, int(res.direct_face_damage or 0))
    except Exception:
        return 0


def _is_face_optional_targeted(defn, card_text: dict[str, str]) -> bool:
    if spell_sim_tier(defn) != SpellSimTier.DIRECT_FACE:
        return False
    if _face_on_empty(defn) <= 0:
        return False
    skip_random_multi = (
        "激寒急流", "拉格纳罗斯的余烬", "爆裂射击", "麦芽岩浆", "血染大海",
    )
    if defn.name in skip_random_multi:
        return False
    text = _card_text(defn, card_text)
    if _is_face_optional_text(text):
        return True
    doc = (inspect.getdoc(defn.apply) or "")
    return "可选目标" in doc or "直伤" in doc or "打脸" in doc


def main() -> None:
    card_text = _load_card_text()
    seen_clear: set[str] = set()
    seen_face: set[str] = set()
    clear_rows: list[tuple] = []
    face_rows: list[tuple] = []

    for _cid, defn in sorted(BOARD_CLEAR_SPELLS.items(), key=lambda x: (x[1].name, x[0])):
        if _is_clear_targeted(defn, card_text) and defn.name not in seen_clear:
            seen_clear.add(defn.name)
            cid = defn.card_ids[0]
            allow = "是" if clear_targeted_pointed_allows_no_taunt_minion(defn=defn) else "否"
            clear_rows.append((
                defn.name,
                cid,
                "是" if defn.uses_random else "否",
                allow,
                _effect(defn, card_text),
            ))

    for _cid, defn in sorted(BOARD_CLEAR_SPELLS.items(), key=lambda x: (x[1].name, x[0])):
        if _is_face_optional_targeted(defn, card_text) and defn.name not in seen_face:
            seen_face.add(defn.name)
            face_rows.append((
                defn.name,
                defn.card_ids[0],
                "是" if defn.uses_random else "否",
                _effect(defn, card_text),
            ))

    out = ROOT / "docs" / "CLEAR_TARGETED_SPELL_TABLE.md"
    lines = [
        "# 清场指向性 / 指向性可打脸法术对照表",
        "",
        "供检查斩杀模拟中的**单体目标**法术策略。",
        "",
        "## 模拟规则（当前实现）",
        "",
        "| 类型 | 有嘲讽 | 无嘲讽 |",
        "|------|--------|--------|",
        "| **清场指向性** | 只点嘲讽随从 | 遍历敌方随从择优（表一全部启用） |",
        "| **指向性可打脸** | 打脸 vs 点嘲讽，取场攻更高 | **只打脸**，不考虑点非嘲讽随从 |",
        "",
        "## 表一：清场指向性法术",
        "",
        f"共 **{len(clear_rows)}** 张（`SpellSimTier.清场` 且单点/少量随从目标，按中文名去重）。",
        "",
        "| 名称 | card_id | 随机 | 无嘲讽点随从 | 法术效果 |",
        "|------|---------|------|--------------|----------|",
    ]
    for name, cid, rnd, allow, effect in clear_rows:
        lines.append(f"| {name} | {cid} | {rnd} | {allow} | {effect} |")

    lines.extend([
        "",
        "## 表二：指向性可打脸法术",
        "",
        f"共 **{len(face_rows)}** 张（`SpellSimTier.直伤` 且空场可打脸，按中文名去重）。",
        "",
        "**无嘲讽时仅模拟打脸**，不参与「点非嘲讽随从」遍历。",
        "",
        "| 名称 | card_id | 随机 | 法术效果 |",
        "|------|---------|------|----------|",
    ])
    for name, cid, rnd, effect in face_rows:
        lines.append(f"| {name} | {cid} | {rnd} | {effect} |")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  清场指向性: {len(clear_rows)}")
    print(f"  指向性可打脸: {len(face_rows)}")


if __name__ == "__main__":
    main()
